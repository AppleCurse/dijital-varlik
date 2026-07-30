import os
import subprocess
from dotenv import load_dotenv

# config/.env dosyasini yukle (bulundugu dizine gore)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_env_path)


def _windows_ip() -> str:
    """WSL2'de Windows host IP'sini bul."""
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if "via" in parts:
                idx = parts.index("via")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    except Exception:
        pass
    return "172.23.96.1"  # fallback


class Config:
    # 9Router — WSL2'de Windows host IP'si (localhost çalışmaz)
    _ROUTER_HOST = os.getenv("ROUTER_HOST", _windows_ip())
    LITELLM_URL = os.getenv("LITELLM_URL", os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1"))
    LITELLM_KEY = os.getenv("LITELLM_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

    MAHKEME_MODEL = os.getenv("MAHKEME_MODEL", "deepseek-v4-flash")
    FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "deepseek-v4-flash")
    KOD_MODEL = os.getenv("KOD_MODEL", "dijitalvarlik")
    WEB_MODEL = os.getenv("WEB_MODEL", "deepseek-v4-flash")

    # Servisler
    BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "http://localhost:3004")

    # Hafiza
    MEM0_DATA_DIR = os.getenv("MEM0_DATA_DIR", "./altyapi/mem0_data")
    LETTA_DATA_DIR = os.getenv("LETTA_DATA_DIR", "./altyapi/letta_data")

    # 9router uyumlulugu
    ROUTER9_URL = LITELLM_URL
    ROUTER9_KEY = LITELLM_KEY

config = Config()
