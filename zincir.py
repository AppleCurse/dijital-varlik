"""
ZİNCİR — Uçtan Uca Duyu→İşlem→Çıktı Boru Hattı.

Her zincir EventBus üzerinden akar. Modüller birbirini tanımaz.

Kullanım:
    python zincir.py ses "bugün haberlerde ne var"
    python zincir.py goru
    python zincir.py kod "bana web scraper yaz"
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from runtime import bus, state, Event, EventType, memory, gpu
from altyapi.vram_manager import vram


# ═══════════════════════════════════════════════════════════
# ZİNCİR 1: SES → METİN → İŞLE → SES
# ═══════════════════════════════════════════════════════════

def zincir_ses(metin: str = None):
    """
    STT(opsiyonel) → Kesici → smolagents/BrowserUse → TTS → 🔊
    """
    from altyapi.kesici import kesici

    # Adım 0: Mikrofondan dinle (varsa)
    if metin is None:
        try:
            from algi.algi_stt import get_mikrofon
            mik = get_mikrofon()
            print("🎤 Dinliyorum...")
            metin = mik.dinle()
            print(f"   STT: {metin}")
            bus.publish(Event(EventType.SPEECH_RECOGNIZED, {"text": metin}))
        except Exception as e:
            print(f"   STT hatası: {e}")
            metin = input("✏️  Metin gir: ")

    state.update(current_text=metin)

    # Adım 1: Kesici — basit sorgu mu?
    sonuc = kesici.isle(metin)
    if sonuc["yerel"]:
        print(f"⚡ Kesici: {sonuc['yanit']}")
        _konus(sonuc["yanit"])
        return sonuc["yanit"]

    # Adım 2: Mahkeme + smolagents + BrowserUse
    from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
    from config.config import config
    from agentik_dongu import gorev_tipini_belirle, GorevTipi

    m = HakikatMahkemesi(llm=LLMClient(config.LITELLM_URL, config.LITELLM_KEY))
    karar = m.yargila(claim=f"GOREV: {metin}", mode="task")
    print(f"⚖️  Mahkeme: {karar.verdict.value}")

    if karar.verdict.value == "REJECTED":
        _konus("Bu görevi yapamıyorum.")
        return "REJECTED"

    tip = gorev_tipini_belirle(metin)
    print(f"🔀 Rota: {tip.value}")

    # İcra
    if tip == GorevTipi.WEB:
        from mudahale.browser_use_bridge import get_browser_use
        bw = get_browser_use()
        sonuc_metni = bw.calistir(metin)
        bus.publish(Event(EventType.BROWSER_COMPLETED, {"result": str(sonuc_metni)[:200]}))
    else:
        from karar.smolagents_bridge import get_smol
        from mudahale.web_tools import web_fetch, web_extract_title
        sm = get_smol(tools=[web_fetch, web_extract_title])
        sonuc_metni = sm.calistir(metin)

    if isinstance(sonuc_metni, dict):
        sonuc_metni = sonuc_metni.get("message", str(sonuc_metni))
    sonuc_metni = str(sonuc_metni or "Tamamlandı")[:500]

    print(f"✅ Sonuç: {sonuc_metni[:200]}")

    # Adım 3: Sesli yanıt
    _konus(sonuc_metni[:300])
    memory.store(f"[zincir-ses] {metin[:100]} → {sonuc_metni[:100]}", scope="semantic")

    return sonuc_metni


# ═══════════════════════════════════════════════════════════
# ZİNCİR 2: GÖRÜNTÜ → ANALİZ → SES
# ═══════════════════════════════════════════════════════════

def zincir_goru():
    """
    Ekran görüntüsü → Qwen-VL(INT4) → smolagents → TTS → 🔊
    """
    import subprocess
    import tempfile

    # Adım 1: Ekran görüntüsü al
    print("📸 Ekran görüntüsü alınıyor...")
    img_path = Path(tempfile.gettempdir()) / "dv_screenshot.png"
    subprocess.run(["import", "-window", "root", str(img_path)],
                   capture_output=True, timeout=5)
    # fallback: scrot veya xdg
    if not img_path.exists():
        subprocess.run(["scrot", str(img_path)], capture_output=True, timeout=5)
    if not img_path.exists():
        subprocess.run(["gnome-screenshot", "-f", str(img_path)],
                       capture_output=True, timeout=5)

    if not img_path.exists():
        print("❌ Ekran görüntüsü alınamadı. PIL ile deneniyor...")
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(img_path)
        except Exception:
            pass

    if not img_path.exists():
        msg = "Ekran görüntüsü alınamadı."
        _konus(msg)
        return msg

    print(f"   Kaydedildi: {img_path}")
    bus.publish(Event(EventType.VISION_IMAGE_CAPTURED, {"path": str(img_path)}))

    # Adım 2: Qwen-VL analizi
    print("👁️ Qwen-VL analiz ediyor...")
    from mudahale.qwen_bridge import get_qwen
    qw = get_qwen()
    sonuc = qw.calistir("Bu ekran görüntüsünde ne var? Detaylı açıkla.", str(img_path))

    if sonuc.get("status") == "error":
        # Model yoksa smolagents'a sor
        from karar.smolagents_bridge import get_smol
        sm = get_smol()
        sonuc_metni = sm.calistir("Ekran görüntüsü alındı ama görü analizi yapılamadı. Ne yapmak istersin?")
        if isinstance(sonuc_metni, dict):
            sonuc_metni = sonuc_metni.get("message", str(sonuc_metni))
    else:
        sonuc_metni = sonuc.get("message", "Analiz tamamlandı")
        bus.publish(Event(EventType.VISION_ANALYSIS_COMPLETED,
                          {"description": str(sonuc_metni)[:200]}))

    sonuc_metni = str(sonuc_metni)[:500]
    print(f"✅ Analiz: {sonuc_metni[:200]}")

    # Adım 3: Sesli yanıt
    _konus(sonuc_metni[:300])
    memory.store(f"[zincir-goru] → {sonuc_metni[:100]}", scope="semantic")

    return sonuc_metni


# ═══════════════════════════════════════════════════════════
# ZİNCİR 3: KOD → YAZ → ÇALIŞTIR → SES
# ═══════════════════════════════════════════════════════════

def zincir_kod(gorev: str):
    """
    STT/Kesici → Mahkeme → smolagents(code) → TTS → 🔊
    """
    from altyapi.kesici import kesici
    from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
    from config.config import config

    print(f"🛠️ Kod görevi: {gorev}")

    # Kesici
    sonuc = kesici.isle(gorev)
    if sonuc["yerel"]:
        _konus(sonuc["yanit"])
        return sonuc["yanit"]

    # Mahkeme
    m = HakikatMahkemesi(llm=LLMClient(config.LITELLM_URL, config.LITELLM_KEY))
    karar = m.yargila(claim=f"GOREV: {gorev}", mode="task")
    print(f"⚖️  Mahkeme: {karar.verdict.value}")

    if karar.verdict.value == "REJECTED":
        _konus("Bu kodu yazmam güvenli değil.")
        return "REJECTED"

    # smolagents CodeAgent
    from karar.smolagents_bridge import get_smol
    sm = get_smol()
    sonuc_metni = sm.calistir(gorev)

    if isinstance(sonuc_metni, dict):
        sonuc_metni = sonuc_metni.get("message", str(sonuc_metni))
    sonuc_metni = str(sonuc_metni or "Kod yazıldı ve çalıştırıldı")[:500]

    print(f"✅ Sonuç: {sonuc_metni[:200]}")

    bus.publish(Event(EventType.TOOL_COMPLETED, {"tool": "smolagents", "result": sonuc_metni[:100]}))

    # Sesli yanıt
    _konus(sonuc_metni[:300])
    memory.store(f"[zincir-kod] {gorev[:100]} → {sonuc_metni[:100]}", scope="semantic")

    return sonuc_metni


# ═══════════════════════════════════════════════════════════
# ORTAK: SESLİ ÇIKIŞ
# ═══════════════════════════════════════════════════════════

def _konus(metin: str):
    """Metni seslendir. F5-TTS gerçek sentez → espeak fallback."""
    if not metin:
        return

    # F5-TTS gerçek ses sentezi dene
    try:
        from altyapi.vram_manager import vram
        import torch

        def _f5_sentez():
            from f5_tts.api import F5TTS
            return F5TTS(model="F5TTS_v1_Base")

        with vram.acquire("f5tts", _f5_sentez) as f5:
            import tempfile, os
            tmp = os.path.join(tempfile.gettempdir(), "dv_tts_out.wav")
            f5.infer(
                ref_file=None,  # zero-shot, ref ses yok
                ref_text="",
                gen_text=metin[:500],
                file_wave=tmp,
                nfe_step=16,
            )
            # Oynat
            try:
                import soundfile as sf
                import sounddevice as sd
                wav, sr = sf.read(tmp)
                sd.play(wav, sr)
                sd.wait()
            except Exception:
                pass
            print(f"🔊 F5-TTS: {metin[:80]}...")
            bus.publish(Event(EventType.SPEECH_SYNTHESIS_COMPLETED, {"text": metin[:100]}))
            return
    except Exception as e:
        print(f"  F5-TTS hatası (espeak'e düşüyor): {str(e)[:100]}")

    # espeak fallback
    try:
        import subprocess
        subprocess.run(["espeak-ng", "-v", "tr", metin[:500]],
                       timeout=30, capture_output=True)
        print(f"🔊 espeak: {metin[:80]}...")
        bus.publish(Event(EventType.SPEECH_SYNTHESIS_COMPLETED, {"text": metin[:100]}))
    except Exception:
        print(f"🔇 Seslendirme başarısız: {metin[:100]}")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python zincir.py [ses|goru|kod] [metin]")
        print("  python zincir.py ses 'bugün haberlerde ne var'")
        print("  python zincir.py goru")
        print("  python zincir.py kod 'bana web scraper yaz'")
        sys.exit(1)

    komut = sys.argv[1]
    metin = sys.argv[2] if len(sys.argv) > 2 else None

    vram.evict_all()

    if komut == "ses":
        zincir_ses(metin)
    elif komut == "goru":
        zincir_goru()
    elif komut == "kod":
        zincir_kod(metin or input("Görev: "))
    else:
        print(f"Bilinmeyen komut: {komut}")

    vram.evict_all()
