"""
Katman 2: Fiziksel Müdahale — Fare, Klavye, Web
Bileşenler: Browser Use (browserless:3004), Skyvern, Agent S

Tüm bridge'ler bu paketten import edilir.
Sınıf bazlı bridge'ler: class adıyla
Fonksiyon bazlı bridge'ler: fonksiyon adıyla (voicebox, web_tools)
"""
# Sinif bazli bridge'ler
from .browser_bridge import get_browser, BrowserBridge
from .atom_bridge import get_atom, ATomBridge
from .qwen_bridge import get_qwen, QwenVLBridge
from .weather_bridge import WeatherBridge
from .deepface_bridge import DeepFaceBridge
from .f5tts_bridge import F5TTSBridge
from .firecrawl_bridge import FirecrawlBridge
from .openclaw_bridge import OpenClawBridge
from .pipecat_bridge import PipecatBridge
from .xtts_bridge import XTTSBridge
from .browser_use_bridge import get_browser_use, BrowserUseBridge

# Fonksiyon bazli bridge'ler (sinif yok, dogrudan fonksiyon cagirilir)
from .voicebox_bridge import Voicebox, voicebox_konus, voicebox_dinle, voicebox_yaziya_dok
from .web_tools import web_fetch, web_extract_title, web_screenshot, web_navigate

