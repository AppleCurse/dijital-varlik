"""Check available models on 9router and LiteLLM."""
import requests, json

print("=== 9ROUTER MODELS (port 20128) ===")
try:
    r = requests.get("http://localhost:20128/v1/models", timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    models = data.get("data", [])
    print(f"Models: {len(models)}")
    for m in models[:10]:
        print(f"  - {m.get('id', m)}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== LITELLM MODELS (port 4000) ===")
try:
    r = requests.get("http://localhost:4000/models",
                      headers={"Authorization": "Bearer omniroute"}, timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    models = data.get("data", [])
    print(f"Models: {len(models)}")
    for m in models[:10]:
        print(f"  - {m.get('id', m)}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== TEST CHAT (9router directly) ===")
try:
    r = requests.post("http://localhost:20128/v1/chat/completions",
        json={
            "model": "dijitalvarlik",
            "messages": [{"role": "user", "content": "Say 'hello' in one word"}],
            "max_tokens": 10
        },
        headers={"Authorization": "Bearer sk-58bbadde44171bff-6jq5bl-7378c3af"},
        timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")
