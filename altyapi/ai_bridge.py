"""
Birlesik AI Koprusu — Tum LLM ve Arama API'leri tek catida.

Tavily (web arama) + DeepSeek + Gemini + 9Router.
Otomatik fallback zinciri: 9Router → DeepSeek → Gemini.
"""
import os, requests, json
from typing import Optional

# API keyleri
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")


class AIBridge:
    """Tek noktadan tum AI cagrilari."""

    def tavily_search(self, query: str, max_results: int = 5) -> dict:
        """Tavily ile gercek web aramasi."""
        key = os.getenv("TAVILY_API_KEY", "")
        if not key:
            return {"status": "error", "message": "TAVILY_API_KEY yok"}
        try:
            r = requests.post("https://api.tavily.com/search",
                json={"api_key": key, "query": query, "max_results": max_results,
                      "search_depth": "basic"}, timeout=15)
            data = r.json()
            results = []
            for item in data.get("results", [])[:max_results]:
                results.append({"title": item.get("title", ""),
                               "url": item.get("url", ""),
                               "content": item.get("content", "")[:300]})
            return {"status": "ok", "results": results, "count": len(results),
                    "answer": data.get("answer", "")[:500]}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}

    def deepseek_chat(self, messages: list, max_tokens: int = 500) -> dict:
        """DeepSeek API cagrisi."""
        if not DEEPSEEK_KEY:
            return {"status": "error", "message": "DEEPSEEK_API_KEY yok"}
        try:
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": messages,
                      "max_tokens": max_tokens, "stream": False}, timeout=30)
            d = r.json()
            return {"status": "ok", "content": d["choices"][0]["message"]["content"],
                    "model": d.get("model", "deepseek-chat")}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}

    def gemini_chat(self, messages: list, max_tokens: int = 500) -> dict:
        """Gemini API cagrisi."""
        if not GEMINI_KEY:
            return {"status": "error", "message": "GEMINI_API_KEY yok"}
        try:
            # Gemini API expects different format
            contents = []
            for m in messages:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                params={"key": GEMINI_KEY},
                json={"contents": contents,
                      "generationConfig": {"maxOutputTokens": max_tokens}}, timeout=30)
            d = r.json()
            text = d["candidates"][0]["content"]["parts"][0]["text"]
            return {"status": "ok", "content": text, "model": "gemini-2.0-flash"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}

    def chat(self, messages: list, max_tokens: int = 500) -> dict:
        """Fallback zinciri: 9Router → DeepSeek → Gemini."""
        # 1. 9Router
        try:
            from altyapi.litellm_bridge import litellm
            r = litellm.chat(messages, max_tokens=max_tokens)
            if r and r.get("content"):
                return {"status": "ok", "content": r["content"][:1000], "model": r.get("model", "9router")}
        except: pass

        # 2. DeepSeek
        r = self.deepseek_chat(messages, max_tokens)
        if r["status"] == "ok":
            return r

        # 3. Gemini
        return self.gemini_chat(messages, max_tokens)


ai = AIBridge()
