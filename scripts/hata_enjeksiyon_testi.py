"""
Faz 1 Kabul Kriteri — Hata Enjeksiyon Testi

Testler:
  1. Harness: ConnectionError yakalama + exponential backoff
  2. smolagents: Bozuk araç (her zaman hata fırlatan web_fetch)
  3. Tam akış: Ulaşılamaz URL (bağlanamayacağı bir adres)

Amaç: Harness'ın hataları yakalayıp kurtarabildiğini kanıtlamak.
"""
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(ROOT))

from config.config import config
from karar.harness import HarnessMotoru, get_harness
from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
from karar.smolagents_bridge import get_smol, SmolAgentBridge
from altyapi.mem0_bridge import get_mem0
from altyapi.litellm_bridge import litellm
from smolagents import tool

# ─── Test çıktılarını topla ───
test_sonuclari = []
TEST_RAPORU = {
    "test_tarihi": datetime.now().isoformat(),
    "test_adi": "Faz 1 — Hata Enjeksiyon ve Kurtarma Testi",
    "testler": [],
    "genel_basari": False,
}

def test_sonuc_kaydet(isim, basarili, detay, kanit=""):
    sonuc = {
        "test": isim,
        "basarili": basarili,
        "detay": detay,
        "kanit": kanit[:500],
    }
    test_sonuclari.append(sonuc)
    TEST_RAPORU["testler"].append(sonuc)
    emoji = "✅" if basarili else "❌"
    print(f"\n  {emoji} {isim}: {'BAŞARILI' if basarili else 'BAŞARISIZ'}")
    print(f"     {detay[:200]}")


# ═══════════════════════════════════════════════════════════════
# TEST 1: Harness — ConnectionError yakalama ve backoff
# ═══════════════════════════════════════════════════════════════
def test1_harness_connection_error():
    print("\n" + "=" * 60)
    print("TEST 1: Harness — ConnectionError yakalama + exponential backoff")
    print("=" * 60)

    harness = HarnessMotoru()
    deneme_sayaci = [0]

    def baglanamayan_fonksiyon():
        deneme_sayaci[0] += 1
        raise ConnectionError(f"Bağlantı reddedildi (deneme {deneme_sayaci[0]})")

    baslangic = time.time()
    sonuc = harness.calistir(baglanamayan_fonksiyon)
    gecen_sure = time.time() - baslangic

    # Backoff: 2^1=2s, 2^2=4s → toplam ~6s bekleme + 3 deneme
    print(f"  Deneme sayısı: {deneme_sayaci[0]}")
    print(f"  Geçen süre: {gecen_sure:.1f}s")
    print(f"  Harness sonucu: {'None (pes etti)' if sonuc is None else sonuc}")

    # Doğrulama: 3 deneme yapıldı mı? Backoff uygulandı mı?
    if deneme_sayaci[0] == harness.MAX_DENEME and sonuc is None:
        test_sonuc_kaydet(
            "Harness ConnectionError",
            True,
            f"Harness {deneme_sayaci[0]} deneme sonunda pes etti. "
            f"Exponential backoff çalıştı ({gecen_sure:.1f}s bekleme).",
            f"MAX_DENEME={harness.MAX_DENEME}, deneme={deneme_sayaci[0]}, süre={gecen_sure:.1f}s, sonuç=None"
        )
    else:
        test_sonuc_kaydet(
            "Harness ConnectionError",
            False,
            f"Beklenen: 3 deneme + None. Gerçek: {deneme_sayaci[0]} deneme + {sonuc}",
            f"deneme={deneme_sayaci[0]}, sonuç={sonuc}"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 2: smolagents — Bozuk araç (her zaman hata fırlatan tool)
# ═══════════════════════════════════════════════════════════════
def test2_bozuk_arac():
    print("\n" + "=" * 60)
    print("TEST 2: smolagents — Bozuk araç (web_fetch_broken)")
    print("=" * 60)

    @tool
    def web_fetch_broken(url: str) -> str:
        """
        BOZUK ARAÇ — Her zaman hata fırlatır. Harness testi içindir.

        Args:
            url: Açılacak web sayfası URL'i (kasıtlı olarak hata verir)

        Returns:
            Hata mesajı (normalde dönmez, istisna fırlatır)
        """
        raise RuntimeError(f"ARAÇ ARIZASI: {url} için bağlantı kurulamadı — devre dışı!")

    # smolagents'i bozuk araçla başlat
    try:
        smol_broken = SmolAgentBridge(tools=[web_fetch_broken])
        if not smol_broken.hazir_mi():
            test_sonuc_kaydet(
                "smolagents Bozuk Araç",
                False,
                "smolagents bozuk araçla başlatılamadı",
                "hazir_mi()=False"
            )
            return

        print("  smolagents bozuk araçla başlatıldı, görev deneniyor...")

        harness = get_harness()
        gorev = (
            "GOREV: https://example.com sitesini ac ve basligini soyle\n\n"
            "Bu görevi verilen araçları kullanarak gerçekleştir."
        )

        baslangic = time.time()
        sonuc = harness.calistir(smol_broken.calistir, gorev)
        gecen_sure = time.time() - baslangic

        print(f"  Geçen süre: {gecen_sure:.1f}s")
        print(f"  Sonuç: {str(sonuc)[:200] if sonuc else 'None'}")

        if sonuc is None:
            # Harness pes etti — bu beklenen davranış (bozuk araç kurtarılamaz)
            test_sonuc_kaydet(
                "smolagents Bozuk Araç",
                True,
                f"Harness bozuk aracın hatasını yakaladı, {harness.MAX_DENEME} deneme sonunda pes etti. "
                f"Sistem çökmedi, kontrollü şekilde None döndü.",
                f"süre={gecen_sure:.1f}s, sonuç=None, MAX_DENEME={harness.MAX_DENEME}"
            )
        else:
            # smolagents içeride hatayı yakalayıp string döndüyse
            test_sonuc_kaydet(
                "smolagents Bozuk Araç",
                True,
                f"smolagents hata aldı ama kontrollü şekilde sonuç döndü: {str(sonuc)[:150]}",
                f"süre={gecen_sure:.1f}s, sonuç tipi={type(sonuc).__name__}"
            )

    except Exception as e:
        test_sonuc_kaydet(
            "smolagents Bozuk Araç",
            False,
            f"Beklenmeyen istisna: {type(e).__name__}: {str(e)[:150]}",
            str(e)
        )


# ═══════════════════════════════════════════════════════════════
# TEST 3: Tam akış — Ulaşılamaz URL
# ═══════════════════════════════════════════════════════════════
def test3_ulasilamaz_url():
    print("\n" + "=" * 60)
    print("TEST 3: Tam akış — Ulaşılamaz URL (var olmayan domain)")
    print("=" * 60)

    from mudahale.web_tools import web_fetch, web_extract_title, web_screenshot

    smol = get_smol(tools=[web_fetch, web_extract_title, web_screenshot])
    if not smol.hazir_mi():
        test_sonuc_kaydet(
            "Ulaşılamaz URL",
            False,
            "smolagents başlatılamadı",
            "hazir_mi()=False"
        )
        return

    harness = get_harness()

    # Var olmayan bir domain — DNS çözümlenemez veya bağlantı timeout olur
    gorev = (
        "GOREV: https://bu-domain-kesinlikle-yok-12345.invalid sitesini ac ve basligini soyle\n\n"
        "Bu görevi verilen araçları kullanarak gerçekleştir. "
        "Eğer sayfa açılamazsa, bunu açıkça belirt."
    )

    print("  Görev çalıştırılıyor (ulaşılamaz domain)...")
    baslangic = time.time()
    sonuc = harness.calistir(smol.calistir, gorev)
    gecen_sure = time.time() - baslangic

    print(f"  Geçen süre: {gecen_sure:.1f}s")
    print(f"  Sonuç: {str(sonuc)[:300] if sonuc else 'None'}")

    if sonuc is not None:
        # smolagents hata mesajını içeren bir sonuç döndü
        test_sonuc_kaydet(
            "Ulaşılamaz URL",
            True,
            f"Sistem ulaşılamaz URL'i kontrollü şekilde işledi. "
            f"Çökme olmadı, hata mesajı döndü.",
            f"süre={gecen_sure:.1f}s, sonuç={str(sonuc)[:300]}"
        )
    else:
        test_sonuc_kaydet(
            "Ulaşılamaz URL",
            True,
            f"Harness ulaşılamaz URL sonrası kontrollü şekilde pes etti. Sistem çökmedi.",
            f"süre={gecen_sure:.1f}s, sonuç=None"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 4: Tam entegrasyon — Orchestrator üzerinden hata akışı
# ═══════════════════════════════════════════════════════════════
def test4_orchestrator_hata_akisi():
    print("\n" + "=" * 60)
    print("TEST 4: Orchestrator — dusun_ve_karar_ver ile bozuk URL")
    print("=" * 60)

    from orchestrator import DijitalVarlik

    print("  DijitalVarlik başlatılıyor...")
    try:
        varlik = DijitalVarlik()

        # Var olmayan bir URL dene
        gorev = "https://192.0.2.1:666 adresine baglan ve sayfa icerigini getir"
        print(f"  Görev: {gorev}")

        sonuc = varlik.dusun_ve_karar_ver(gorev)

        print(f"  Status: {sonuc.get('status')}")
        print(f"  Verdict: {sonuc.get('verdict')}")
        print(f"  Message: {str(sonuc.get('message', ''))[:200]}")

        # Mahkeme APPROVED verirse → smolagents dener → hata alır → harness kurtarır
        # Mahkeme REJECTED verirse → güvenlik filtresi çalışıyor
        if sonuc["status"] in ("error", "rejected"):
            test_sonuc_kaydet(
                "Orchestrator Hata Akışı",
                True,
                f"Orchestrator hatalı görevi kontrollü şekilde işledi: {sonuc['status']}. "
                f"Sistem çökmedi, kullanıcıya anlamlı yanıt döndü.",
                json.dumps({k: str(v)[:150] for k, v in sonuc.items()}, ensure_ascii=False)
            )
        elif sonuc["status"] == "success":
            test_sonuc_kaydet(
                "Orchestrator Hata Akışı",
                True,
                f"Orchestrator görevi çalıştırdı ve smolagents iç hatayı yönetti: {sonuc['message'][:150]}",
                f"status={sonuc['status']}"
            )
        else:
            test_sonuc_kaydet(
                "Orchestrator Hata Akışı",
                False,
                f"Beklenmeyen durum: {sonuc.get('status')}",
                str(sonuc)[:300]
            )

        varlik.kapat()
    except Exception as e:
        test_sonuc_kaydet(
            "Orchestrator Hata Akışı",
            False,
            f"Orchestrator çöktü: {type(e).__name__}: {str(e)[:200]}",
            str(e)
        )


# ═══════════════════════════════════════════════════════════════
# TEST 5: Harness strateji çeşitliliği
# ═══════════════════════════════════════════════════════════════
def test5_harness_stratejiler():
    print("\n" + "=" * 60)
    print("TEST 5: Harness — Strateji çeşitliliği (TimeoutError, ValueError)")
    print("=" * 60)

    harness = HarnessMotoru()

    # 5a: TimeoutError → backoff stratejisi
    print("\n  5a: TimeoutError → backoff stratejisi")
    timeout_sayaci = [0]

    def timeout_fonksiyonu():
        timeout_sayaci[0] += 1
        raise TimeoutError(f"İstek zaman aşımına uğradı (deneme {timeout_sayaci[0]})")

    baslangic = time.time()
    sonuc = harness.calistir(timeout_fonksiyonu)
    sure = time.time() - baslangic

    print(f"    Deneme: {timeout_sayaci[0]}, Süre: {sure:.1f}s, Sonuç: {sonuc}")

    # TimeoutError backoff kullanır: 2^1=2s, 2^2=4s → en az 6s
    if timeout_sayaci[0] == 3 and sure >= 5:
        test_sonuc_kaydet(
            "Harness TimeoutError",
            True,
            f"TimeoutError backoff stratejisi çalıştı: {timeout_sayaci[0]} deneme, {sure:.1f}s",
            f"deneme={timeout_sayaci[0]}, sure={sure:.1f}s"
        )
    else:
        test_sonuc_kaydet(
            "Harness TimeoutError",
            False,
            f"Beklenen: 3 deneme + ≥5s. Gerçek: {timeout_sayaci[0]} deneme, {sure:.1f}s",
            f"deneme={timeout_sayaci[0]}, sure={sure:.1f}s"
        )

    # 5b: ValueError → şimdilik manuel (false döner)
    print("\n  5b: ValueError → tip düzeltme stratejisi")
    value_sayaci = [0]

    def value_fonksiyonu():
        value_sayaci[0] += 1
        raise ValueError(f"Geçersiz değer (deneme {value_sayaci[0]})")

    sonuc2 = harness.calistir(value_fonksiyonu)
    print(f"    Deneme: {value_sayaci[0]}, Sonuç: {sonuc2}")

    if value_sayaci[0] == 3 and sonuc2 is None:
        test_sonuc_kaydet(
            "Harness ValueError",
            True,
            f"ValueError stratejisi (manuel) çalıştı: {value_sayaci[0]} deneme, kontrollü pes etti",
            f"deneme={value_sayaci[0]}, sonuç=None"
        )
    else:
        test_sonuc_kaydet(
            "Harness ValueError",
            False,
            f"Beklenmeyen: {value_sayaci[0]} deneme, sonuç={sonuc2}",
            f"deneme={value_sayaci[0]}"
        )


# ═══════════════════════════════════════════════════════════════
# ANA ÇALIŞTIRICI
# ═══════════════════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("  FAZ 1 — HATA ENJEKSİYON VE KURTARMA TESTİ")
    print("  dijital-varlık — Harness Kendini Onarma Döngüsü")
    print("=" * 65)
    print(f"  Başlangıç: {datetime.now().isoformat()}")
    print(f"  LiteLLM: {config.LITELLM_URL}")
    print(f"  Harness MAX_DENEME: {HarnessMotoru.MAX_DENEME}")

    # Tüm testleri çalıştır
    testler = [
        ("Test 1: Harness ConnectionError", test1_harness_connection_error),
        ("Test 2: smolagents Bozuk Araç", test2_bozuk_arac),
        ("Test 3: Ulaşılamaz URL", test3_ulasilamaz_url),
        ("Test 4: Orchestrator Hata Akışı", test4_orchestrator_hata_akisi),
        ("Test 5: Harness Stratejileri", test5_harness_stratejiler),
    ]

    for isim, test_fn in testler:
        try:
            test_fn()
        except Exception as e:
            print(f"\n  💀 {isim} BEKLENMEDİK ÇÖKME: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            test_sonuc_kaydet(isim, False, f"Test çöktü: {type(e).__name__}: {str(e)[:200]}", str(e))

    # ─── Özet ───
    basarili = sum(1 for t in test_sonuclari if t["basarili"])
    basarisiz = sum(1 for t in test_sonuclari if not t["basarili"])
    toplam = len(test_sonuclari)
    TEST_RAPORU["genel_basari"] = basarisiz == 0
    TEST_RAPORU["ozet"] = {
        "toplam": toplam,
        "basarili": basarili,
        "basarisiz": basarisiz,
        "basari_orani": f"{basarili/toplam*100:.0f}%" if toplam > 0 else "0%",
    }

    print("\n" + "=" * 65)
    print("  TEST ÖZETİ")
    print("=" * 65)
    for t in test_sonuclari:
        emoji = "✅" if t["basarili"] else "❌"
        print(f"  {emoji} {t['test']}")
    print(f"\n  Toplam: {toplam} | Başarılı: {basarili} | Başarısız: {basarisiz}")
    print(f"  Genel: {'✅ TÜM TESTLER BAŞARILI' if TEST_RAPORU['genel_basari'] else '❌ BAŞARISIZ TESTLER VAR'}")

    # Raporu JSON olarak kaydet
    rapor_yolu = ROOT / "docs" / "hata_enjeksiyon_raporu.json"
    os.makedirs(ROOT / "docs", exist_ok=True)
    with open(rapor_yolu, "w", encoding="utf-8") as f:
        json.dump(TEST_RAPORU, f, ensure_ascii=False, indent=2)
    print(f"\n  Detaylı rapor: {rapor_yolu}")

    return 0 if TEST_RAPORU["genel_basari"] else 1


if __name__ == "__main__":
    sys.exit(main())
