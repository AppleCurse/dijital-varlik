"""
Katman 4 — LiteLLM Köprüsü
Tüm LLM çağrıları buradan geçer. Rate limiting, fallback, retry yönetir.
"""
import requests
import json

def _reasoning_temizle(ham_yanit: str) -> str:
    """Reasoning model <think> bloklarini ayiklar."""
    import re
    for desen in [r'<think>(.*?)</think>', r'<thinking>(.*?)</thinking>', r'<reasoning>(.*?)</reasoning>']:
        ham_yanit = re.sub(desen, '', ham_yanit, flags=re.DOTALL | re.IGNORECASE)
    temiz = ham_yanit.strip()
    if len(temiz) < 5 and len(ham_yanit) > 500:
        return ""  # reasoning yarida kesilmis, bos cevap
    return temiz

from typing import Optional
from config.config import config


class LiteLLMBridge:
    """LiteLLM proxy üzerinden tüm LLM erişimini yönetir."""

    def __init__(self):
        self.base_url = config.LITELLM_URL.rstrip("/")
        self.api_key = config.LITELLM_KEY
        self.default_model = config.MAHKEME_MODEL
        self.fallback_model = config.FALLBACK_MODEL

    def health(self) -> bool:
        """9router sağlık kontrolü (/v1/health yok, /models kullanılır)."""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return resp.status_code == 200
        except Exception:
            return False

    def models(self) -> list:
        """Kullanılabilir modelleri listele."""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return resp.json().get("data", [])
        except Exception as e:
            print(f"[LiteLLM] Model listesi alınamadı: {e}")
            return []

    def chat(self, messages: list, model: str = None,
             temperature: float = 0.3, max_tokens: int = 4096,
             response_format: dict = None, timeout: int = 120) -> Optional[dict]:
        """
        Chat completion çağrısı. Önce primary model, başarısız olursa fallback.

        Returns:
            {
                "content": str,
                "model": str,
                "usage": dict,
                "raw": dict
            }
        """
        models_to_try = [model or self.default_model]
        if models_to_try[0] != self.fallback_model:
            models_to_try.append(self.fallback_model)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        last_error = None

        for m in models_to_try:
            payload = {
                "model": m,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }
            if response_format:
                payload["response_format"] = response_format

            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]

                return {
                    "content": _reasoning_temizle(choice["message"]["content"]),
                    "model": data.get("model", m),
                    "usage": data.get("usage", {}),
                    "raw": data
                }
            except Exception as e:
                last_error = e
                print(f"[LiteLLM] {m} başarısız, sonraki deneniyor... ({e})")
                continue

        print(f"[LiteLLM] Tüm modeller başarısız: {last_error}")
        return None

    def is_alive(self) -> bool:
        """Tam bağlantı kontrolü (health + models)."""
        if not self.health():
            return False
        models = self.models()
        return len(models) > 0


# Global instance
litellm = LiteLLMBridge()
