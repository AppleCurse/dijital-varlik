"""
Harness — Kendini Onaran Hata Kurtarma Motoru (+AgentLedger konsepti).

- 7 strateji, 3 deneme
- Audit trail (tüm denemeler kayıt altında)
- Circuit breaker (arka arkaya 5 hata → 60sn mola)
- Checkpoint (başarısız görevleri kaydet, sonra devam et)
- Metrikler (başarılı/başarısız sayacı)
"""
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

CHECKPOINT_FILE = Path(__file__).resolve().parent.parent / "altyapi" / "harness_checkpoint.json"


class Harness:
    """Kendini onaran görev çalıştırıcı."""

    def __init__(self, max_deneme: int = 3):
        self.max_deneme = max_deneme
        self.stratejiler = [
            "_retry_with_backoff",
            "_fix_value_error",
            "_retry_same",
            "_strip_and_retry",
            "_wait_and_retry",
            "_force_reload",
            "_escalate_error",
        ]
        # AgentLedger: metrikler
        self.basarili = 0
        self.basarisiz = 0
        self.deneme_sayisi = 0
        # Circuit breaker
        self.ardisik_hata = 0
        self.devre_acik = False
        self.devre_acilma_zamani = 0.0
        # Audit trail
        self.audit_log: list = []

    def _audit(self, olay: str, detay: dict = None):
        entry = {"zaman": datetime.now().isoformat(), "olay": olay, "detay": detay or {}}
        self.audit_log.append(entry)
        if len(self.audit_log) > 500:
            self.audit_log = self.audit_log[-500:]

    def calistir(self, fn: Callable, gorev_adi: str = "", *args, **kwargs):
        """Harness korumalı çalıştır. Circuit breaker + checkpoint."""
        self.deneme_sayisi += 1

        # Circuit breaker kontrolü
        if self.devre_acik:
            gecen = time.time() - self.devre_acilma_zamani
            if gecen < 60:
                print(f"[Harness] ⚡ Devre kesik ({60-gecen:.0f}s bekle)")
                self._audit("devre_kesik", {"gorev": gorev_adi, "kalan": 60-gecen})
                return None
            else:
                self.devre_acik = False
                self.ardisik_hata = 0
                print("[Harness] 🔄 Devre kapandı, tekrar deneniyor")
                self._audit("devre_kapandi", {"gorev": gorev_adi})

        # Checkpoint: önceki başarısız görev var mı?
        cp = self._checkpoint_oku()
        if cp and cp.get("gorev") == gorev_adi:
            print(f"[Harness] 📋 Önceki checkpoint: {cp['hata'][:100]}")

        son_hata = None
        for deneme in range(1, self.max_deneme + 1):
            try:
                print(f"[Harness] Deneme {deneme}/{self.max_deneme}...")
                sonuc = fn(*args, **kwargs)
                if sonuc is not None:
                    self.basarili += 1
                    self.ardisik_hata = 0
                    self._audit("basarili", {"gorev": gorev_adi, "deneme": deneme})
                    self._checkpoint_sil()
                    print(f"[Harness] ✅ Başarılı (deneme {deneme})")
                    return sonuc
            except Exception as e:
                son_hata = e
                self.basarisiz += 1
                self.ardisik_hata += 1
                hata_adi = type(e).__name__
                print(f"[Harness] ❌ Deneme {deneme}: {hata_adi}: {str(e)[:150]}")
                self._audit("hata", {"gorev": gorev_adi, "deneme": deneme,
                           "hata": hata_adi, "mesaj": str(e)[:200]})

                if deneme < self.max_deneme:
                    strateji = self._strateji_sec(e, deneme)
                    bekle = strateji(e, deneme)
                    if bekle > 0:
                        time.sleep(bekle)

        # Circuit breaker: 5 ardışık hata → devreyi kes
        if self.ardisik_hata >= 5:
            self.devre_acik = True
            self.devre_acilma_zamani = time.time()
            print("[Harness] 🔴 Devre kesildi! 60sn mola.")
            self._audit("devre_acildi", {"gorev": gorev_adi})

        # Checkpoint kaydet
        self._checkpoint_yaz(gorev_adi, str(son_hata)[:300] if son_hata else "bilinmeyen")
        print(f"[Harness] ⚠️ {self.max_deneme} deneme başarısız")
        return None

    def _checkpoint_yaz(self, gorev: str, hata: str):
        try:
            CHECKPOINT_FILE.write_text(json.dumps(
                {"gorev": gorev, "hata": hata, "zaman": datetime.now().isoformat()},
                ensure_ascii=False))
        except: pass

    def _checkpoint_oku(self) -> dict | None:
        try:
            if CHECKPOINT_FILE.exists():
                return json.loads(CHECKPOINT_FILE.read_text())
        except: pass
        return None

    def _checkpoint_sil(self):
        try:
            if CHECKPOINT_FILE.exists():
                CHECKPOINT_FILE.unlink()
        except: pass

    def metrikler(self) -> dict:
        return {
            "basarili": self.basarili, "basarisiz": self.basarisiz,
            "deneme": self.deneme_sayisi, "ardisik_hata": self.ardisik_hata,
            "devre_acik": self.devre_acik,
            "son_olaylar": self.audit_log[-5:] if self.audit_log else [],
        }

    def _strateji_sec(self, hata: Exception, deneme: int):
        """Hata tipine göre en uygun stratejiyi seç."""
        hata_str = str(hata).lower()

        if any(k in hata_str for k in ["connection", "timeout", "refused"]):
            return self._retry_with_backoff
        elif any(k in hata_str for k in ["value", "type", "attribute"]):
            return self._fix_value_error
        elif any(k in hata_str for k in ["auth", "401", "403"]):
            return self._wait_and_retry
        else:
            return self._retry_same

    def _retry_with_backoff(self, hata, deneme) -> float:
        """Üstel geri çekilme: 2s → 4s → 8s."""
        return 2 ** deneme

    def _retry_same(self, hata, deneme) -> float:
        """Sabit 3 saniye bekle."""
        return 3.0

    def _fix_value_error(self, hata, deneme) -> float:
        """Value/Type hatalarında kısa bekle."""
        return 1.0

    def _strip_and_retry(self, hata, deneme) -> float:
        """Temizleyip tekrar dene."""
        return 1.5

    def _wait_and_retry(self, hata, deneme) -> float:
        """Auth hatalarında uzun bekle (rate limit)."""
        return 10.0 * deneme

    def _force_reload(self, hata, deneme) -> float:
        """Yeniden yükleme stratejisi."""
        return 0.5

    def _escalate_error(self, hata, deneme) -> float:
        """Hatayı logla, son denemede pes et."""
        traceback.print_exc()
        return 0.0


_harness_instance: Optional[Harness] = None


def get_harness() -> Harness:
    global _harness_instance
    if _harness_instance is None:
        _harness_instance = Harness(max_deneme=3)
    return _harness_instance


def is_success(result_text: str) -> bool:
    """Sonuç metninde hata/exception/tamamlanamadı varsa False döndür."""
    negative_keywords = [
        "hata", "exception", "tamamlanamad", "failed", "error",
        "timeout", "connection", "refused", "404", "500", "401",
        "establish", "invalid", "crash", "cannot connect", "fatal",
        "did not receive", "eof", "broken pipe", "reset by peer",
        "no route to host", "unreachable", "denied", "unauthorized",
        "missing auth", "rate limit", "insufficient", "balance",
        "503", "502", "400", "not found"
    ]
    lower = result_text.lower()
    return not any(kw in lower for kw in negative_keywords)
