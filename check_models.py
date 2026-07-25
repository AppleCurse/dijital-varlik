"""Check available models on 9router."""
import requests, json
from config.config import config

print("=== 9ROUTER MODELS ===")
print(f"URL: {config.LITELLM_URL}")
try:
    r = requests.get(f"{config.LITELLM_URL}/models", timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    models = data.get("data", [])
    print(f"Models: {len(models)}")
    for m in models[:10]:
        print(f"  - {m.get('id', m)}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== TEST CHAT (9router) ===")
try:
    r = requests.post(f"{config.LITELLM_URL}/chat/completions",
        json={
            "model": config.MAHKEME_MODEL,
            "messages": [{"role": "user", "content": "Say 'hello' in one word"}],
            "max_tokens": 10
        },
        headers={"Authorization": f"Bearer {config.LITELLM_KEY}"},
        timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Response: {r.json()['choices'][0]['message']['content']}")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
