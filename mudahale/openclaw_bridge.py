"""
OpenClaw Bridge — 7/24 Mesajlaşma İstihbaratı (Raw HTTP API).

Platformlar: Telegram, WhatsApp (Twilio), X (Twitter)
Şu an aktif: Telegram bot (raw API, sıfır async sorunu)
"""
import sys, os, time, json, requests, threading
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TELEGRAM_API = "https://api.telegram.org/bot"


class OpenClawBridge:
    """Çoklu platform mesajlaşma köprüsü."""

    def __init__(self):
        self._ready = False
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._offset = 0
        self._running = False
        self._thread = None
        if self._token:
            self._ready = True

    def hazir_mi(self) -> bool:
        return self._ready

    @property
    def token_set(self) -> bool:
        return bool(self._token)

    def _api(self, method: str, data: dict = None) -> dict:
        try:
            url = f"{TELEGRAM_API}{self._token}/{method}"
            r = requests.post(url, json=data, timeout=15) if data else requests.get(url, timeout=15)
            return r.json()
        except:
            return {"ok": False}

    def _send(self, chat_id: int, text: str):
        self._api("sendMessage", {"chat_id": chat_id, "text": text[:4000]})

    def _islem(self, msg: str) -> str:
        try:
            from karar.aspasia import aspasia_kesici
            yerel = aspasia_kesici(msg)
            if yerel: return yerel
        except: pass
        try:
            from altyapi.litellm_bridge import litellm
            from karar.aspasia import aspasia_system_prompt
            r = litellm.chat([
                {"role": "system", "content": aspasia_system_prompt()},
                {"role": "user", "content": msg}
            ], max_tokens=400)
            if r and r.get("content"): return r["content"][:1500]
        except: pass
        return "Düşüncelerimizi sıraya dizelim Mösyö. Bir an."

    def telegram_baslat(self, token: str = None):
        """Telegram bot'u arka planda başlat (polling, raw HTTP)."""
        if token: self._token = token
        if not self._token:
            print("[OpenClaw] ❌ Token yok.")
            return False

        self._ready = True
        self._running = True
        # İlk offset'i al
        updates = self._api("getUpdates", {"limit": 1, "offset": -1})
        if updates.get("result"):
            self._offset = updates["result"][-1]["update_id"] + 1

        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[OpenClaw] 🟢 Telegram bot dinlemede (raw HTTP)...", flush=True)
        return True

    def _poll_loop(self):
        while self._running:
            try:
                updates = self._api("getUpdates", {"offset": self._offset, "timeout": 10})
                if updates.get("ok") and updates.get("result"):
                    for upd in updates["result"]:
                        self._offset = upd["update_id"] + 1
                        msg = upd.get("message", {})
                        text = msg.get("text", "")
                        chat_id = msg.get("chat", {}).get("id")
                        if text and chat_id:
                            print(f"[OpenClaw] 📩 {text[:80]}", flush=True)
                            yanit = self._islem(text)
                            self._send(chat_id, yanit)
            except Exception as e:
                print(f"[OpenClaw] Poll hatası: {e}", flush=True)
                time.sleep(5)

    def durdur(self):
        self._running = False
        print("[OpenClaw] Durduruldu.")


_openclaw: Optional[OpenClawBridge] = None

def get_openclaw() -> OpenClawBridge:
    global _openclaw
    if _openclaw is None: _openclaw = OpenClawBridge()
    return _openclaw


if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Kullanım: python mudahale/openclaw_bridge.py <TOKEN>")
        sys.exit(1)
    oc = OpenClawBridge()
    oc.telegram_baslat(token)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        oc.durdur()
