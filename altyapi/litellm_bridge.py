"""
Katman 4 — LiteLLM Köprüsü
Tüm LLM çağrıları buradan geçer.
4 provider fallback: DeepSeek → Groq → NVIDIA → OpenRouter
"""
import requests
import json
import re
import os
from typing import Optional
from config.config import config


def _reasoning_temizle(ham_yanit: str) -> str:
    """Reasoning model <think> bloklarini ayiklar."""
    for desen in [r'<think>(.*?)</think>', r'<thinking>(.*?)</thinking>', r'<reasoning>(.*?)</reasoning>']:
        ham_yanit = re.sub(desen, '', ham_yanit, flags=re.DOTALL | re.IGNORECASE)
    temiz = ham_yanit.strip()
    if len(temiz) < 5 and len(ham_yanit) > 500:
        return ""
    return temiz


# ── Provider Fallback Zinciri (sira ONEMLI) ──

PROVIDERS = [
    {
        "name": "omniroute",
        "url":   os.getenv("OMNIROUTE_URL", "http://localhost:3000/v1"),
        "key":   os.getenv("OMNIROUTE_API_KEY", "sk-d284d18e441e2a43-484250-242a270f"),
        "model": os.getenv("OMNIROUTE_MODEL", "auto"),
    },
    {
        "name": "deepseek",
        "url":   os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1"),
        "key":   os.getenv("DEEPSEEK_API_KEY", ""),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    },
    {
        "name": "groq",
        "url":   os.getenv("GROQ_URL", "https://api.groq.com/openai/v1"),
        "key":   os.getenv("GROQ_API_KEY", ""),
        "model": os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
    },
    {
        "name": "nvidia",
        "url":   os.getenv("NVIDIA_URL", "https://integrate.api.nvidia.com/v1"),
        "key":   os.getenv("NVIDIA_API_KEY", ""),
        "model": os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct"),
    },
    {
        "name": "openrouter",
        "url":   os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
        "key":   os.getenv("OPENROUTER_API_KEY", ""),
        "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    },
]


class LiteLLMBridge:
    """Coklu provider fallback'li LLM erisimi."""

    def __init__(self):
        self.providers = PROVIDERS
        self.default_model = config.MAHKEME_MODEL
        self.fallback_model = config.FALLBACK_MODEL

    def health(self) -> bool:
        """En az bir provider saglikli mi?"""
        for p in self.providers:
            try:
                resp = requests.get(
                    f"{p['url'].rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {p['key']}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    return True
            except Exception:
                continue
        return False

    def models(self) -> list:
        """Tum provider'lardaki modelleri listele."""
        all_models = []
        for p in self.providers:
            try:
                resp = requests.get(
                    f"{p['url'].rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {p['key']}"},
                    timeout=10
                )
                data = resp.json().get("data", [])
                for m in data:
                    m["_provider"] = p["name"]
                all_models.extend(data)
            except Exception:
                continue
        return all_models

    def chat(self, messages: list, model: str = None,
             temperature: float = 0.3, max_tokens: int = 4096,
             response_format: dict = None, timeout: int = 120) -> Optional[dict]:
        """
        Chat completion — 4 provider fallback zinciri ile.

        Sira: DeepSeek → Groq → NVIDIA → OpenRouter
        Her provider basarisiz olursa siradakine gecer.

        Returns:
            {"content": str, "model": str, "provider": str, "usage": dict}
        """
        last_error = None

        for provider in self.providers:
            if not provider["key"]:
                continue

            url = f"{provider['url'].rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {provider['key']}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model or provider["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }
            if response_format:
                payload["response_format"] = response_format

            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]

                return {
                    "content": _reasoning_temizle(choice["message"]["content"]),
                    "model": data.get("model", provider["model"]),
                    "provider": provider["name"],
                    "usage": data.get("usage", {}),
                    "raw": data
                }
            except Exception as e:
                last_error = e
                print(f"[LLM] {provider['name']} basarisiz → siradaki... ({type(e).__name__})")
                continue

        print(f"[LLM] TUM PROVIDER'LAR BASARISIZ: {last_error}")
        return None

    def is_alive(self) -> bool:
        return self.health()


# Global instance
litellm = LiteLLMBridge()
