"""Quick smoke test for Mem0 real integration."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from altyapi.mem0_bridge import Mem0Bridge

print("Mem0Bridge baslatiliyor...")
m = Mem0Bridge()
print(f"Hazir: {m.hazir_mi}")

if m.hazir_mi:
    print("\nTest kaydi yapiliyor...")
    m.kaydet("Test: example.com sayfasinin basligi Example Domain olarak bulundu.")

    print("Arama yapiliyor...")
    results = m.hatirla("example.com basligi nedir?")
    print(f"Sonuc sayisi: {len(results)}")
    for r in results:
        score = r.get("score", 0)
        memory = r.get("memory", "")[:150]
        print(f"  [{score:.3f}] {memory}")

    # Clean up test data
    m.sil_hepsini()
    print("\n✅ Mem0 smoke test basarili!")
else:
    print("❌ Mem0 baslatilamadi")
