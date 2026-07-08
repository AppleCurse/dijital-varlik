"""
Hebo Gateway Bridge — MCP-native LLM Routing
Hebo Gateway Bun/TS projesidir. HTTP API uzerinden baglanir.
Calismiyorsa fallback olarak 9router kullanilir.
"""
import requests
import subprocess
import os
from pathlib import Path
from typing import Optional
from config.config import config

ROOT = Path(__file__).resolve().parent.parent
HEBO_DIR = ROOT / "hebo-gateway-main"
HEBO_DEFAULT_PORT = 3002


class HeboBridge:
    """Hebo Gateway HTTP koprusu. MCP routing ve LLM yasam dongusu yonetimi."""

    def __init__(self, port: int = None):
        self.port = port or HEBO_DEFAULT_PORT
        self.base_url = f"http://localhost:{self.port}"
        self._ready = False
        self._bootstrap()

    def _bootstrap(self):
        self._ready = self._check_health()

    def _check_health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def hazir_mi(self) -> bool:
        return self._ready or HEBO_DIR.exists()

    def baslat(self) -> dict:
        """Hebo Gateway'i baslat (Bun gerektirir)."""
        if not HEBO_DIR.exists():
            return {"status": "error", "message": "hebo-gateway-main reposu yok"}

        if self._check_health():
            return {"status": "ok", "message": f"Zaten calisiyor :{self.port}"}

        try:
            subprocess.Popen(
                ["bun", "run", "start"],
                cwd=str(HEBO_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, "PORT": str(self.port)}
            )
            return {"status": "ok", "message": f"Baslatildi :{self.port}"}
        except FileNotFoundError:
            return {"status": "error", "message": "Bun kurulu degil. curl -fsSL https://bun.sh/install | bash"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}

    def route(self, model: str = None) -> dict:
        """Model routing — Hebo aktifse onu, yoksa 9router'i kullan."""
        if self._check_health():
            try:
                r = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": model or config.MAHKEME_MODEL,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5,
                    },
                    headers={"Authorization": f"Bearer {config.LITELLM_KEY}"},
                    timeout=10
                )
                if r.status_code == 200:
                    return {"status": "ok", "via": "hebo", "port": self.port}
            except Exception:
                pass

        return {"status": "ok", "via": "9router", "port": 20128,
                "message": "Hebo calismiyor, 9router fallback"}

    def calistir(self, gorev: str) -> dict:
        """Genel routing islemi."""
        return self.route()


_hebo: Optional[HeboBridge] = None

def get_hebo() -> HeboBridge:
    global _hebo
    if _hebo is None:
        _hebo = HeboBridge()
    return _hebo
