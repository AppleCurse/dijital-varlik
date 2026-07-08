"""
Kesici — Basit sorguları 9Router'a göndermeden yerelde yanıtlar.

STT → Kesici → (basitse) yerel yanıt / (karmaşıksa) 9Router

Kullanım:
    from altyapi.kesici import kesici
    yanit = kesici.isle("saat kaç")  # → "Saat 14:30"
"""
from datetime import datetime


class Kesici:
    """Basit sorgular için yerel yanıt üreticisi."""

    def __init__(self):
        self._basit_kaliplar = {
            "saat": self._saat_yanit,
            "tarih": self._tarih_yanit,
            "bugün": self._tarih_yanit,
            "merhaba": lambda: "Merhaba! Ben Dijital Varlık. Size nasıl yardımcı olabilirim?",
            "selam": lambda: "Selam! Ben Dijital Varlık. Ne yapmamı istersiniz?",
            "nasılsın": lambda: "İyiyim, teşekkürler! Size nasıl yardımcı olabilirim?",
            "kimsin": lambda: "Ben Dijital Varlık — çok modüllü bir AI asistanıyım.",
            "ne yapıyorsun": lambda: "Size yardım etmek için buradayım! Soru sorabilir, web'de gezinebilir, ses ve görüntü işleyebilirim.",
            "teşekkür": lambda: "Rica ederim! Başka bir şeye ihtiyacınız var mı?",
            "günaydın": lambda: "Günaydın! Bugün size nasıl yardımcı olabilirim?",
        }

    def _saat_yanit(self) -> str:
        now = datetime.now()
        return f"Şu an saat {now.strftime('%H:%M')}."

    def _tarih_yanit(self) -> str:
        now = datetime.now()
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        return f"Bugün {now.day} {aylar[now.month-1]} {now.year}."

    def tani(self, metin: str) -> str | None:
        """
        Metni tanı, basitse yerel yanıt üret.

        Returns:
            Yanıt metni (basit sorgu), veya None (9Router'a gitmeli)
        """
        if not metin:
            return None
        lower = metin.lower().strip()

        for kalip, yanit_fn in self._basit_kaliplar.items():
            if kalip in lower:
                return yanit_fn()

        return None

    def isle(self, metin: str) -> dict:
        """
        Metni işle, sonuç döndür.

        Returns:
            {"yerel": True, "yanit": str}  veya  {"yerel": False, "metin": str}
        """
        yanit = self.tani(metin)
        if yanit:
            return {"yerel": True, "yanit": yanit}
        return {"yerel": False, "metin": metin}


# Global singleton
kesici = Kesici()
