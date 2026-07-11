"""Quick test: Can 9router model handle a basic chat completion?"""
import requests, json

url = "http://localhost:4000/chat/completions"
headers = {"Authorization": "Bearer omniroute", "Content-Type": "application/json"}
payload = {
    "model": "9router",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "max_tokens": 20,
}

print(f"Testing 9router at {url}...")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print(f"Response: {content}")
        print("9router OK!")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
