"""
Katman 2: Fiziksel Müdahale — Fare, Klavye, Web
Bileşenler: Browser Use (browserless:3001), Skyvern, Agent S
"""
from .browser_bridge import get_browser, BrowserBridge
from .skyvern_bridge import get_skyvern, SkyvernBridge

__all__ = ["get_browser", "BrowserBridge", "get_skyvern", "SkyvernBridge"]
