import requests
import json
import os

VOICEBOX_URL = "http://localhost:8001"
OPENHANDS_URL = "http://localhost:3005"

def speak(text, profile="default"):
    try:
        r = requests.post(
            f"{VOICEBOX_URL}/speak",
            json={"text": text, "profile": profile},
            timeout=30
        )
        if r.status_code == 200:
            return {"status": "success", "audio": r.content}
        return {"status": "error", "message": r.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def openhands_chat(prompt, model="openhands"):
    try:
        r = requests.post(
            f"{OPENHANDS_URL}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"Hata: {r.status_code} - {r.text}"
    except Exception as e:
        return f"Hata: {str(e)}"

def sesli_komut(prompt, profile="default"):
    response = openhands_chat(prompt)
    speak(response, profile)
    return response

print("✅ OpenHands + Voicebox bridge yüklendi")
