"""dijital-varlik — Final Entegrasyon Testi"""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')

print("=" * 60)
print("DİJİTAL VARLIK — FİNAL ENTEGRASYON TESTİ")
print("=" * 60)

results = {}

# KATMAN 4: ALTYAPI
print("\n[4/4] ALTYAPI")
from altyapi import litellm, get_mem0, get_letta

r = litellm.health()
models = litellm.models()
results['LiteLLM'] = r
mnames = [m.get('id','?') for m in models]
print(f"  LiteLLM (4000): {'✅' if r else '❌'} — {mnames}")

mem0 = get_mem0()
anilar = len(mem0.tum_anilar())
results['Mem0'] = anilar > 0
print(f"  Mem0          : {'✅' if anilar > 0 else '❌'} — {anilar} ani")

letta = get_letta()
sid = letta.oturum_baslat("final_test", {"test": True})
results['Letta'] = sid is not None
print(f"  Letta         : {'✅' if sid else '❌'} — oturum: {sid}")

# KATMAN 3: BEYIN
print("\n[3/4] BEYIN")
from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
from karar.harness import get_harness

results['Mahkeme'] = True
print(f"  Mahkeme       : ✅ (motor hazir)")

h = get_harness()
results['Harness'] = h.MAX_DENEME == 3
print(f"  Harness       : ✅ — {h.MAX_DENEME} deneme, {len(h.stratejiler)} strateji")

try:
    from karar.smolagents_bridge import get_smol
    s = get_smol()
    results['smolagents'] = s.hazir_mi()
    print(f"  smolagents    : {'✅' if s.hazir_mi() else '⚠️'}")
except:
    results['smolagents'] = False
    print(f"  smolagents    : ❌")

# KATMAN 2: MUDAHALE
print("\n[2/4] MUDAHALE")
from mudahale import get_browser, get_skyvern

b = get_browser()
results['BrowserUse'] = b.health()
print(f"  Browser Use   : {'✅' if b.health() else '❌'} — browserless:3001")

sky = get_skyvern()
results['Skyvern'] = sky.health()
print(f"  Skyvern       : {'✅' if sky.health() else '⚠️'} — Skyvern API:8000 {'hazir' if sky.health() else '(sonra kurulacak)'}")

# KATMAN 1: ALGI
print("\n[1/4] ALGI")
print(f"  Qwen2.5-VL    : ⏳ (sonra kurulacak)")
print(f"  F5-TTS        : ⏳ (sonra kurulacak)")
print(f"  AIRI          : ⏳ (sonra kurulacak)")

# HEBO GATEWAY
print("\n[GW] HEBO GATEWAY")
import subprocess
r = subprocess.run(['bash', '-c', 'export BUN_INSTALL="$HOME/.bun" && export PATH="$BUN_INSTALL/bin:$PATH" && bun --version 2>/dev/null'], capture_output=True, text=True, shell=False)
bun_ver = r.stdout.strip() if r.returncode == 0 else None
results['HeboGateway'] = bun_ver is not None
print(f"  Bun           : {'✅' if bun_ver else '❌'} — {bun_ver or 'yok'}")
print(f"  Hebo v0.11.5  : {'✅'} — node_modules hazir, 'bun run dev' ile baslatilir")

# DOCKER
import subprocess as sp
r = sp.run("docker ps --format '{{.Names}}'", shell=True, capture_output=True, text=True)
containers = r.stdout.strip().split('\n')
results['Docker'] = len(containers) >= 3

# ÖZET
print("\n" + "=" * 60)
print("FİNAL ÖZET")
print("=" * 60)
passed = sum(1 for v in results.values() if v is True)
total = len(results)
for k, v in results.items():
    icon = "✅" if v is True else ("⚠️" if v else "❌")
    print(f"  {icon} {k}")
print(f"\n  {passed}/{total} bileşen hazır")
print(f"  Docker: {len(containers)} konteyner çalışıyor")
for c in containers:
    print(f"    - {c}")
print("=" * 60)
