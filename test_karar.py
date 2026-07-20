"""Katman 3 entegrasyon testi."""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')

print("=" * 50)
print("KATMAN 3 - BEYIN TESTI")
print("=" * 50)

# 1. Mahkeme Motoru
print("\n1. Hakikat Mahkemesi")
from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
print("   Motor yüklendi: OK")
# LLMClient testi (LiteLLM'e bağlanır)
try:
    client = LLMClient()
    print(f"   LLMClient: {client.base_url}")
except Exception as e:
    print(f"   LLMClient: HATA - {e}")

# 2. Harness (Kendini Onarma)
print("\n2. Harness Motoru")
from karar.harness import get_harness
h = get_harness()
print(f"   Strateji sayısı: {len(h.stratejiler)}")
print(f"   Max deneme: {h.max_deneme}")

# Basit test: hata vermeyen fonksiyon
def basit_fonksiyon(x, y):
    return x + y

sonuc = h.calistir(basit_fonksiyon, 2, 3)
print(f"   Basit test (2+3): {sonuc}")

# Hatalı fonksiyon testi
def hata_veren():
    raise ValueError("Test hatasi")

sonuc2 = h.calistir(hata_veren)
print(f"   Hata testi sonucu: {sonuc2} (None beklenir)")

# 3. smolagents
print("\n3. smolagents")
from karar.smolagents_bridge import get_smol
s = get_smol()
print(f"   Agent hazır: {s.hazir_mi()}")

print("\n" + "=" * 50)
print("KATMAN 3 ÖZET:")
print(f"  Mahkeme    : ✅ (motor yüklendi)")
print(f"  Harness    : ✅ ({len(h.stratejiler)} strateji, max {h.max_deneme} deneme)")
print(f"  smolagents : {'✅' if s.hazir_mi() else '⚠️'} (agent {'hazır' if s.hazir_mi() else 'başlatılamadı'})")
print("=" * 50)
