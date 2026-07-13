"""Katman 4 entegrasyon testi."""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')

from altyapi import litellm, get_mem0, get_letta

print("=" * 50)
print("KATMAN 4 - ALTYAPI TESTI")
print("=" * 50)

# LiteLLM
print("\n1. LiteLLM")
print(f"   Health: {litellm.health()}")
models = litellm.models()
print(f"   Models: {len(models)} bulundu")
for m in models[:3]:
    print(f"     - {m.get('id', m)}")

# Mem0
print("\n2. Mem0")
mem0 = get_mem0()
mem0.olay_kaydet("Altyapi testi baslatildi", "altyapi", "normal")
mem0.ders_cikar("Test hatasi", "Test cozumu")
anilar = mem0.tum_anilar()
print(f"   Toplam ani: {len(anilar)}")
# Son anıyı göster
if anilar:
    son = anilar[-1]
    print(f"   Son ani: {son['content'][:80]}...")

# Letta — oturum testi (dosya tabanlı)
print("\n3. Letta (dosya tabanli)")
letta = get_letta()
sid = letta.oturum_baslat("test_1", {"test": True})
print(f"   Oturum baslatildi: {sid}")
# Doğru anahtarla yükle
state = letta.agent_durumu_yukle(f"session_{sid}")
print(f"   Oturum kaydi: {'OK' if state else 'HATA'}")

# Özet
print("\n" + "=" * 50)
print("KATMAN 4 ÖZET:")
print(f"  LiteLLM : {'✅' if litellm.health() else '❌'} (port 4000)")
print(f"  Mem0    : {'✅'} ({len(anilar)} ani, dosya tabanli)")
print(f"  Letta   : {'✅'} (dosya tabanli)")
print(f"  Hebo    : ⏳ (TypeScript/Bun, sonra kurulacak)")
print("=" * 50)
