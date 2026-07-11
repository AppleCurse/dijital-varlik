# 9Router / LiteLLM üzerinden dönen reasoning modellerinin (nemotron-nano-12b-v2-vl,
# deepseek-r1 türevleri vb.) <think>...</think> bloklarını yanıta karıştırması
# 2609 token harcayıp "2" gibi anlamsız tek karakter dönmesinin muhtemel sebebi.
#
# Bu fonksiyonu 9Router bridge'inin (Python tarafı, LiteLLM'i bypass eden kod)
# yanıt işleme noktasına ekle.

import re

def reasoning_izini_temizle(ham_yanit: str) -> tuple[str, str]:
    """
    Reasoning modelinin <think>...</think> ya da benzer bloklarını ayıklar.
    Dönüş: (temiz_yanit, dusunme_izi)
    """
    # Yaygın reasoning formatları
    desenler = [
        r'<think>(.*?)</think>',
        r'<thinking>(.*?)</thinking>',
        r'<reasoning>(.*?)</reasoning>',
        r'\[THINK\](.*?)\[/THINK\]',
    ]

    dusunme_izi = ""
    temiz = ham_yanit

    for desen in desenler:
        eslesmeler = re.findall(desen, temiz, re.DOTALL | re.IGNORECASE)
        if eslesmeler:
            dusunme_izi += "\n".join(eslesmeler)
            temiz = re.sub(desen, '', temiz, flags=re.DOTALL | re.IGNORECASE)

    temiz = temiz.strip()

    # Eğer temizlik sonrası yanıt boş/aşırı kısa kaldıysa (mesela sadece "2"),
    # bu muhtemelen modelin reasoning'i TAMAMLAYAMADAN kesildiği anlamına gelir —
    # yani max_tokens çok düşük ayarlanmış olabilir, reasoning 2609 token'ı yiyip
    # gerçek cevaba sıra gelmeden kesilmiş olabilir.
    if len(temiz) < 5 and len(dusunme_izi) > 500:
        return (
            "[UYARI: max_tokens reasoning'i yarıda kesti, gerçek cevap üretilemedi]",
            dusunme_izi
        )

    return temiz, dusunme_izi


# ============================================================
# 9ROUTER BRIDGE'İNE UYGULAMA NOKTASI
# ============================================================
# Python'un 9Router'a doğrudan bağlandığı yerde (checkup'ta [3/5] adımı),
# API çağrısına şunu ekle:
#
#   response = requests.post(NINE_ROUTER_URL, json={
#       ...,
#       "max_tokens": 4096,   # reasoning modeller için önceki değer muhtemelen düşüktü
#   })
#   ham = response.json()["choices"][0]["message"]["content"]
#   temiz_cevap, izi = reasoning_izini_temizle(ham)
#
#   # temiz_cevap'ı kullanıcıya/mahkemeye gönder
#   # izi'yi (varsa) event_bus'a 'kod' kanalından debug amaçlı yayınla —
#   # komuta merkezinde KOD_AJANI panelinde reasoning süreci görünür olur.
#
# Bu hem token israfını (2609 → gerçek ihtiyaç kadar) hem de "2" gibi anlamsız
# kesilmiş yanıtları çözer.
