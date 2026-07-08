"""
AIRI Bridge — 3D Avatar (Live2D/VRM, WebGPU)
⚠️ WebGPU destekli tarayici GEREKIR. Bun runtime ile calisir.
"""
from typing import Optional
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AIRI_DIR = ROOT / "airi-main"


class AiriBridge:
    """AIRI 3D avatar koprusu. WebGPU bekliyor."""

    def __init__(self):
        self._ready = AIRI_DIR.exists()

    def hazir_mi(self) -> bool:
        return self._ready

    def calistir(self, gorev: str) -> dict:
        return {"status": "ok",
                "message": f"AIRI avatar hazir (WebGPU tarayici gerekli). Gorev: {gorev[:100]}",
                "requires": "WebGPU browser + Bun runtime"}


_airi: Optional[AiriBridge] = None

def get_airi() -> AiriBridge:
    global _airi
    if _airi is None:
        _airi = AiriBridge()
    return _airi
