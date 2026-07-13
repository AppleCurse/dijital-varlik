"""
Sensory: TTS (Text-to-Speech) Node — Metni sese cevirme.
espeak-ng ile calisir, F5-TTS GPU geldiginde aktif olur.
"""
import subprocess
from nodes import register

register("tts", "sensory", "nodes.sensory.tts_node",
         description="Metin-ses cevirme (espeak-ng / F5-TTS)",
         deps=["espeak-ng"])


class TTSNode:
    def __init__(self):
        self._ready = self._check_espeak()

    def _check_espeak(self) -> bool:
        try:
            r = subprocess.run(["espeak-ng", "--version"],
                             capture_output=True, timeout=3)
            return r.returncode == 0
        except Exception:
            return False

    def hazir_mi(self) -> bool:
        return self._ready

    def konus(self, text: str, lang: str = "tr"):
        if not self._ready:
            return False
        try:
            subprocess.run(["espeak-ng", "-v", lang, text[:500]],
                         capture_output=True, timeout=30)
            return True
        except Exception:
            return False


_tts_instance = None


def get_tts() -> TTSNode:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSNode()
    return _tts_instance
