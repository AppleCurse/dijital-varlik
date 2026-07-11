"""Quick test: Check which models work."""
import requests, json

url = "http://localhost:4000/chat/completions"
headers = {"Authorization": "Bearer omniroute", "Content-Type": "application/json"}

for model in ["deepseek-v4-pro", "9router", "deepseek-v4-flash"]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "max_tokens": 20,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        status = resp.status_code
        if status == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            print(f"  {model}: ✅ OK → '{content}'")
        else:
            err = resp.json().get("error", {}).get("message", "")[:100]
            print(f"  {model}: ❌ {status} → {err}")
    except Exception as e:
        print(f"  {model}: ❌ {e}")
