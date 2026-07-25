"""
OpenClaw Bridge — 7/24 Mesajlasma Istihbarati (Raw HTTP API).

Platformlar: Telegram, WhatsApp (Twilio), X (Twitter)
Telegram: Raw HTTP bot API (sifir async sorunu)
WhatsApp: Twilio Business API
X: Twitter API v2 (opsiyonel)

Kullanim:
    from mudahale.openclaw_bridge import get_openclaw
    oc = get_openclaw()
    oc.telegram_baslat()           # Telegram polling baslat
    oc.whatsapp_gonder("+90...", "mesaj")  # WhatsApp mesaj gonder
"""
import sys, os, time, json, requests, threading
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', '.env'))

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TELEGRAM_API = "https://api.telegram.org/bot"
TWILIO_API = "https://api.twilio.com/2010-04-01"


class OpenClawBridge:
    """Coklu platform mesajlasma koprusu — Telegram + WhatsApp + X."""

    def __init__(self):
        self._ready = False
        self._tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._tg_offset = 0
        self._tg_running = False
        self._tg_thread = None

        # Twilio (WhatsApp)
        self._twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self._twilio_auth = os.getenv("TWILIO_AUTH_TOKEN", "")
        self._twilio_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # +14155238886
        self._twilio_ready = bool(self._twilio_sid and self._twilio_auth and self._twilio_from)

        # X (Twitter)
        self._x_bearer = os.getenv("X_BEARER_TOKEN", "")
        self._x_ready = bool(self._x_bearer)

        if self._tg_token:
            self._ready = True

    def hazir_mi(self) -> bool:
        return self._ready

    @property
    def status(self) -> dict:
        return {
            "telegram": bool(self._tg_token),
            "whatsapp": self._twilio_ready,
            "x_twitter": self._x_ready,
        }

    # ═══════════════════════════════════════════
    # TELEGRAM
    # ═══════════════════════════════════════════

    def _tg_api(self, method: str, data: dict = None) -> dict:
        try:
            url = f"{TELEGRAM_API}{self._tg_token}/{method}"
            r = requests.post(url, json=data, timeout=15) if data else requests.get(url, timeout=15)
            return r.json()
        except:
            return {"ok": False}

    def _tg_send(self, chat_id: int, text: str):
        self._tg_api("sendMessage", {"chat_id": chat_id, "text": text[:4000]})

    def _islem(self, msg: str) -> str:
        """Gelen mesaji isle, 9Router ile yanitla."""
        try:
            from karar.aspasia import aspasia_kesici
            yerel = aspasia_kesici(msg)
            if yerel:
                return yerel
        except:
            pass
        try:
            from altyapi.litellm_bridge import litellm
            from karar.aspasia import aspasia_system_prompt
            r = litellm.chat([
                {"role": "system", "content": aspasia_system_prompt()},
                {"role": "user", "content": msg}
            ], max_tokens=400)
            if r and r.get("content"):
                return r["content"][:1500]
        except:
            pass
        return "Mosyo, su an derin dusunce modundayim. Birazdan donus yapacagim."

    def telegram_baslat(self, token: str = None):
        """Telegram bot'u arka planda baslat (polling, raw HTTP)."""
        if token:
            self._tg_token = token
        if not self._tg_token:
            print("[OpenClaw] Telegram: Token yok")
            return False

        self._ready = True
        self._tg_running = True
        updates = self._tg_api("getUpdates", {"limit": 1, "offset": -1})
        if updates.get("result"):
            self._tg_offset = updates["result"][-1]["update_id"] + 1

        self._tg_thread = threading.Thread(target=self._tg_poll_loop, daemon=True)
        self._tg_thread.start()
        print("[OpenClaw] Telegram: Dinlemede (raw HTTP polling)")
        return True

    def _tg_poll_loop(self):
        while self._tg_running:
            try:
                updates = self._tg_api("getUpdates", {"offset": self._tg_offset, "timeout": 10})
                if updates.get("ok") and updates.get("result"):
                    for upd in updates["result"]:
                        self._tg_offset = upd["update_id"] + 1
                        msg = upd.get("message", {})
                        text = msg.get("text", "")
                        chat_id = msg.get("chat", {}).get("id")
                        photo = msg.get("photo", [])
                        if photo and chat_id:
                            file_id = photo[-1]["file_id"]
                            text = f"[GORSEL: {file_id}] {text or ''}".strip()
                        if chat_id and text:
                            print(f"[OpenClaw] Telegram: {text[:80]}")
                            yanit = self._islem(text)
                            self._tg_send(chat_id, yanit)
                        elif chat_id and photo:
                            self._tg_send(chat_id, "Gorselinizi aldim Mosyo. Ne ogrenmek istersiniz?")
            except Exception as e:
                print(f"[OpenClaw] Telegram poll hatasi: {e}")
                time.sleep(5)

    def telegram_durdur(self):
        self._tg_running = False
        print("[OpenClaw] Telegram: Durduruldu")

    # ═══════════════════════════════════════════
    # WHATSAPP (Twilio Business API)
    # ═══════════════════════════════════════════

    def whatsapp_gonder(self, to_number: str, mesaj: str) -> dict:
        """WhatsApp mesaji gonder (Twilio). to_number: +90... formatinda."""
        if not self._twilio_ready:
            return {"ok": False, "error": "Twilio yapilandirilmadi. TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER .env'e ekleyin."}

        try:
            from_number = self._twilio_from
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            resp = requests.post(
                f"{TWILIO_API}/Accounts/{self._twilio_sid}/Messages.json",
                auth=(self._twilio_sid, self._twilio_auth),
                data={"From": from_number, "To": to_number, "Body": mesaj[:1600]},
                timeout=15
            )
            data = resp.json()
            if resp.status_code == 201:
                print(f"[OpenClaw] WhatsApp: Gonderildi → {to_number}")
                return {"ok": True, "sid": data.get("sid", "")}
            return {"ok": False, "error": data.get("message", str(resp.status_code))}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def whatsapp_gelenleri_oku(self, limit: int = 10) -> list:
        """WhatsApp gelen mesajlari oku (Twilio)."""
        if not self._twilio_ready:
            return []

        try:
            from_number = self._twilio_from
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"

            resp = requests.get(
                f"{TWILIO_API}/Accounts/{self._twilio_sid}/Messages.json",
                auth=(self._twilio_sid, self._twilio_auth),
                params={"To": from_number, "PageSize": limit},
                timeout=15
            )
            if resp.status_code == 200:
                messages = []
                for m in resp.json().get("messages", []):
                    if m.get("direction") == "inbound":
                        messages.append({
                            "from": m.get("from", ""),
                            "body": m.get("body", ""),
                            "date": m.get("date_created", ""),
                        })
                return messages
            return []
        except Exception as e:
            print(f"[OpenClaw] WhatsApp okuma hatasi: {e}")
            return []

    # ═══════════════════════════════════════════
    # X (TWITTER) API v2
    # ═══════════════════════════════════════════

    def x_ara(self, query: str, limit: int = 10) -> list:
        """Twitter'da arama yap (recent tweets)."""
        if not self._x_ready:
            return [{"error": "X_BEARER_TOKEN .env'de tanimli degil"}]

        try:
            resp = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": f"Bearer {self._x_bearer}"},
                params={"query": query, "max_results": min(limit, 50),
                        "tweet.fields": "created_at,public_metrics"},
                timeout=15
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return [{"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}]
        except Exception as e:
            return [{"error": str(e)}]

    def x_kullanici_tweetleri(self, username: str, limit: int = 10) -> list:
        """Bir kullanicinin son tweetlerini getir."""
        if not self._x_ready:
            return [{"error": "X_BEARER_TOKEN .env'de tanimli degil"}]

        try:
            # Once user ID'yi bul
            uid_resp = requests.get(
                f"https://api.twitter.com/2/users/by/username/{username}",
                headers={"Authorization": f"Bearer {self._x_bearer}"},
                timeout=10
            )
            if uid_resp.status_code != 200:
                return [{"error": f"Kullanici bulunamadi: {username}"}]
            user_id = uid_resp.json()["data"]["id"]

            # Tweetleri getir
            resp = requests.get(
                f"https://api.twitter.com/2/users/{user_id}/tweets",
                headers={"Authorization": f"Bearer {self._x_bearer}"},
                params={"max_results": min(limit, 50), "tweet.fields": "created_at,public_metrics"},
                timeout=15
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return [{"error": f"HTTP {resp.status_code}"}]
        except Exception as e:
            return [{"error": str(e)}]

    # ═══════════════════════════════════════════
    # TUMUNU BASLAT / DURDUR
    # ═══════════════════════════════════════════

    def baslat(self):
        """Tum platform dinleyicilerini baslat."""
        print(f"[OpenClaw] Baslatiliyor...")
        print(f"  Telegram: {'AKTIF' if self._tg_token else 'TOKEN YOK'}")
        print(f"  WhatsApp: {'AKTIF' if self._twilio_ready else 'KONFIGURE EDILMEDI'}")
        print(f"  X/Twitter: {'AKTIF' if self._x_ready else 'KONFIGURE EDILMEDI'}")

        if self._tg_token:
            self.telegram_baslat()

        return {
            "telegram": bool(self._tg_token),
            "whatsapp": self._twilio_ready,
            "x_twitter": self._x_ready,
        }

    def durdur(self):
        self.telegram_durdur()
        print("[OpenClaw] Tum platformlar durduruldu.")


_openclaw: Optional[OpenClawBridge] = None


def get_openclaw() -> OpenClawBridge:
    global _openclaw
    if _openclaw is None:
        _openclaw = OpenClawBridge()
    return _openclaw


if __name__ == "__main__":
    oc = OpenClawBridge()
    print(json.dumps(oc.status, indent=2))
    if oc.hazir_mi():
        oc.baslat()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            oc.durdur()
    else:
        print("HATA: TELEGRAM_BOT_TOKEN .env'de tanimli degil.")
