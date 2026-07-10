import os
import subprocess
from dotenv import load_dotenv

load_dotenv()


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
    LITELLM_URL = os.getenv("LITELLM_URL", f"http://{_ROUTER_HOST}:20128/v1")
    LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-58bbadde44171bff-6jq5bl-7378c3af")

    MAHKEME_MODEL = os.getenv("MAHKEME_MODEL", "karisik")
    FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "karisik")
    KOD_MODEL = os.getenv("KOD_MODEL", "dijitalvarlik")
    WEB_MODEL = os.getenv("WEB_MODEL", "karisik")

    # Servisler
    BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "http://localhost:3004")

    # Hafiza
    MEM0_DATA_DIR = os.getenv("MEM0_DATA_DIR", "./altyapi/mem0_data")
    LETTA_DATA_DIR = os.getenv("LETTA_DATA_DIR", "./altyapi/letta_data")

    # 9router uyumlulugu
    ROUTER9_URL = LITELLM_URL
    ROUTER9_KEY = LITELLM_KEY

config = Config()
