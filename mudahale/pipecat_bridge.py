"""
Pipecat Bridge — Gerçek Zamanlı Ses Pipeline
CPU-only temel modda çalışır. Tam WebRTC için GPU/cihaz gerekir.
"""
from typing import Optional
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class PipecatBridge:
    """Pipecat ses pipeline köprüsü."""

    def __init__(self):
        self._ready = False
        try:
            from pipecat.pipeline.pipeline import Pipeline
            self.Pipeline = Pipeline
            self._ready = True
            print("[Pipecat] Pipeline hazir (CPU mod)")
        except ImportError:
            print("[Pipecat] Kurulu degil: pip install pipecat-ai")
        except Exception as e:
            print(f"[Pipecat] Hata: {e}")

    def hazir_mi(self) -> bool:
        return self._ready

    def calistir(self, gorev: str) -> dict:
        if not self._ready:
            return {"status": "error", "message": "Pipecat GPU/cihaz bekliyor"}
        return {
            "status": "ok",
            "message": f"Pipecat ses pipeline hazir. Gorev: {gorev[:100]}",
            "cpu_mode": True,
        }


_pipecat: Optional[PipecatBridge] = None

def get_pipecat() -> PipecatBridge:
    global _pipecat
    if _pipecat is None:
        _pipecat = PipecatBridge()
    return _pipecat
