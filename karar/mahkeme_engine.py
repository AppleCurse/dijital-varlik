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
Üretilen bir sonucun orijinal göreve uygunluğunu ve kalitesini değerlendirmektir.

Kuralların:
1. Sonuç görevle ilgili ve faydalıysa APPROVED ver.
2. Sonuç tamamen alakasız, yanlış veya zararlıysa REJECTED ver.
3. Sonuç kısmen doğru ama eksikse bile APPROVED verebilirsin (küçük eksikler için NEEDS_MORE_EVIDENCE kullanma).
4. Amacın sistemi felç etmek değil, makul cevapları geçirmektir.
5. Şüphe durumunda APPROVED lehine karar ver.

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
    """
    Coklu provider fallback'li LLM istemcisi.
    Sira: DeepSeek → Groq → NVIDIA → OpenRouter
    Her provider basarisiz olursa siradakine gecer.
    """

    # Provider zinciri — .env'den okur, yoksa default
    def _load_providers(self):
        import os as _os
        return [
            {
                "name": "deepseek",
                "url": _os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1"),
                "key": _os.getenv("DEEPSEEK_API_KEY", ""),
                "model": _os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            },
            {
                "name": "groq",
                "url": _os.getenv("GROQ_URL", "https://api.groq.com/openai/v1"),
                "key": _os.getenv("GROQ_API_KEY", ""),
                "model": _os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            },
            {
                "name": "nvidia",
                "url": _os.getenv("NVIDIA_URL", "https://integrate.api.nvidia.com/v1"),
                "key": _os.getenv("NVIDIA_API_KEY", ""),
                "model": _os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct"),
            },
            {
                "name": "openrouter",
                "url": _os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
                "key": _os.getenv("OPENROUTER_API_KEY", ""),
                "model": _os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            },
        ]

    def __init__(self, base_url: str = None, api_key: str = None):
        self.providers = self._load_providers()
        # Tek provider (geriye uyumlu)
        self.base_url = (base_url or config.LITELLM_URL).rstrip("/")
        self.api_key = api_key or config.LITELLM_KEY

    def call(self, system_prompt: str, user_message: str,
             model: str = None, temperature: float = 0.3,
             max_tokens: int = 4096) -> dict:
        """LLM cagrisi — 4 provider fallback zinciri."""
        model = model or config.MAHKEME_MODEL
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Her provider'i sirasiyla dene
        for provider in self.providers:
            if not provider["key"]:
                continue

            result = self._try_provider(provider, messages, model, temperature, max_tokens)
            if result and "error" not in result:
                result["_provider"] = provider["name"]
                return result

        # Tum provider'lar basarisiz — direkt URL'yi dene
        print("[LLM] Tum provider'lar basarisiz, direkt URL deneniyor...", file=sys.stderr)
        result = self._call_openai_direct(system_prompt, user_message, model, temperature, max_tokens)
        if result and "error" not in result:
            return result
        return {"error": "All providers failed"}

    def _try_provider(self, provider, messages, model, temperature, max_tokens):
        """Tek bir provider'a OpenAI-format istek gonder."""
        url = f"{provider['url'].rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {str(provider['key']).strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        return self._post(url, headers, payload, provider["name"])

    def _call_openai_direct(self, system_prompt, user_message, model, temperature, max_tokens):
        """Direkt URL'ye OpenAI-format istek (geriye uyumlu fallback)."""
        headers = {
            "Authorization": f"Bearer {str(self.api_key).strip()}",
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
        return self._post(f"{self.base_url}/chat/completions", headers, payload, "direct")

    def _post(self, url, headers, payload, provider_name: str = ""):
        content = None
        tag = f"[LLM:{provider_name}]" if provider_name else "[LLM]"
        try:
            import json as _json
            resp = requests.post(url, headers=headers, data=_json.dumps(payload, ensure_ascii=False).encode('utf-8'), timeout=120)
            if resp.status_code != 200:
                print(f"{tag} HTTP {resp.status_code} → siradaki...", file=sys.stderr)
                return {"error": f"HTTP {resp.status_code}"}
            
            raw_text = resp.text or ""
            # JSON ise parse et
            if raw_text.strip().startswith("{"):
                try:
                    data = json.loads(raw_text)
                    if "choices" in data and data["choices"]:
                        message = data["choices"][0].get("message", {})
                        # message içinde content veya reasoning_content var
                        msg_content = message.get("content", "")
                        reasoning = message.get("reasoning_content", "")
                        # reasoning varsa onu kullan, yoksa content
                        if reasoning:
                            content = reasoning.strip()
                        elif msg_content:
                            content = msg_content.strip()
                        else:
                            content = _reasoning_temizle(json.dumps(message))
                        
                        if content:
                            return {
                                "content": content,
                                "model": data.get("model", ""),
                                "usage": data.get("usage", {}),
                                "raw": data
                            }
                except json.JSONDecodeError:
                    pass
            
            # Düz metin ise
            content = _reasoning_temizle(raw_text)
            if content:
                return {
                    "content": content,
                    "model": "",
                    "usage": {},
                    "raw": {"text": raw_text}
                }
            
            print(f"{tag} Could not extract content. Raw: {raw_text[:200]}", file=sys.stderr)
            return {"error": "No content extracted"}
        except Exception as e:
            print(f"{tag} Exception: {e}", file=sys.stderr)
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

        # DEBUG
        print(f"[DEBUG] Judge response keys: {list(judge_raw.keys())}")

        # content alanından JSON çıkarmaya çalış
        parsed = {}
        raw_content = judge_raw.get("content", "") or ""
        
        # Önce content içinde JSON arıyoruz
        import re, json as _json
        json_match = re.search(r'\{[\s\S]*\}', raw_content)
        if json_match:
            try:
                parsed = _json.loads(json_match.group(0))
            except Exception:
                parsed = {}
        
        # Hâlâ boşsa heuristic kullan
        if not parsed:
            parsed = _parse_verdict_heuristic(raw_content)
        
        # Eğer LLM zaten dict verdiyse onu da dene
        if not parsed and isinstance(judge_raw, dict):
            if "verdict" in judge_raw:
                parsed = judge_raw

        print(f"[DEBUG] Parsed keys: {list(parsed.keys())}")
        print(f"[DEBUG] Confidence: {parsed.get('confidence', 'MISSING')}")

        verdict_str = str(parsed.get("verdict", "NEEDS_MORE_EVIDENCE")).upper()
        try:
            verdict = Verdict(verdict_str)
        except ValueError:
            verdict = Verdict.NEEDS_MORE_EVIDENCE

        conf = parsed.get("confidence", 0.0)
        try:
            conf = float(conf)
        except Exception:
            conf = 0.0

        result = MahkemeResult(
            verdict=verdict,
            judge_reasoning=parsed.get("reasoning", raw_content[:400]),
            debate_log=list(self.log),
            approved_output=parsed.get("approved_output") if verdict == Verdict.APPROVED else None,
            confidence=conf,
            minority_report=parsed.get("dissent_note"),
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
