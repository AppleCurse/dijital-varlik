"""Doğrudan LiteLLM API çağrısı test et."""
import requests, json, time

# Test 1: 9router modeli (eski, çalışması lazım)
print("TEST 1: 9router")
payload = {
    "model": "9router",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "max_tokens": 20
}
try:
    resp = requests.post("http://localhost:4000/chat/completions",
        headers={"Authorization": "Bearer omniroute", "Content-Type": "application/json"},
        json=payload, timeout=30)
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  Response: {resp.json()['choices'][0]['message']['content']}")
    else:
        print(f"  Body: {resp.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")

time.sleep(1)

# Test 2: kr/claude-sonnet-4.5
print("\nTEST 2: kr/claude-sonnet-4.5")
payload["model"] = "kr/claude-sonnet-4.5"
try:
    resp = requests.post("http://localhost:4000/chat/completions",
        headers={"Authorization": "Bearer omniroute", "Content-Type": "application/json"},
        json=payload, timeout=30)
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  Response: {resp.json()['choices'][0]['message']['content']}")
    else:
        print(f"  Body: {resp.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")
