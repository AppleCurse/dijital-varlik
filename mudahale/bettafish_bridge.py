"""
BettaFish Bridge — Sosyal Medya Istihbarati (Izole Hucre)
KENDI .venv_betta'sinda calisir, ana sisteme bagimlilik eklemez.
MindSpider: BroadTopicExtraction + DeepSentimentCrawling
"""
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

ROOT = Path(__file__).resolve().parent.parent
BETTA_DIR = ROOT / "BettaFish-main" / "BettaFish-main"
BETTA_PYTHON = BETTA_DIR / ".venv_betta" / "bin" / "python"
MINDSPIDER = BETTA_DIR / "MindSpider"


class BettaFishBridge:
    """BettaFish istihbarat sistemine izole erisim katmani."""

    def __init__(self):
        self._ready = BETTA_PYTHON.exists()

    def hazir_mi(self) -> bool:
        return self._ready

    def _run_betta(self, script: str) -> dict:
        """BettaFish'in kendi venv'inde Python kodu calistir."""
        if not self._ready:
            return {"status": "error", "message": "BettaFish .venv_betta yok"}

        try:
            r = subprocess.run(
                [str(BETTA_PYTHON), "-c", script],
                capture_output=True, text=True, timeout=60,
                cwd=str(BETTA_DIR),
                env={**os.environ, "PYTHONPATH": str(MINDSPIDER)}
            )
            if r.returncode == 0 and r.stdout.strip():
                try:
                    return json.loads(r.stdout.strip())
                except json.JSONDecodeError:
                    return {"status": "ok", "data": r.stdout.strip()[:500]}
            return {"status": "error", "message": r.stderr[:300] or "Unknown error"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Timeout (60s)"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}

    def gundem_tara(self, konu: str = "") -> dict:
        """Guncel konulari tara (BroadTopicExtraction)."""
        script = f'''
import sys, json, asyncio
sys.path.insert(0, "{MINDSPIDER}")
try:
    from BroadTopicExtraction.main import BroadTopicExtraction
    bte = BroadTopicExtraction()
    keywords = bte.get_keywords_for_crawling()
    analysis = bte.get_daily_analysis()
    print(json.dumps({{"status":"ok","keywords": keywords[:10] if keywords else [],
                      "analysis": str(analysis)[:300] if analysis else "no data"}}))
except Exception as e:
    print(json.dumps({{"status":"error","message": str(e)}}))
'''
        return self._run_betta(script)

    def duygu_analizi(self, konu: str) -> dict:
        """Bir konuda sosyal medya duygu analizi (DeepSentimentCrawling)."""
        script = f'''
import sys, json
sys.path.insert(0, "{MINDSPIDER}")
try:
    from DeepSentimentCrawling.main import DeepSentimentCrawling
    dsc = DeepSentimentCrawling()
    topics = dsc.list_available_topics()
    print(json.dumps({{"status":"ok","topics": str(topics)[:500]}}))
except Exception as e:
    print(json.dumps({{"status":"error","message": str(e)}}))
'''
        return self._run_betta(script)

    def calistir(self, gorev: str) -> dict:
        """Genel amacli BettaFish calistir. Gorev tipine gore yonlendirir."""
        g = gorev.lower()
        if any(k in g for k in ["gundem", "haber", "topic", "konu"]):
            return self.gundem_tara(gorev)


_bettafish: Optional[BettaFishBridge] = None

def get_bettafish() -> BettaFishBridge:
    global _bettafish
    if _bettafish is None:
        _bettafish = BettaFishBridge()
    return _bettafish
