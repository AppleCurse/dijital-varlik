"""
GERCEK SES SENTEZLEME (TTS) — espeak-ng + CPU
===============================================
Internet yokken calisir. Turkce seslendirme.
GPU gerekmez. F5-TTS GPU gelince devreye girer.
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional


class GercekTTS:
    """CPU'da calisan gercek TTS motoru."""

    def __init__(self):
        self._espeak_yolu = self._espeak_bul()
        self._hazir = self._espeak_yolu is not None

    def _espeak_bul(self) -> Optional[str]:
        for yol in ["/usr/bin/espeak-ng", "/usr/bin/espeak", "/usr/local/bin/espeak-ng"]:
            if Path(yol).exists():
                return yol
        try:
            r = subprocess.run(["which", "espeak-ng"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return r.stdout.strip()
        except:
            pass
        return None

    def hazir_mi(self) -> bool:
        return self._hazir

    def konus(self, metin: str, hiz: int = 160) -> dict:
        """Metni gercek sese cevir ve hoparlorden cal."""
        if not self.hazir_mi():
            return {"status": "error", "message": "espeak-ng bulunamadi"}
        try:
            subprocess.run(
                [self._espeak_yolu, "-v", "tr", "-s", str(hiz), metin[:2000]],
                capture_output=True,
                timeout=30
            )
            return {"status": "success", "message": f"Seslendirildi: {metin[:80]}..."}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "TTS zaman asimi"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def dosyaya_kaydet(self, metin: str, dosya_yolu: str = None) -> Optional[str]:
        """Sesi WAV dosyasina kaydet."""
        if not self.hazir_mi():
            return None
        if dosya_yolu is None:
            dosya_yolu = tempfile.mktemp(suffix=".wav")
        try:
            subprocess.run(
                [self._espeak_yolu, "-v", "tr", "-w", dosya_yolu, metin[:2000]],
                capture_output=True,
                timeout=30
            )
            return dosya_yolu if Path(dosya_yolu).exists() else None
        except:
            return None


_tts = None

def get_tts() -> GercekTTS:
    global _tts
    if _tts is None:
        _tts = GercekTTS()
    return _tts
