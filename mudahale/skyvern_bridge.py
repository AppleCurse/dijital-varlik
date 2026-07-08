"""
Skyvern Bridge — Otonom Web Otomasyonu
Browserless CDP uzerinden calisir. Skyvern sunucusu opsiyonel.
"""
import asyncio
import sys
import os
from typing import Optional
from config.config import config

SKYVERN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skyvern-main")
if SKYVERN_ROOT not in sys.path:
    sys.path.insert(0, SKYVERN_ROOT)


class SkyvernBridge:
    """Skyvern/Browserless web otomasyon koprusu."""

    def __init__(self):
        self.browserless_url = config.BROWSERLESS_URL
        self._ready = False
        self._server_ready = False
        self._bootstrap()

    def _bootstrap(self):
        """Baglantilari kontrol et."""
        self._check_browserless()
        self._check_skyvern_server()

    def _check_browserless(self):
        try:
            import requests
            r = requests.get(f"{self.browserless_url}/json/version", timeout=5)
            self._ready = r.status_code == 200
        except Exception:
            self._ready = False

    def _check_skyvern_server(self):
        try:
            import requests
            r = requests.get("http://localhost:8000/api/v1/health", timeout=3)
            self._server_ready = r.status_code == 200
        except Exception:
            self._server_ready = False

    def hazir_mi(self) -> bool:
        return self._ready

    def calistir(self, gorev: str) -> dict:
        """Web gorevini browser-use uzerinden calistir (Skyvern sunucusu olmadan)."""
        if not self._ready:
            return {"status": "error", "message": "Browserless hazir degil"}

        try:
            from mudahale.browser_use_bridge import get_browser_use
            bu = get_browser_use()
            if bu.hazir_mi():
                sonuc = bu.calistir(gorev)
                return {"status": "success", "message": sonuc or "Tamamlandi", "via": "browser-use"}
        except Exception as e:
            pass

        return {"status": "error", "message": "Browser-use da hazir degil"}

    def form_doldur(self, url: str, form_data: dict) -> dict:
        """Web formu otomatik doldur."""
        gorev = f"Go to {url} and fill the form with: {form_data}. Submit."
        return self.calistir(gorev)

    def sayfa_cek(self, url: str) -> dict:
        """Sayfa icerigini cek."""
        gorev = f"Go to {url} and return the page title and main content summary."
        return self.calistir(gorev)


_skyvern: Optional[SkyvernBridge] = None

def get_skyvern() -> SkyvernBridge:
    global _skyvern
    if _skyvern is None:
        _skyvern = SkyvernBridge()
    return _skyvern
