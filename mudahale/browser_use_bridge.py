"""
Katman 2 — Browser-Use Köprüsü (Faz 3)
browser-use Agent'i browserless:3001 CDP'ye bağlar, tam otonom tarayıcı kontrolü sağlar.
Eski web_tools'un yerini alır — tıklama, form doldurma, gezinme dahil.

browser-use kendi LLM'sini kullanır (LiteLLM proxy üzerinden),
BrowserSession ise browserless:3001'e CDP/WebSocket ile bağlanır.

Arayüz: SmolAgentBridge ile aynı — calistir(gorev) → str
"""
import asyncio
import sys
import os
from typing import Optional

from config.config import config

# browser-use'un kurulu olduğu dizini sys.path'e ekle
_BROWSER_USE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "browser-use-main", "browser-use-main"
)
if _BROWSER_USE_ROOT not in sys.path:
    sys.path.insert(0, _BROWSER_USE_ROOT)


def _cdp_url() -> str:
    """Browserless CDP WebSocket URL'ini olustur.
    Once dogrudan /json/version endpoint'inden okumayi dener,
    basarisizsa URL donusumu yapar.
    """
    import requests
    http_url = config.BROWSERLESS_URL
    try:
        r = requests.get(f"{http_url}/json/version", timeout=3)
        if r.status_code == 200:
            data = r.json()
            ws = data.get("webSocketDebuggerUrl", "")
            if ws:
                print(f"[BrowserUse] CDP URL from browserless: {ws}")
                return ws
    except Exception:
        pass
    # Fallback: dogrudan ws donusumu
    ws_url = http_url.replace("http://", "ws://").replace("https://", "wss://")
    # Browserless CDP endpoint
    if "/json/version" not in ws_url:
        ws_url = ws_url.rstrip("/")
    print(f"[BrowserUse] CDP URL fallback: {ws_url}")
    return ws_url


class BrowserUseBridge:
    """
    browser-use Agent sarmalayıcı.

    Her görev için müstakil bir BrowserSession + Agent oluşturur.
    Agent LLM'siyle (LiteLLM proxy) web sayfasını gezer, DOM'u okur,
    butonlara tıklar, form doldurur, içerik çeker.

    CDP bağlantısı browserless:3001 üzerinden yapılır.
    """

    def __init__(self):
        self._ready = False
        self._llm = None
        self._init_agent()

    def _init_agent(self):
        """Browser-use LLM istemcisini yapılandır (LiteLLM proxy)."""
        try:
            from browser_use.llm.openai.chat import ChatOpenAI

            self._llm = ChatOpenAI(
                model=config.MAHKEME_MODEL,
                base_url=config.LITELLM_URL.rstrip("/") if config.LITELLM_URL.endswith("/v1") else f"{config.LITELLM_URL}/v1",
                api_key=config.LITELLM_KEY,
                frequency_penalty=None,          # LiteLLM/Anthropic uyumsuzluğu
                temperature=0.2,
                max_retries=3,
                dont_force_structured_output=True,  # tool_choice → thinking mode çakışmasını önler
                add_schema_to_system_prompt=True,   # şemayı tool_choice yerine system prompt'a koy
            )
            self._ready = True
            print(f"[BrowserUse] Bridge ready (LLM: {config.MAHKEME_MODEL} @ "
                  f"{config.LITELLM_URL}, CDP: {_cdp_url()})")
        except Exception as e:
            print(f"[BrowserUse] Init error: {e}")
            import traceback
            traceback.print_exc()
            self._ready = False

    def hazir_mi(self) -> bool:
        return self._ready

    def calistir(self, gorev: str, max_steps: int = 15) -> Optional[str]:
        """
        Bir web görevini browser-use Agent ile çalıştır.

        Agent, browserless:3001'deki headless Chrome'u CDP ile kontrol eder,
        LLM olarak LiteLLM proxy üzerinden modeli kullanır.

        Args:
            gorev: Doğal dilde görev tanımı (örn: "Go to example.com and get the title")
            max_steps: Maksimum tarayıcı adımı (varsayılan 15)

        Returns:
            Görev sonucu metni, veya None (hata)
        """
        if not self._ready:
            print("[BrowserUse] Agent hazır değil.")
            return None

        try:
            print(f"[BrowserUse] Executing: {gorev[:120]}...")
            sonuc = asyncio.run(self._async_calistir(gorev, max_steps))
            return sonuc
        except RuntimeError as e:
            # asyncio.run() hataları (event loop zaten çalışıyorsa)
            print(f"[BrowserUse] Async execution error: {e}")
            # Yeni thread'de dene
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self._async_calistir(gorev, max_steps))
                )
                return future.result(timeout=300)
        except Exception as e:
            print(f"[BrowserUse] Execution error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _async_calistir(self, gorev: str, max_steps: int = 15) -> Optional[str]:
        """Asenkron browser-use Agent çalıştırıcısı."""
        from browser_use import Agent, BrowserSession

        cdp = _cdp_url()
        browser = BrowserSession(
            cdp_url=cdp,
            headless=True,
            disable_security=True,
        )

        try:
            # Browserless'a CDP ile bağlan
            print(f"[BrowserUse] CDP connection: {cdp}")
            await browser.start()
            print(f"[BrowserUse] Browserless connection established.")

            # Agent'ı oluştur
            agent = Agent(
                task=gorev,
                llm=self._llm,
                browser_session=browser,
                use_vision=False,          # Headless browserless'ta vision gerekmez
                use_thinking=False,        # LiteLLM proxy ile uyumluluk
                directly_open_url=True,    # URL varsa doğrudan aç
                max_failures=3,
                flash_mode=True,           # Daha hızlı, planlama olmadan
                enable_planning=False,     # Basit görevler için planlamasız
            )

            print(f"[BrowserUse] Agent running (max {max_steps} steps)...")
            history = await agent.run(max_steps=max_steps)

            # Sonucu çıkar
            if history.is_done():
                result = history.final_result()
                steps = history.number_of_steps()
                try:
                    duration = history.total_duration_seconds()
                    print(f"[BrowserUse] OK Completed ({steps} steps, {duration:.1f}s)")
                except Exception:
                    print(f"[BrowserUse] OK Completed ({steps} steps)")
                return str(result) if result else "Task completed (no result text)."
            else:
                error_list = history.errors()
                error_msgs = [str(e) for e in (error_list or []) if e]
                print(f"[BrowserUse] WARN Agent incomplete. Errors: {error_msgs[:3]}")
                # Son adımın sonucunu döndürmeyi dene
                if history.history:
                    last = history.history[-1]
                    if hasattr(last, 'result') and last.result:
                        for r in reversed(last.result):
                            if hasattr(r, 'extracted_content') and r.extracted_content:
                                return str(r.extracted_content)
                return f"Görev tamamlanamadı. Hatalar: {error_msgs[:3]}"

        except Exception as e:
            print(f"[BrowserUse] Agent hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            try:
                await browser.kill()
            except Exception:
                pass


# Global instance
_browser_use_instance: Optional[BrowserUseBridge] = None


def get_browser_use() -> BrowserUseBridge:
    """
    Global browser-use köprüsünü döndür.
    orchestrator.py tarafından import edilir.
    """
    global _browser_use_instance
    if _browser_use_instance is None:
        _browser_use_instance = BrowserUseBridge()
    return _browser_use_instance
