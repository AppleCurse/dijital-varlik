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
# ZİNCİR 4: YÜZ TANIMA → ANALİZ → SES
# ═══════════════════════════════════════════════════════════

def zincir_yuz(image_path: str = None, action: str = "analyze", db_path: str = None):
    """
    Yüz tanıma/analiz zinciri.

    Kullanım:
        python zincir.py yuz analyze /path/to/foto.jpg
        python zincir.py yuz verify /path/1.jpg /path/2.jpg
        python zincir.py yuz find /path/arama.jpg /path/veritabani/
    """
    from mudahale.deepface_bridge import get_deepface

    df = get_deepface()
    if not df.hazir_mi():
        _konus("Yüz tanıma motoru hazır değil.")
        return {"status": "error"}

    if action == "analyze":
        print(f"👤 Yüz analizi: {image_path}")
        result = df.analyze(image_path)
        if result["status"] == "ok":
            data = result["data"]
            info_parts = []
            if "age" in data: info_parts.append(f"Yaş: {data['age']}")
            if "gender" in data: info_parts.append(f"Cinsiyet: {data.get('dominant_gender', '?')}")
            if "emotion" in data: info_parts.append(f"Duygu: {data.get('dominant_emotion', '?')}")
            if "race" in data: info_parts.append(f"Irk: {data.get('dominant_race', '?')}")
            msg = ". ".join(info_parts)
        else:
            msg = f"Analiz başarısız: {result['message'][:100]}"

    elif action == "verify":
        img2 = db_path  # verify için ikinci arg db_path olarak geçer
        print(f"👤 Yüz doğrulama: {image_path} vs {img2}")
        result = df.verify(image_path, img2)
        if result["status"] == "ok":
            msg = "Aynı kişi." if result["verified"] else "Farklı kişiler."
            msg += f" (benzerlik: {result['distance']:.2f})"
        else:
            msg = f"Doğrulama başarısız: {result['message'][:100]}"

    elif action == "find":
        print(f"🔍 Yüz arama: {image_path} → {db_path}")
        result = df.find(image_path, db_path)
        if result["status"] == "ok":
            if result["count"] > 0:
                msg = f"{result['count']} eşleşme bulundu. En yakın: {result['matches'][0]['identity']}"
            else:
                msg = "Eşleşme bulunamadı."
        else:
            msg = f"Arama başarısız: {result['message'][:100]}"

    else:
        msg = f"Bilinmeyen işlem: {action}"

    print(f"✅ {msg}")
    _konus(msg)
    memory.store(f"[zincir-yuz] {action} → {msg[:100]}", scope="semantic")
    return {"status": "ok", "message": msg}


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
    """Metni seslendir. XTTS → F5-TTS → espeak."""
    if not metin:
        return

    # 1. XTTS dene (hafif, hizli)
    try:
        from mudahale.xtts_bridge import get_xtts
        xtts = get_xtts()
        if xtts.hazir_mi():
            r = xtts.konus(metin)
            if r["status"] == "ok":
                print(f"🔊 XTTS: {metin[:80]}...")
                try:
                    import soundfile as sf, sounddevice as sd
                    wav, sr = sf.read(r["file"])
                    sd.play(wav, sr); sd.wait()
                except: pass
                bus.publish(Event(EventType.SPEECH_SYNTHESIS_COMPLETED, {"text": metin[:100]}))
                return
    except Exception as e:
        print(f"  XTTS yok: {str(e)[:60]}")

    # 2. F5-TTS dene
    try:
        from altyapi.vram_manager import vram
        def _f5(): from f5_tts.api import F5TTS; return F5TTS(model="F5TTS_v1_Base")
        with vram.acquire("f5tts", _f5) as f5:
            import tempfile, os
            tmp = os.path.join(tempfile.gettempdir(), "dv_tts_out.wav")
            f5.infer(ref_file=None, ref_text="", gen_text=metin[:500], file_wave=tmp, nfe_step=16)
            try:
                import soundfile as sf, sounddevice as sd
                wav, sr = sf.read(tmp); sd.play(wav, sr); sd.wait()
            except: pass
            print(f"🔊 F5-TTS: {metin[:80]}...")
            bus.publish(Event(EventType.SPEECH_SYNTHESIS_COMPLETED, {"text": metin[:100]}))
            return
    except Exception as e:
        print(f"  F5-TTS yok: {str(e)[:60]}")

    # 3. espeak fallback
    try:
        import subprocess
        subprocess.run(["espeak-ng", "-v", "tr", metin[:500]], timeout=30, capture_output=True)
        print(f"🔊 espeak: {metin[:80]}...")
        bus.publish(Event(EventType.SPEECH_SYNTHESIS_COMPLETED, {"text": metin[:100]}))
    except Exception:
        print(f"🔇 Ses yok: {metin[:100]}")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python zincir.py [ses|goru|kod|yuz] [argumanlar]")
        print("  python zincir.py ses 'bugün haberlerde ne var'")
        print("  python zincir.py goru")
        print("  python zincir.py kod 'bana web scraper yaz'")
        print("  python zincir.py yuz analyze fotograflar/ben.jpg")
        print("  python zincir.py yuz verify foto1.jpg foto2.jpg")
        print("  python zincir.py yuz find arama.jpg veritabani/")
        sys.exit(1)

    komut = sys.argv[1]

    vram.evict_all()

    if komut == "ses":
        metin = sys.argv[2] if len(sys.argv) > 2 else None
        zincir_ses(metin)
    elif komut == "goru":
        zincir_goru()
    elif komut == "kod":
        metin = sys.argv[2] if len(sys.argv) > 2 else input("Görev: ")
        zincir_kod(metin)
    elif komut == "yuz":
        action = sys.argv[2] if len(sys.argv) > 2 else "analyze"
        img = sys.argv[3] if len(sys.argv) > 3 else None
        extra = sys.argv[4] if len(sys.argv) > 4 else None
        zincir_yuz(img, action, extra)
    else:
        print(f"Bilinmeyen komut: {komut}")

    vram.evict_all()
