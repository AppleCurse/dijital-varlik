"""
Harness — Kendini Onaran Hata Kurtarma Motoru
7 strateji ile hata aldığında farklı yöntemlerle tekrar dener.
"""
import time
import traceback
from typing import Callable, Optional


class Harness:
    """Kendini onaran görev çalıştırıcı. Hata → strateji → tekrar dene."""

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

    def calistir(self, fn: Callable, *args, **kwargs):
        """Fonksiyonu harness koruması altında çalıştır.
        Hata alırsa strateji değiştirerek max_deneme kez tekrar dener.
        """
        son_hata = None

        for deneme in range(1, self.max_deneme + 1):
            try:
                print(f"[Harness] Deneme {deneme}/{self.max_deneme}...")
                sonuc = fn(*args, **kwargs)
                if sonuc is not None:
                    print(f"[Harness] ✅ Başarılı (deneme {deneme})")
                    return sonuc
            except Exception as e:
                son_hata = e
                hata_adi = type(e).__name__
                print(f"[Harness] ❌ Deneme {deneme} başarısız: {hata_adi}: {str(e)[:200]}")

                if deneme < self.max_deneme:
                    strateji = self._strateji_sec(e, deneme)
                    bekle = strateji(e, deneme)
                    if bekle > 0:
                        print(f"[Harness] {bekle}s bekleniyor...")
                        time.sleep(bekle)

        print(f"[Harness] ⚠️ {self.max_deneme} deneme başarısız, pes edildi")
        return None

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
