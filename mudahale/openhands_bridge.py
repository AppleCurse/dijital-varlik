"""
OpenHands Bridge — Alt Ajan Olarak OpenHands
Agent-canvas API'si uzerinden alt ajan baslatir.
"""
import requests
import os
from typing import Optional
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OPENHANDS_URL = os.getenv("OPENHANDS_API_URL", "http://localhost:18000")
OPENHANDS_KEY = os.getenv("OPENHANDS_AUTOMATION_API_KEY", "")


class OpenHandsBridge:
    """OpenHands agent-canvas alt ajan koprusu."""

    def __init__(self):
        self.base_url = OPENHANDS_URL
        self.api_key = OPENHANDS_KEY
        self._ready = self._check()

    def _check(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def hazir_mi(self) -> bool:
        return self._ready

    def calistir(self, gorev: str) -> dict:
        """OpenHands API'sine gorev gonder."""
        if not self._ready:
            return {"status": "error", "message": "OpenHands API'ye ulasilamiyor"}

        try:
            r = requests.post(
                f"{self.base_url}/api/conversations",
                json={"message": gorev[:500]},
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if r.status_code in (200, 201):
                data = r.json()
                return {"status": "ok", "conversation_id": data.get("id", "?"),
                        "message": f"OpenHands agent baslatildi"}
            return {"status": "error", "message": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}


_openhands: Optional[OpenHandsBridge] = None

def get_openhands() -> OpenHandsBridge:
    global _openhands
    if _openhands is None:
        _openhands = OpenHandsBridge()
    return _openhands
