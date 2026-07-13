"""smolagents testi."""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')

print("1. Import testi...")
from smolagents import CodeAgent, LiteLLMModel
print("   Import OK")

print("2. Model bağlantısı...")
from config.config import config
model = LiteLLMModel(
    model_id=f"openai/{config.MAHKEME_MODEL}",
    api_base=config.LITELLM_URL,
    api_key=config.LITELLM_KEY,
)
print(f"   Model: {config.MAHKEME_MODEL}")

print("3. Agent başlatma...")
agent = CodeAgent(
    tools=[],
    model=model,
    add_base_tools=True,
)
print("   Agent OK")

print("4. Kod üretim testi...")
result = agent.run("What is 2 + 2? Just return the number.")
print(f"   Sonuç: {result}")

print("\nsmolagents ✅")
