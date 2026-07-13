"""
GERÇEK MAHKEME TESTİ
LiteLLM:4000 üzerinden deepseek-v4-pro ile 4 rol API çağrısı.
Savcı → Savunma → Şüpheci → Hakim zinciri.
"""
import sys, json, time
sys.path.insert(0, '/home/administrator/dijital-varlik')

from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
from config.config import config

print("=" * 60)
print("HAKİKAT MAHKEMESİ — CANLI TEST")
print("=" * 60)
print(f"Model: deepseek-v4-pro")
print(f"Endpoint: {config.LITELLM_URL}")

# LLMClient'i deepseek modeliyle başlat
llm = LLMClient(
    base_url=config.LITELLM_URL,
    api_key=config.LITELLM_KEY
)

# Önce basit bir bağlantı testi
print("\n📡 Bağlantı testi...")
test_result = llm.call(
    system_prompt="Sen bir test asistanisin. Sadece JSON formatinda yanit ver.",
    user_message='{"soru": "2+2 kactir?"} cevabini {"cevap": sayi} formatinda ver.',
    model="deepseek-v4-pro",
    temperature=0.1,
    max_tokens=100
)
print(f"   Yanıt: {json.dumps(test_result, ensure_ascii=False, indent=2)[:200]}")

if "error" in test_result:
    print("❌ Bağlantı başarısız. Test sonlandı.")
    sys.exit(1)

print("✅ Bağlantı başarılı!\n")

# Gerçek Mahkeme testi
print("=" * 60)
print("MAHKEME BAŞLIYOR")
print("=" * 60)

mahkeme = HakikatMahkemesi(llm)

# Test edilecek önerme
claim = "WSL üzerinde çalışan dijital-varlik projesi, Claude Code ile entegre bir siber organizma olarak başarıyla çalışmaktadır."
context = """
Proje durumu:
- LiteLLM proxy çalışıyor (port 4000)
- Open WebUI çalışıyor (port 3000)
- Browserless çalışıyor (port 3001)
- Hakikat Mahkemesi motoru hazır
- Mem0 bilgi grafiği çalışıyor
- Harness kendini onaran döngü çalışıyor
- smolagents yüklendi
- EC2'ya doğrudan bağlantı yok (9router'a erişilemiyor)
"""

start_time = time.time()
result = mahkeme.yargila(claim, context)
duration = time.time() - start_time

print("\n" + "=" * 60)
print("MAHKEME SONUCU")
print("=" * 60)
print(f"Karar:     {result.verdict.value}")
print(f"Güven:     {result.confidence:.1%}")
print(f"Süre:      {duration:.1f}s")
print(f"Tartışma:  {len(result.debate_log)} tur")

if result.verdict.value == "APPROVED":
    print(f"\n✅ ONAYLANAN ÇIKTI:\n{result.approved_output}")
else:
    print(f"\n❌ RED GEREKÇESİ:\n{result.judge_reasoning[:500]}")

if result.minority_report:
    print(f"\n📝 AZINLIK GÖRÜŞÜ:\n{result.minority_report[:300]}")

# Tartışma kaydını kaydet
with open("mahkeme_test_log.json", "w", encoding="utf-8") as f:
    json.dump({
        "claim": claim,
        "verdict": result.verdict.value,
        "confidence": result.confidence,
        "duration": duration,
        "debate": [{"role": t.role, "content": t.content[:300]} for t in result.debate_log],
        "approved_output": result.approved_output,
        "reasoning": result.judge_reasoning[:500]
    }, f, ensure_ascii=False, indent=2)

print(f"\n📄 Kayıt: mahkeme_test_log.json")
print("=" * 60)
