"""
Gerçek Mahkeme Testi — LiteLLM:4000 üzerinden 9router ile 4 rol API çağrısı.
Savcı, Savunma, Şüpheci, Hakim sırayla gerçek LLM'e çağrı yapar.
"""
import sys
import json
import time
sys.path.insert(0, '/home/administrator/dijital-varlik')

from config.config import config
from karar.mahkeme_engine import HakikatMahkemesi, LLMClient

print("=" * 60)
print("HAKIKAT MAHKEMESI — GERÇEK API TESTİ")
print("=" * 60)
print(f"LiteLLM : {config.LITELLM_URL}")
print(f"Model   : {config.MAHKEME_MODEL}")
print(f"Fallback: {config.FALLBACK_MODEL}")
print()

# LiteLLM health check
import requests
try:
    resp = requests.get(
        f"{config.LITELLM_URL}/health",
        headers={"Authorization": f"Bearer {config.LITELLM_KEY}"},
        timeout=5
    )
    print(f"Health  : {'OK' if resp.status_code == 200 else 'FAIL'} ({resp.status_code})")
except Exception as e:
    print(f"Health  : FAIL ({e})")
    sys.exit(1)

# Model listesi
try:
    resp = requests.get(
        f"{config.LITELLM_URL}/models",
        headers={"Authorization": f"Bearer {config.LITELLM_KEY}"},
        timeout=5
    )
    models = resp.json().get("data", [])
    print(f"Models  : {[m.get('id') for m in models]}")
except Exception as e:
    print(f"Models  : FAIL ({e})")

print()
print("-" * 60)
print("BASLANGIC: 4 roller tartismasi")
print("-" * 60)

# Mahkeme motorunu başlat
llm_client = LLMClient(config.LITELLM_URL, config.LITELLM_KEY)
mahkeme = HakikatMahkemesi(llm_client)

test_claim = "Python, yapay zeka geliştirme için en uygun programlama dilidir."
test_context = "Bu bir sentetik testtir. Dijital Varlık projesinin Hakikat Mahkemesi bileşeni test ediliyor."

start = time.time()
result = mahkeme.yargila(test_claim, test_context)
elapsed = time.time() - start

print()
print("=" * 60)
print("TEST SONUCU")
print("=" * 60)
print(f"Verdict   : {result.verdict.value}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Reasoning : {result.judge_reasoning[:200]}...")
print(f"Süre      : {elapsed:.1f}s")
print(f"Log tur   : {len(result.debate_log)}")
for turn in result.debate_log:
    content_preview = turn.content[:100].replace('\n', ' ')
    print(f"  [{turn.role}] {content_preview}...")
print()

if result.verdict.value == "APPROVED":
    print(f"Onaylanan: {result.approved_output[:150]}...")
if result.minority_report:
    print(f"Azınlık  : {result.minority_report[:150]}...")

print()
print("TUM API CAGRI BASARILI" if len(result.debate_log) == 4 else "EKSIK CAGRI!")
