"""
Katman 2 — Browser Use Köprüsü
browserless:3001 üzerinden otonom tarayıcı kontrolü.
"""
import os
from typing import Optional
from config.config import config


class BrowserBridge:
    """
    Browser Use ile browserless entegrasyonu.
    Browserless headless Chrome sağlar, Browser Use AI ile kontrol eder.
    """

    def __init__(self):
        self.browserless_url = config.BROWSERLESS_URL
        self._connected = False

    def health(self) -> bool:
        """Browserless sağlık kontrolü (JSON version endpoint)."""
        try:
            import requests
            resp = requests.get(f"{self.browserless_url}/json/version", timeout=5)
            self._connected = resp.status_code == 200
            if self._connected:
                data = resp.json()
                print(f"[Browser] {data.get('Browser', '?')} hazır")
            return self._connected
        except Exception:
            self._connected = False
            return False

    def chrome_ws_endpoint(self) -> str:
        """Browserless WebSocket endpoint (CDP bağlantısı için)."""
        return f"ws://localhost:3001"

    def tarayici_ac_ve_calistir(self, gorev: str, url: str = None) -> Optional[str]:
        """
        Browser Use ile bir web görevini otonom çalıştır.

        Args:
            gorev: Doğal dilde görev (örn: "formu doldur ve submit et")
            url: Başlangıç URL'si

        Returns:
            Görev sonucu metni
        """
        if not self.health():
            return "HATA: Browserless'a bağlanılamadı"

        try:
            from browser_use import Agent
            from langchain_openai import ChatOpenAI

            # LiteLLM proxy üzerinden LLM bağlantısı
            llm = ChatOpenAI(
                model=config.MAHKEME_MODEL,
                base_url=f"{config.LITELLM_URL}/v1",
                api_key=config.LITELLM_KEY,
            )

            # Browser Use agent'ı browserless'a bağla
            agent = Agent(
                task=gorev,
                llm=llm,
                # browserless CDP endpoint
                browser=config.BROWSERLESS_URL,
            )

            result = agent.run()
            return str(result)

        except Exception as e:
            return f"HATA: {e}"

    def ekran_goruntusu_al(self, selector: str = "body") -> Optional[bytes]:
        """Sayfanın ekran görüntüsünü al."""
        try:
            import requests
            resp = requests.post(
                f"{self.browserless_url}/screenshot",
                json={"url": "about:blank", "options": {"fullPage": False}},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            print(f"[Browser] Ekran görüntüsü hatası: {e}")
        return None

    def pdf_yap(self, url: str) -> Optional[bytes]:
        """Bir URL'yi PDF olarak kaydet."""
        try:
            import requests
            resp = requests.post(
                f"{self.browserless_url}/pdf",
                json={"url": url, "options": {"format": "A4"}},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            print(f"[Browser] PDF hatası: {e}")
        return None


# Global instance
_browser: Optional[BrowserBridge] = None

def get_browser() -> BrowserBridge:
    global _browser
    if _browser is None:
        _browser = BrowserBridge()
    return _browser
