import time
from enum import Enum

class GorevTipi(Enum):
    WEB = "web"
    MASAUSTU = "masaustu"
    ANALIZ = "analiz"
    KOD = "kod"
    SORU = "soru"
    ISTIHBARAT = "istihbarat"

def old_func(gorev: str):
    g = gorev.lower()

    web_keywords = ["site", "web", "tarayici", "browser", "http", "tikla",
                    "sayfa", "form", "indir", "download", "url", "link",
                    "ekran goruntusu", "screenshot", "gez", "dolas"]
    masaustu_keywords = ["excel", "word", "dosya", "klasor", "fare", "klavye",
                         "masaustu", "pencere", "kaydet", "notepad",
                         "hesap makinesi", "cmd", "powershell", "agent s"]
    analiz_keywords = ["analiz", "rapor", "ozetle", "karsilastir", "istatistik",
                       "grafik", "tablo", "veri", "arastir", "incele"]
    istihbarat_keywords = ["gundem", "haber", "sosyal medya", "tara", "twitter",
                           "reddit", "tiktok", "instagram", "trend", "viral",
                           "sentiment", "duygu analizi", "public opinion"]
    kod_keywords = ["kod", "python", "script", "hesapla", "fonksiyon",
                    "program", "debug", "fix", "duzelt"]

    scores = {
        GorevTipi.WEB: sum(1 for kw in web_keywords if kw in g),
        GorevTipi.MASAUSTU: sum(1 for kw in masaustu_keywords if kw in g),
        GorevTipi.ANALIZ: sum(1 for kw in analiz_keywords if kw in g),
        GorevTipi.KOD: sum(1 for kw in kod_keywords if kw in g),
        GorevTipi.ISTIHBARAT: sum(1 for kw in istihbarat_keywords if kw in g),
    }

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return GorevTipi.SORU
    return best

_WEB_KEYWORDS = ("site", "web", "tarayici", "browser", "http", "tikla",
                 "sayfa", "form", "indir", "download", "url", "link",
                 "ekran goruntusu", "screenshot", "gez", "dolas")
_MASAUSTU_KEYWORDS = ("excel", "word", "dosya", "klasor", "fare", "klavye",
                      "masaustu", "pencere", "kaydet", "notepad",
                      "hesap makinesi", "cmd", "powershell", "agent s")
_ANALIZ_KEYWORDS = ("analiz", "rapor", "ozetle", "karsilastir", "istatistik",
                    "grafik", "tablo", "veri", "arastir", "incele")
_ISTIHBARAT_KEYWORDS = ("gundem", "haber", "sosyal medya", "tara", "twitter",
                        "reddit", "tiktok", "instagram", "trend", "viral",
                        "sentiment", "duygu analizi", "public opinion")
_KOD_KEYWORDS = ("kod", "python", "script", "hesapla", "fonksiyon",
                 "program", "debug", "fix", "duzelt")

def new_func(gorev: str):
    g = gorev.lower()

    scores = {
        GorevTipi.WEB: sum(1 for kw in _WEB_KEYWORDS if kw in g),
        GorevTipi.MASAUSTU: sum(1 for kw in _MASAUSTU_KEYWORDS if kw in g),
        GorevTipi.ANALIZ: sum(1 for kw in _ANALIZ_KEYWORDS if kw in g),
        GorevTipi.KOD: sum(1 for kw in _KOD_KEYWORDS if kw in g),
        GorevTipi.ISTIHBARAT: sum(1 for kw in _ISTIHBARAT_KEYWORDS if kw in g),
    }

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return GorevTipi.SORU
    return best

texts = [
    "lutfen excel dosyasini ac",
    "bu bir analiz raporudur",
    "bana python scripti yaz",
    "saat kac",
    "browser ac"
]

start = time.time()
for _ in range(100000):
    for t in texts:
        old_func(t)
old_time = time.time() - start

start = time.time()
for _ in range(100000):
    for t in texts:
        new_func(t)
new_time = time.time() - start

print(f"Old time: {old_time:.4f}s")
print(f"New time: {new_time:.4f}s")
print(f"Improvement: {(old_time - new_time) / old_time * 100:.2f}%")