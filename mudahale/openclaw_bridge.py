"""
OpenClaw Bridge — 7/24 Mesajlaşma İstihbaratı.

Platformlar: Telegram, WhatsApp (Twilio), X (Twitter)
Şu an aktif: Telegram bot

Kullanım:
    python mudahale/openclaw_bridge.py  # Telegram bot'u başlat
"""
import sys, os, asyncio, threading
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class OpenClawBridge:
    """Çoklu platform mesajlaşma köprüsü."""

    def __init__(self):
        self._ready = False
        self._bot = None
        self._app = None
        self._thread = None
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if self._token:
            self._ready = True

    def hazir_mi(self) -> bool:
        return self._ready

    @property
    def token_set(self) -> bool:
        return bool(self._token)

    def telegram_baslat(self, token: str = None):
        """Telegram bot'u arka planda başlat."""
        if token:
            self._token = token
        if not self._token:
            print("[OpenClaw] ❌ TELEGRAM_BOT_TOKEN gerekli. @BotFather'dan al.")
            return False

        self._ready = True
        self._thread = threading.Thread(target=self._run_telegram, daemon=True)
        self._thread.start()
        print(f"[OpenClaw] 🟢 Telegram bot başlatıldı")
        return True

    def _run_telegram(self):
        """Telegram bot ana döngüsü (ayrı thread)."""
        import asyncio
        try:
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

            async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text(
                    "🤖 Dijital Varlık hizmetinizde.\n"
                    "Sohbet edebilir, kod yazdırabilir, web'de gezinebilir,\n"
                    "görüntü analiz ettirebilir, yüz tanıma yapabilirsiniz.\n\n"
                    "Komutlar: /saat /tarih /ara /kod /durum"
                )

            async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
                msg = update.message.text
                if not msg: return
                await update.message.chat.send_action("typing")
                try:
                    from karar.aspasia import aspasia_kesici, aspasia_format, aspasia_system_prompt
                    yerel = aspasia_kesici(msg)
                    if yerel:
                        await update.message.reply_text(yerel)
                        return
                except: pass
                try:
                    from altyapi.litellm_bridge import litellm
                    from karar.aspasia import aspasia_system_prompt
                    sistem = aspasia_system_prompt()
                    r = litellm.chat([
                        {"role": "system", "content": sistem},
                        {"role": "user", "content": msg}
                    ], max_tokens=400)
                    if r and r.get("content"):
                        await update.message.reply_text(r["content"][:1500])
                        return
                except: pass
                await update.message.reply_text("Düşüncelerimizi sıraya dizelim Mösyö. Bir an.")

            async def komut_saat(update: Update, context: ContextTypes.DEFAULT_TYPE):
                from datetime import datetime
                await update.message.reply_text(f"Saat {datetime.now().strftime('%H:%M')}. Zaman stratejinin en sessiz ortağıdır.")

            async def komut_tarih(update: Update, context: ContextTypes.DEFAULT_TYPE):
                from datetime import datetime
                await update.message.reply_text(f"{datetime.now().strftime('%d.%m.%Y')}. Takvimler değişir, sorular kalır.")

            async def komut_durum(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    from wsl_backend.main import _sistem_durumu
                    await update.message.reply_text(_sistem_durumu())
                except:
                    await update.message.reply_text("Sistem durumu alınamadı.")

            async def main():
                self._app = Application.builder().token(self._token).build()
                self._app.add_handler(CommandHandler("start", start))
                self._app.add_handler(CommandHandler("saat", komut_saat))
                self._app.add_handler(CommandHandler("tarih", komut_tarih))
                self._app.add_handler(CommandHandler("durum", komut_durum))
                self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
                print("[OpenClaw] Telegram bot dinlemede...")
                await self._app.run_polling()

            asyncio.run(main())
        except Exception as e:
            print(f"[OpenClaw] Telegram hatası: {e}")
            self._ready = False

    def durdur(self):
        if self._app:
            self._app.stop()
        print("[OpenClaw] Durduruldu.")


# Global instance
_openclaw: Optional[OpenClawBridge] = None

def get_openclaw() -> OpenClawBridge:
    global _openclaw
    if _openclaw is None:
        _openclaw = OpenClawBridge()
    return _openclaw


if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Kullanım: python mudahale/openclaw_bridge.py <BOT_TOKEN>")
        print("Token al: https://t.me/BotFather → /newbot")
        sys.exit(1)

    oc = OpenClawBridge()
    oc.telegram_baslat(token)
    try:
        while True:
            import time; time.sleep(1)
    except KeyboardInterrupt:
        oc.durdur()
