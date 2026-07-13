"""
Sensory: STT (Speech-to-Text) Node — Mikrofondan ses tanima.
Kendi kendine kurulur: faster-whisper + sounddevice.
"""
from nodes import register

register("stt", "sensory", "nodes.sensory.stt_node",
         description="Mikrofon ses tanima (faster-whisper)",
         deps=["faster-whisper", "sounddevice"])


class STTNode:
    def __init__(self):
        self._ready = False
        self._model = None
        self._model_size = "tiny"
        self._bootstrap()

    def _bootstrap(self):
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
            self._ready = True
        except Exception as e:
            print(f"[STT] Bootstrap failed: {e}")

    def hazir_mi(self) -> bool:
        return self._ready

    def dinle(self, duration: float = 5.0) -> str:
        if not self._ready:
            return ""
        try:
            import sounddevice as sd
            import numpy as np
            audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype="float32")
            sd.wait()
            segments, _ = self._model.transcribe(audio.flatten(), beam_size=5)
            return " ".join(s.text for s in segments)
        except Exception as e:
            print(f"[STT] Error: {e}")
            return ""


_stt_instance = None


def get_stt() -> STTNode:
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = STTNode()
    return _stt_instance
