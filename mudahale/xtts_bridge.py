"""
XTTS Bridge — Hafif Ses Klonlama (F5-TTS alternatifi).

3 saniyelik referans ses ile klonlama. GPU/CPU çalışır.
VRAM Manager entegre.
"""
from pathlib import Path
from typing import Optional


class XTTSBridge:
    """Coqui XTTS ses klonlama."""

    def __init__(self):
        self._ready = False
        self._model = None
        try:
            from TTS.api import TTS as CoquiTTS
            self._CoquiTTS = CoquiTTS
            self._ready = True
        except ImportError:
            pass

    def hazir_mi(self) -> bool:
        return self._ready

    def konus(self, metin: str, ref_ses: str = None, cikis: str = None) -> dict:
        """
        Metni seslendir. Ref ses varsa klonlar.

        Args:
            metin: Seslendirilecek metin
            ref_ses: Referans ses dosyası (3-5 saniye, .wav)
            cikis: Çıktı dosya yolu (yoksa temp)
        """
        if not self._ready:
            return {"status": "error", "message": "XTTS model yuklenemedi"}

        try:
            from altyapi.vram_manager import vram

            def _yukle():
                return self._CoquiTTS(
                    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                    progress_bar=False,
                )

            with vram.acquire("xtts", _yukle) as tts:
                import tempfile, os
                if not cikis:
                    cikis = os.path.join(tempfile.gettempdir(), "dv_xtts_out.wav")

                if ref_ses and os.path.exists(ref_ses):
                    tts.tts_to_file(
                        text=metin[:500],
                        speaker_wav=ref_ses,
                        language="tr",
                        file_path=cikis,
                    )
                else:
                    tts.tts_to_file(
                        text=metin[:500],
                        file_path=cikis,
                    )

                return {"status": "ok", "file": cikis}

        except Exception as e:
            vram.evict("xtts")
            return {"status": "error", "message": str(e)[:300]}


_xtts: Optional[XTTSBridge] = None

def get_xtts() -> XTTSBridge:
    global _xtts
    if _xtts is None:
        _xtts = XTTSBridge()
    return _xtts
