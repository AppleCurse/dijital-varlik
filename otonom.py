#!/usr/bin/env python3
"""
OTONOM — Sürekli Dinleyen, Kendi Karar Veren Dijital Varlık.

Tek döngü. Tüm zincirler buradan geçer.
Girişi sınıflandırır, zincire yollar, seslendirir, tekrar dinler.

Kullanım:
    python otonom.py              # Sürekli mod (mikrofon/text)
    python otonom.py --once "metin"  # Tek seferlik
"""
import sys
import time
import signal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from runtime import bus, state, Event, EventType, memory
from altyapi.vram_manager import vram
from altyapi.kesici import kesici


# ═══════════════════════════════════════════════════════════
# GİRİŞ SINIFLANDIRICI
# ═══════════════════════════════════════════════════════════

def siniflandir(metin: str) -> str:
    """
    Girdiyi sınıflandır, uygun zincire yönlendir.

    Returns: "ses", "kod", "goru", "yuz", "web"
    """
    lower = metin.lower()

    # Yüz tanıma tetikleyicileri
    yuz_kelimeler = ["yüz", "fotoğraf", "resim", "foto", "kim bu",
                     "tanı", "yüz tanıma", "yüz analizi", "görüntü"]
    if any(k in lower for k in yuz_kelimeler):
        # Görüntü yolu var mı?
        if any(ext in lower for ext in [".jpg", ".png", ".jpeg", "/"]):
            return "goru"

    # Kod tetikleyicileri
    kod_kelimeler = ["kod yaz", "script", "python", "hesapla", "fonksiyon",
                     "program", "yaz", "oluştur", "topla", "çıkar"]
    if any(k in lower for k in kod_kelimeler):
        return "kod"

    # Web tetikleyicileri
    web_kelimeler = ["site", "web", "tarayıcı", "http", "tıkla",
                     "sayfa", "form", "indir", "url", "link", "gez"]
    if any(k in lower for k in web_kelimeler):
        return "web"

    # Görü tetikleyicileri
    goru_kelimeler = ["ekran", "görüntü", "grafik", "ne var", "göster"]
    if any(k in lower for k in goru_kelimeler):
        return "goru"

    return "ses"


# ═══════════════════════════════════════════════════════════
# ANA DÖNGÜ
# ═══════════════════════════════════════════════════════════

class OtonomDijitalVarlik:
    """Sürekli çalışan, kendi karar veren döngü."""

    def __init__(self):
        self.running = False
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.adim = 0
        memory.session_start(self.session_id, {"tip": "otonom"})

        # Sinyal yakalama (Ctrl+C)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print("\n⏹ Kapatılıyor...")
        self.running = False

    def dinle(self) -> str | None:
        """Girdi al: mikrofon veya klavye."""
        # Mikrofon dene
        try:
            from algi.algi_stt import get_mikrofon
            mik = get_mikrofon()
            if mik and mik.hazir_mi():
                print("🎤 Dinliyorum...")
                metin = mik.dinle()
                if metin:
                    print(f"   STT: {metin}")
                    bus.publish(Event(EventType.SPEECH_RECOGNIZED, {"text": metin}))
                    return metin
        except Exception:
            pass

        # Klavye fallback
        try:
            return input("✏️  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

    def isle(self, metin: str) -> str:
        """Girdiyi işle, uygun zincire yönlendir."""
        self.adim += 1
        state.update(active_task=metin, current_text=metin)
        bus.publish(Event(EventType.TASK_CREATED, {"text": metin[:120]}))

        # Kesici: basit sorgu mu?
        yerel = kesici.tani(metin)
        if yerel:
            print(f"⚡ Kesici: {yerel}")
            return yerel

        # Sınıflandır ve zincirle
        tip = siniflandir(metin)

        if tip == "kod":
            from zincir import zincir_kod
            sonuc = zincir_kod(metin)
            return str(sonuc)[:500] if isinstance(sonuc, str) else str(sonuc.get("message", ""))[:500]

        elif tip == "web":
            from zincir import zincir_ses
            sonuc = zincir_ses(metin)
            return str(sonuc)[:500] if isinstance(sonuc, str) else ""

        elif tip == "goru":
            from zincir import zincir_goru
            sonuc = zincir_goru()
            return str(sonuc)[:500] if isinstance(sonuc, str) else ""

        else:
            from zincir import zincir_ses
            sonuc = zincir_ses(metin)
            return str(sonuc)[:500] if isinstance(sonuc, str) else ""

    def konus(self, metin: str):
        """Seslendir."""
        from zincir import _konus
        _konus(metin)

    def calistir(self, once: str = None):
        """Ana döngü."""
        print("\n" + "=" * 50)
        print("  🤖 OTONOM DİJİTAL VARLIK")
        print("  Sürekli dinliyor, kendi karar veriyor.")
        print("  'q' veya Ctrl+C ile çık.")
        print("=" * 50)

        self.running = True
        vram.evict_all()

        if once:
            # Tek seferlik mod
            print(f"\n📝 Girdi: {once}")
            sonuc = self.isle(once)
            print(f"✅ {sonuc[:200]}")
            self.konus(sonuc[:300])
            self.running = False
        else:
            # Sürekli döngü
            while self.running:
                try:
                    metin = self.dinle()
                    if not metin or metin.lower() in ('q', 'quit', 'çık', 'exit'):
                        self.running = False
                        break

                    print(f"\n📝 [{self.adim+1}] {metin[:100]}")
                    sonuc = self.isle(metin)
                    print(f"✅ {sonuc[:200] if sonuc else '(boş)'}")

                    if sonuc:
                        self.konus(sonuc[:300])

                    memory.session_update(self.session_id, {
                        "adim": self.adim, "girdi": metin[:100], "sonuc": str(sonuc)[:100]
                    })

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Hata: {e}")

        # Temizlik
        vram.evict_all()
        memory.session_end(self.session_id)
        print("\n👋 Otonom Dijital Varlık kapandı.")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Otonom Dijital Varlik")
    parser.add_argument("--once", type=str, help="Tek seferlik giris")
    args = parser.parse_args()

    otonom = OtonomDijitalVarlik()
    otonom.calistir(args.once)
