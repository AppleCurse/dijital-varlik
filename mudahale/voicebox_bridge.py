"""
Voicebox Bridge — Jamie Pine Voicebox REST API kopusu.

Voicebox, yerel GPU'da calisan ses I/O motorudur:
- /speak     → metni seslendir (TTS)
- /transcribe → sesi yaziya cevir (STT)
- /health    → saglik kontrolu
- MCP tools: voicebox.speak, voicebox.transcribe

Kullanim:
    from mudahale.voicebox_bridge import Voicebox, voicebox_konus, voicebox_dinle, voicebox_yaziya_dok

    vb = Voicebox()
    vb.speak("Merhaba dunya", profile="tr-v1")
    text = vb.listen()  # mikrofondan dinle
    text = vb.transcribe("kayit.wav")
"""
import requests
import io
import wave
import json
from typing import Optional


VOICEBOX_URL = "http://localhost:8001"


class Voicebox:
    """Voicebox REST API istemcisi."""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or VOICEBOX_URL).rstrip("/")
        self._ready = None

    # ── Saglik ──

    def hazir_mi(self) -> bool:
        """Voicebox servisi ayakta mi?"""
        if self._ready is not None:
            return self._ready
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            self._ready = r.status_code == 200
            return self._ready
        except Exception:
            self._ready = False
            return False

    # ── TTS: Metin → Ses ──

    def speak(self, text: str, profile: str = None) -> dict:
        """Metni seslendir. profile: ses profili adi (opsiyonel)."""
        if not self.hazir_mi():
            return {"success": False, "error": "Voicebox servisi kapali"}

        payload = {"text": text}
        if profile:
            payload["profile"] = profile

        try:
            resp = requests.post(
                f"{self.base_url}/speak",
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except requests.HTTPError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── STT: Ses Dosyasi → Metin ──

    def transcribe(self, audio_path: str = None, audio_bytes: bytes = None) -> dict:
        """Ses dosyasini yaziya cevir. Dosya yolu VEYA bytes ver."""
        if not self.hazir_mi():
            return {"success": False, "error": "Voicebox servisi kapali"}

        try:
            if audio_bytes:
                files = {"audio": ("recording.wav", audio_bytes, "audio/wav")}
            elif audio_path:
                with open(audio_path, "rb") as f:
                    files = {"audio": (audio_path.split("/")[-1], f.read(), "audio/wav")}
            else:
                return {"success": False, "error": "audio_path veya audio_bytes gerekli"}

            resp = requests.post(
                f"{self.base_url}/transcribe",
                files=files,
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "text": data.get("text", ""), "data": data}
        except requests.HTTPError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Dinle: Mikrofon → STT → Metin ──

    def listen(self, duration: float = 5.0, sample_rate: int = 16000) -> str | None:
        """Mikrofondan dinle, Voicebox STT ile yaziya cevir."""
        audio_bytes = self._capture_mic(duration, sample_rate)
        if not audio_bytes:
            return None

        result = self.transcribe(audio_bytes=audio_bytes)
        if result.get("success"):
            return result.get("text", "")
        return None

    def _capture_mic(self, duration: float, sample_rate: int) -> bytes | None:
        """Mikrofondan ses yakala, WAV bytes dondur."""
        try:
            import sounddevice as sd
            import numpy as np

            print(f"  Mikrofon dinleniyor ({duration}s)...")
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16"
            )
            sd.wait()

            # WAV bytes'a cevir
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            buf.seek(0)
            return buf.read()
        except ImportError:
            print("  sounddevice kurulu degil. pip install sounddevice")
            return None
        except Exception as e:
            print(f"  Mikrofon hatasi: {e}")
            return None

    # ── Profiller ──

    def profiles(self) -> list:
        """Kullanilabilir ses profillerini listele."""
        if not self.hazir_mi():
            return []
        try:
            resp = requests.get(f"{self.base_url}/profiles", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []


# ── Kolay Fonksiyonlar (mevcut API ile uyumlu) ──

def voicebox_konus(metin: str, profil: str = None) -> dict:
    """Metni seslendir (kolay fonksiyon)."""
    vb = Voicebox()
    return vb.speak(metin, profile=profil)


def voicebox_dinle(sure: float = 5.0) -> str | None:
    """Mikrofondan dinle, metne cevir (kolay fonksiyon)."""
    vb = Voicebox()
    return vb.listen(duration=sure)


def voicebox_yaziya_dok(ses_dosyasi: str) -> dict:
    """Ses dosyasini yaziya cevir (kolay fonksiyon)."""
    vb = Voicebox()
    return vb.transcribe(audio_path=ses_dosyasi)
