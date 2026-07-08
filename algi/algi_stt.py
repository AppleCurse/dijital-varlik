"""
GERCEK KONUSMA TANIMA (STT) — faster-whisper + sounddevice
===========================================================
CPU'da calisir. Mikrofondan sesi alir, metne cevirir.
"""
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from pathlib import Path
import threading
import queue
import time
from typing import Optional

MODEL_BOYUTU = "tiny"  # tiny (400MB), small (1GB), medium (3GB)
ORNEKLEME_HIZI = 16000
SES_SURE_SN = 3  # kac saniyelik parcalar halinde islenecek


class GercekMikrofon:
    """Mikrofondan gercek zamanli ses yakalama ve STT."""

    def __init__(self, model_boyutu: str = MODEL_BOYUTU):
        self.model_boyutu = model_boyutu
        self.model = None
        self._dinleme = False
        self._kuyruk = queue.Queue()
        self._thread = None
        self._ses_parcalari = []
        self._hazir = False
        self._model_yukle()

    def _model_yukle(self):
        """Whisper modelini CPU'ya yukle."""
        try:
            self.model = WhisperModel(
                self.model_boyutu,
                device="cpu",
                compute_type="int8"  # CPU icin en hizli
            )
            self._hazir = True
        except Exception as e:
            print(f"[STT] Model yukleme hatasi: {e}")
            self._hazir = False

    def hazir_mi(self) -> bool:
        return self._hazir and self.model is not None

    def _ses_geri_cagirma(self, indata, frames, time_info, status):
        """sounddevice callback — gelen sesi kuyruga ekler."""
        if status:
            print(f"[STT] Ses durumu: {status}")
        if self._dinleme:
            self._kuyruk.put(indata.copy())

    def dinle_baslat(self):
        """Mikrofon dinlemeyi arka planda baslat."""
        if not self.hazir_mi():
            return False
        self._dinleme = True
        self._thread = threading.Thread(target=self._dinleme_dongusu, daemon=True)
        self._thread.start()
        return True

    def _dinleme_dongusu(self):
        """Arka plan ses yakalama dongusu."""
        try:
            with sd.InputStream(
                samplerate=ORNEKLEME_HIZI,
                channels=1,
                callback=self._ses_geri_cagirma,
                blocksize=int(ORNEKLEME_HIZI * SES_SURE_SN),
            ):
                while self._dinleme:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[STT] Dinleme hatasi: {e}")
            self._dinleme = False

    def dinle_durdur(self):
        self._dinleme = False
        if self._thread:
            self._thread.join(timeout=2)

    def sesi_metne_cevir(self, ses_verisi: np.ndarray) -> Optional[str]:
        """Whisper ile sesi metne cevir. SADECE TURKCE."""
        if not self.hazir_mi() or self.model is None:
            return None
        try:
            ses_verisi = ses_verisi.flatten().astype(np.float32)
            # RMS enerji esigi — sessiz gurultuyu reddet
            rms = float(np.sqrt(np.mean(ses_verisi ** 2)))
            if rms < 0.008:  # sadece net insan sesi
                return None
            segments, _ = self.model.transcribe(
                ses_verisi,
                language="tr",
                task="transcribe",
            )
            metin = " ".join(s.text for s in segments)
            return metin.strip() if metin.strip() else None
        except Exception as e:
            return None

    def son_kuyruktan_oku(self, timeout: float = 5.0) -> Optional[str]:
        """Kuyruktan ses al, metne cevir."""
        try:
            ses = self._kuyruk.get(timeout=timeout)
            return self.sesi_metne_cevir(ses)
        except queue.Empty:
            return None
        except Exception as e:
            print(f"[STT] Okuma hatasi: {e}")
            return None


# Global instance
_mikrofon = None

def get_mikrofon() -> GercekMikrofon:
    global _mikrofon
    if _mikrofon is None:
        _mikrofon = GercekMikrofon()
    return _mikrofon
