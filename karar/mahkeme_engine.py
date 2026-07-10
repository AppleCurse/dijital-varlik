"""
Hakikat Mahkemesi — Minimal Viable Debate Engine
4 Rol: Savcı, Savunma, Şüpheci, Hakim
Sadece Hakim'den APPROVED alan çıktı sistemi terk eder.

v2.1 — config/config.py ile entegre, Open WebUI Pipe uyumlu.
"""
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# Proje yolunu ekle (WSL'de çalışırken)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.config import Config as config

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests")
    import requests


class Verdict(Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


@dataclass
class DebateTurn:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MahkemeResult:
    verdict: Verdict
    judge_reasoning: str
    debate_log: list
    approved_output: Optional[str] = None
    confidence: float = 0.0
    minority_report: Optional[str] = None


# --- System Prompt'lar ---

PROSECUTOR_PROMPT = """Sen HAKİKAT MAHKEMESİ'nin SAVCISISIN. Görevin:
Eline ulaşan önermeyi SAVUNMAK ve DOĞRULUĞUNU KANITLAMAKTIR.

Yaklaşımın:
1. Önermeyi en güçlü argümanlarla savun
2. Lehte delilleri sun
3. Karşı tarafın bulabileceği zayıflıkları önceden tespit edip cevapla
4. Somut veri, kaynak ve mantıksal çıkarımlar kullan
5. Abartıdan ve safsatadan kaçın

ÇIKTI FORMATI (JSON):
{
  "position": "DEFENSE",
  "arguments": ["argüman1", "argüman2", ...],
  "evidence": ["delil1", "delil2", ...],
  "confidence": 0.0-1.0
}"""

DEFENSE_PROMPT = """Sen HAKİKAT MAHKEMESİ'nin SAVUNMA AVUKATISIN (Muhalif). Görevin:
Eline ulaşan önermeyi ÇÜRÜTMEK ve YANLIŞLIĞINI GÖSTERMEKTİR.

Yaklaşımın:
1. Önermenin zayıf noktalarını acımasızca deşifre et
2. Mantık hatalarını, tutarsızlıkları, eksik öncülleri bul
3. Karşı delilleri sırala
4. Duygusal değil, soğukkanlı ve analitik ol

ÇIKTI FORMATI (JSON):
{
  "position": "OPPOSITION",
  "counter_arguments": ["karşı argüman1", ...],
  "logical_fallacies": ["safsata1", ...],
  "counter_evidence": ["karşı delil1", ...],
  "confidence": 0.0-1.0
}"""

SKEPTIC_PROMPT = """Sen HAKİKAT MAHKEMESİ'nin ŞÜPHECİSİSİN. Görevin:
Tartışmanın KÖR NOKTALARINI ve EKSİK KANITLARI bulmaktır.

Ne savcıdan ne de savunmadan yanasın. Senin düşmanın ORTAK YANLIŞ VARSAYIMLAR.

ÇIKTI FORMATI (JSON):
{
  "position": "SKEPTIC",
  "blind_spots": ["kör nokta1", ...],
  "unquestioned_assumptions": ["sorgulanmamış varsayım1", ...],
  "missing_evidence": ["eksik kanıt1", ...],
  "falsification_test": "yanlışlanabilirlik testi önerisi",
  "confidence": 0.0-1.0
}"""

JUDGE_PROMPT = """Sen HAKİKAT MAHKEMESİ'nin HAKİMİSİN. Görevin:
Tüm argümanları değerlendirip NİHAİ KARARI vermektir.

Kuralların:
1. ŞÜPHECİ'NİN bulgularına ÖZEL ÖNEM ver
2. %100 emin değilsen APPROVED verme
3. En ufak şüphede NEEDS_MORE_EVIDENCE ile geri çevir

ÇIKTI FORMATI (JSON):
{
  "verdict": "APPROVED" | "REJECTED" | "NEEDS_MORE_EVIDENCE",
  "reasoning": "detaylı gerekçe",
  "confidence": 0.0-1.0,
  "approved_output": "sadece APPROVED ise, doğrulanmış nihai çıktı metni",
  "dissent_note": "varsa azınlık görüşü/çekince"
}"""

JUDGE_PROMPT_TASK = """Sen HAKİKAT MAHKEMESİ'nin HAKİMİSİN. Görevin:
Bir İCRA TALEBİNİ güvenlik ve uygunluk açısından değerlendirip NİHAİ KARARI vermektir.

BU BIR OLGUSAL IDDIA DOĞRULAMASI DEĞİL, BIR GÖREV ONAYIDIR.

Değerlendirme kriterlerin:
1. Görev açıkça zararlı, yasa dışı veya etik dışı mı? → REJECTED
2. Görev sistemin yetki ve araç sınırları içinde mi?
3. Riskler yönetilebilir ve kabul edilebilir düzeyde mi?
4. Makul bir kullanıcı bu görevin yapılmasını bekler miydi?

ÖNEMLİ: Bu bir görev onayıdır, olgusal doğruluk denetimi değildir.
- Görev güvenli ve uygunsa APPROVED ver.
- Sadece açık bir tehlike veya kötüye kullanım varsa REJECTED ver.
- Küçük belirsizlikler NEEDS_MORE_EVIDENCE değil, APPROVED ile sonuçlanmalıdır.
- Amaç sistemi felç etmek değil, güvenli çalışmayı sağlamaktır.

ÇIKTI FORMATI (JSON):
{
  "verdict": "APPROVED" | "REJECTED" | "NEEDS_MORE_EVIDENCE",
  "reasoning": "detaylı gerekçe",
  "confidence": 0.0-1.0,
  "approved_output": "sadece APPROVED ise, güvenli bulunan görev açıklaması",
  "dissent_note": "varsa azınlık görüşü/çekince"
}"""



def _parse_sse(text: str) -> dict:
    """SSE streaming yanitini JSON dict'e cevir."""
    content_parts = []
    for line in text.split("\n"):
        if line.startswith("data: ") and line != "data: [DONE]":
            try:
                data = json.loads(line[6:])
                # Anthropic format
                if "content" in data and isinstance(data["content"], list):
                    for block in data["content"]:
                        if block.get("type") == "text" and "text" in block:
                            content_parts.append(block["text"])
                # Delta format
                if "delta" in data:
                    d = data["delta"]
                    if "text" in d:
                        content_parts.append(d["text"])
                    if "type" in data and data["type"] == "content_block_delta":
                        if "text_delta" in str(d):
                            content_parts.append(d.get("text", ""))
            except json.JSONDecodeError:
                continue
    if content_parts:
        return {"content": "".join(content_parts)}
    return {}

def _parse_verdict_heuristic(text: str) -> dict:
    """JSON olmayan yanittan verdict cikar."""
    t = text.lower()
    # Verdict extraction
    verdict = "NEEDS_MORE_EVIDENCE"
    if "approved" in t or "dogru" in t or "doğru" in t or "correct" in t:
        verdict = "APPROVED"
    elif "rejected" in t or "yanlis" in t or "yanlış" in t or "incorrect" in t:
        verdict = "REJECTED"
    # Confidence extraction
    confidence = 0.7
    import re
    pct = re.search(r'(\d{1,3})\s*%', text)
    if pct:
        confidence = int(pct.group(1)) / 100.0
    elif re.search(r'kesin|emin|certain|100', t):
        confidence = 0.95
    # Reasoning
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    reasoning = " ".join(lines[:5])[:500]
    return {"verdict": verdict, "reasoning": reasoning, "confidence": confidence}

class LLMClient:
    """9router uzerinden LLM cagrilari. OpenAI + Anthropic format destegi."""

    def __init__(self, base_url: str = None, api_key: str = None):
        raw = (base_url or config.LITELLM_URL).rstrip("/")
        # 9router /v1 path'ini duzgun kullan
        if raw.endswith("/v1"):
            self.base_url = raw
        else:
            self.base_url = raw + "/v1" if "/v1" not in raw else raw
        self.api_key = api_key or config.LITELLM_KEY

    def call(self, system_prompt: str, user_message: str,
             model: str = None, temperature: float = 0.3,
             max_tokens: int = 4096) -> dict:
        """LLM cagrisi — OpenAI Chat, basarisizsa fallback."""
        model = model or config.MAHKEME_MODEL

        # OpenAI Chat Completions (9router'in ana destegi)
        result = self._call_openai(system_prompt, user_message,
                                   model, temperature, max_tokens)
        if result and "error" not in result:
            return result

        # Fallback: Anthropic Messages API
        result = self._call_anthropic(system_prompt, user_message,
                                      model, temperature, max_tokens)
        if result and "error" not in result:
            return result

        return result or {"error": "All endpoints failed"}

    def _call_openai(self, system_prompt, user_message, model, temperature, max_tokens):
        """OpenAI Chat Completions endpoint'i."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        return self._post(f"{self.base_url}/chat/completions", headers, payload)

    def _call_anthropic(self, system_prompt, user_message, model, temperature, max_tokens):
        """Anthropic Messages API endpoint'i (9router uyumlu)."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message}
            ],
            "stream": False,
        }
        return self._post(f"{self.base_url}/messages", headers, payload)

    def _post(self, url, headers, payload):
        content = None
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                print(f"[LLM ERROR] {resp.status_code} for url: {url}", file=sys.stderr)
                return {"error": f"HTTP {resp.status_code}", "raw_response": resp.text[:500]}

            raw_text = resp.text or ""

            # SSE streaming yanitini JSON'a cevir
            if raw_text.startswith("event:") or raw_text.startswith("data:"):
                content = _parse_sse(raw_text)
                if content:
                    return content

            # Anthropic format yaniti
            data = resp.json()
            if "content" in data and isinstance(data["content"], list):
                for block in data["content"]:
                    if block.get("type") == "text":
                        content = block["text"]
                        break

            # OpenAI format yaniti
            if not content and "choices" in data:
                content = data["choices"][0]["message"]["content"]

            if not content:
                # SSE'den parse edilemeyen durum
                print(f"[LLM ERROR] Could not extract content. Raw: {raw_text[:300]}", file=sys.stderr)
                return {"error": "No content in response", "raw_response": raw_text[:500]}
            if not content or not content.strip():
                print(f"[LLM ERROR] Empty response from API", file=sys.stderr)
                return {"error": "Empty API response"}

            # REFUSAL DETECTION
            refusal_phrases = [
                "i can't discuss that",
                "i cannot discuss that",
                "i can't help with that",
                "i'm not able to",
                "i cannot provide",
                "i can't provide"
            ]
            content_lower = content.lower()
            if any(phrase in content_lower for phrase in refusal_phrases):
                print(f"[MAHKEME REFUSAL] LLM refused request. Response: {content[:200]}", file=sys.stderr)
                print(f"[MAHKEME REFUSAL] System: {system_prompt[:150]}...", file=sys.stderr)
                print(f"[MAHKEME REFUSAL] User: {user_message[:150]}...", file=sys.stderr)
                return {
                    "error": "LLM_REFUSAL",
                    "refusal_message": content,
                    "position": "REFUSED",
                    "confidence": 0.0
                }

            # AGGRESSIVE JSON CLEANING + FALLBACK
            content = content.strip()
            # Markdown code block — extract content inside ```json ... ```
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1].strip()
                else:
                    lines = [l for l in content.split("\n") if not l.strip().startswith("```")]
                    content = "\n".join(lines).strip()
            # Extract JSON object from mixed text
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end].lstrip("\ufeff\u200b\xa0")
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass  # fall through to heuristic parser
            # JSON yoksa metinden verdict cikar (heuristic fallback)
            return _parse_verdict_heuristic(content)
        except json.JSONDecodeError as e:
            print(f"[LLM JSON ERROR] {e}\nRaw: {content[:500] if content else 'N/A'}", file=sys.stderr)
            return {"raw_response": content[:2000]}
        except Exception as e:
            print(f"[LLM ERROR] {e}", file=sys.stderr)
            try:
                return {"raw_response": resp.text[:500] if resp and hasattr(resp, 'text') else str(e)[:500]}
            except:
                return {"error": str(e)}


class HakikatMahkemesi:
    """4 aşamalı Minimal Viable Debate motoru."""

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()
        self.log: list[DebateTurn] = []

    def _add_turn(self, role: str, content: str):
        turn = DebateTurn(role=role, content=content)
        self.log.append(turn)
        return turn

    def _format_context(self, turns: list[DebateTurn]) -> str:
        return "\n".join([f"\n### {t.role}\n{t.content}" for t in turns])

    # Hızlı yol: 0 LLM çağrısı ile onaylanacak güvenli kalıplar
    _FAST_PATH_PATTERNS = [
        "merhaba", "nasılsın", "saat", "tarih", "bugün",
        "example.com", "kimsin", "ne yapıyorsun", "teşekkür",
        "günaydın", "iyi akşamlar", "selam", "hey", "hello", "hi",
        "hava", "yardım", "neler yapabilirsin",
    ]

    def _fast_path_check(self, claim: str) -> dict | None:
        """Güvenli kalıpsa APPROVED döndür. Engelleyici kelime varsa None."""
        lower = claim.lower()
        # Engelleyici var mı? (kelime sınırı kontrolü)
        tokens = set(lower.replace(',', ' ').replace('.', ' ').split())
        blocker_words = {"sil", "format", "sudo", "delete", "şifre", "password",
                         "hack", "exploit", "ddos", "kişisel"}
        if tokens & blocker_words:
            return None
        # Tehlikeli kalıplar (substring)
        dangerous = ["rm -rf", "drop table", "kredi kartı", "tc kimlik"]
        if any(d in lower for d in dangerous):
            return None
        # Güvenli kalıp var mı?
        if any(p in lower for p in self._FAST_PATH_PATTERNS):
            return {
                "verdict": "APPROVED",
                "confidence": 1.0,
                "judge_reasoning": "Hızlı yol: güvenli kalıp",
                "minority_report": None,
            }
        return None

    def yargila(self, claim: str, context: str = "", mode: str = "claim") -> MahkemeResult:
        """Bir önermeyi mahkeme sürecinden geçir.

        Args:
            claim: Değerlendirilecek önerme / görev
            context: Ek bağlam
            mode: "claim" (olgusal iddia, katı standart) veya "task" (icra görevi, makul standart)
        """
        # Hızlı yol: güvenli kalıplar için 0 LLM çağrısı
        fast = self._fast_path_check(claim)
        if fast:
            try:
                verdict = Verdict(fast["verdict"])
            except ValueError:
                verdict = Verdict.APPROVED
            return MahkemeResult(
                verdict=verdict,
                confidence=fast["confidence"],
                judge_reasoning=fast["judge_reasoning"],
                debate_log=[],
                minority_report=fast.get("minority_report"),
            )

        is_task = mode == "task"
        judge_prompt = JUDGE_PROMPT_TASK if is_task else JUDGE_PROMPT

        full_prompt = f"""ÖNERME (doğrulanacak):
{claim}

EK BAĞLAM:
{context if context else '(Ek bağlam verilmedi)'}"""

        print(f"\n{'='*60}")
        print(f"MAHKEME STARTING [{mode.upper()} MODE]: {claim[:100]}...")

        # Aşama 1: Savcı
        print("[1/4] Prosecutor preparing defense...")
        prosecutor_raw = self.llm.call(PROSECUTOR_PROMPT, full_prompt)
        self._add_turn("SAVCI", json.dumps(prosecutor_raw, ensure_ascii=False, indent=2))

        # Aşama 2: Savunma
        print("[2/4] Defense preparing counter-arguments...")
        defense_raw = self.llm.call(DEFENSE_PROMPT,
                                     full_prompt + self._format_context(self.log))
        self._add_turn("SAVUNMA", json.dumps(defense_raw, ensure_ascii=False, indent=2))

        # Aşama 3: Şüpheci
        print("[3/4] Skeptic searching for blind spots...")
        skeptic_raw = self.llm.call(SKEPTIC_PROMPT,
                                     full_prompt + self._format_context(self.log))
        self._add_turn("SKEPTIC", json.dumps(skeptic_raw, ensure_ascii=False, indent=2))

        # Aşama 4: Hakim
        print("[4/4] Judge rendering verdict...")
        judge_raw = self.llm.call(judge_prompt,
                                   full_prompt + self._format_context(self.log))
        self._add_turn("JUDGE", json.dumps(judge_raw, ensure_ascii=False, indent=2))

        # DEBUG: Log response structure
        print(f"[DEBUG] Judge response keys: {list(judge_raw.keys())}")
        print(f"[DEBUG] Confidence value: {judge_raw.get('confidence', 'MISSING')}")
        if 'raw_response' in judge_raw:
            print(f"[DEBUG] Raw response: {judge_raw['raw_response'][:300]}")

        # Parse
        verdict_str = judge_raw.get("verdict", "NEEDS_MORE_EVIDENCE").upper()
        try:
            verdict = Verdict(verdict_str)
        except ValueError:
            verdict = Verdict.NEEDS_MORE_EVIDENCE

        result = MahkemeResult(
            verdict=verdict,
            judge_reasoning=judge_raw.get("reasoning", ""),
            debate_log=list(self.log),
            approved_output=judge_raw.get("approved_output") if verdict == Verdict.APPROVED else None,
            confidence=judge_raw.get("confidence", 0.0),
            minority_report=judge_raw.get("dissent_note"),
        )

        print(f"VERDICT: {result.verdict.value} (Confidence: {result.confidence:.1%})")
        print(f"{'='*60}")
        return result


# --- Open WebUI Pipe Modu ---

def pipe(body: dict) -> dict:
    """
    Open WebUI Pipe uyumlu giriş noktası.

    Girdi: {"claim": "...", "context": "..."}  veya  {"text": "..."}
    Çıktı: {"status": "approved", "output": "..."} veya {"status": "rejected", "reason": "..."}
    """
    mahkeme = HakikatMahkemesi()

    claim = body.get("claim") or body.get("text") or body.get("message") or str(body)
    ctx = body.get("context", "")

    result = mahkeme.yargila(claim, ctx)

    if result.verdict == Verdict.APPROVED:
        return {
            "status": "approved",
            "output": result.approved_output or claim,
            "confidence": result.confidence,
            "verdict": "APPROVED"
        }
    else:
        return {
            "status": "rejected",
            "reason": result.judge_reasoning,
            "verdict": result.verdict.value,
            "minority_report": result.minority_report
        }


# --- CLI modu (geriye uyumlu) ---

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--pipe":
        # stdin/stdout pipe modu (geriye uyumlu)
        input_data = sys.stdin.read().strip()
        if not input_data:
            print("HATA: Giriş verisi boş.")
            sys.exit(1)
        try:
            body = json.loads(input_data)
        except json.JSONDecodeError:
            body = {"claim": input_data}
        result = pipe(body)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["status"] == "approved" else 1)

    elif len(sys.argv) > 1 and sys.argv[1] == "--demo":
        mahkeme = HakikatMahkemesi()
        result = mahkeme.yargila(
            "Python web geliştirme için en iyi seçimdir.",
            "Demo testi — genel programlama dilleri karşılaştırması"
        )
        print(f"\nSONUÇ: {result.verdict.value}")

    else:
        # Varsayılan: Open WebUI pipe modunda bekle
        print("Hakikat Mahkemesi hazır. Kullanım:")
        print("  python mahkeme_engine.py --pipe    (stdin/stdout)")
        print("  python mahkeme_engine.py --demo    (test)")
        print("  Open WebUI: pipe(body) fonksiyonu kullanır")


if __name__ == "__main__":
    main()
