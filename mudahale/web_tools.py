"""
smolagents için web araçları — browser-use Agent üzerinden (Faz 3).
Eski browserless HTTP API çağrıları yerini browser-use CDP tabanlı Agent'a bıraktı.
Tıklama, form doldurma, gezinme, içerik çekme dahil tam tarayıcı kontrolü.

CodeAgent bu araçları kullanarak web sayfalarını ziyaret eder.
"""
import re
import base64
from smolagents import tool

from mudahale.browser_use_bridge import get_browser_use
from config.config import config


def _browser_use_calistir(gorev: str) -> str:
    """browser-use Agent ile bir görev çalıştır, hata durumunda mesaj döndür."""
    bridge = get_browser_use()
    if not bridge.hazir_mi():
        return "HATA: browser-use Agent hazır değil."

    sonuc = bridge.calistir(gorev)
    if sonuc is None:
        return "HATA: browser-use Agent çalıştırılamadı."
    return sonuc


@tool
def web_fetch(url: str) -> str:
    """
    Bir web sayfasını browser-use Agent ile açar ve içeriğini/tanımını döndürür.
    Agent tam tarayıcı kontrolüne sahiptir — JavaScript render edilmiş içeriği okur.

    Args:
        url: Açılacak web sayfası URL'i (örn: https://example.com)

    Returns:
        Sayfanın içeriği ve başlığı
    """
    gorev = (
        f"Go to {url} and tell me:\n"
        f"1. The page title\n"
        f"2. A brief description of what this page is about (2-3 sentences)\n"
        f"Return the result in this format: TITLE: <title> | DESCRIPTION: <description>"
    )
    return _browser_use_calistir(gorev)


@tool
def web_extract_title(url_or_html: str) -> str:
    """
    Bir web sayfasının başlığını (<title>) browser-use Agent ile çıkarır.
    URL verilirse sayfayı açar, HTML verilirse içinden başlığı regex ile çıkarır.

    Args:
        url_or_html: URL (örn: https://example.com) veya HTML içeriği

    Returns:
        Sayfa başlığı
    """
    # HTML içeriği verilmişse regex ile hızlıca çıkar (eski davranış)
    if url_or_html.strip().startswith("<") or "DOCTYPE" in url_or_html[:200]:
        match = re.search(r'<title[^>]*>(.*?)</title>', url_or_html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "BAŞLIK BULUNAMADI"

    # URL verilmişse browser-use ile sayfayı aç
    gorev = (
        f"Go to {url_or_html} and extract ONLY the page title from the <title> tag. "
        f"Return just the title text, nothing else."
    )
    return _browser_use_calistir(gorev)


@tool
def web_screenshot(url: str) -> str:
    """
    Bir web sayfasının ekran görüntüsünü alır.
    browser-use Agent sayfayı açar ve görüntüyü yakalar.

    Args:
        url: Görüntüsü alınacak URL

    Returns:
        Ekran görüntüsü bilgisi (base64 kodlu PNG)
    """
    gorev = (
        f"Go to {url}, take a screenshot, and describe what you see on the page. "
        f"Return a detailed description of the page content and layout."
    )
    return _browser_use_calistir(gorev)


@tool
def web_navigate(url: str, action: str = "describe") -> str:
    """
    Bir web sayfasında browser-use Agent ile karmaşık bir eylem gerçekleştirir.
    Tıklama, form doldurma, arama yapma gibi işlemleri destekler.

    Args:
        url: Hedef URL
        action: Yapılacak eylem (örn: "search for X", "click the login button",
                "fill the form with name=John email=john@test.com", "describe")

    Returns:
        Eylemin sonucu
    """
    if action == "describe":
        gorev = f"Go to {url} and describe what you see on the page in detail."
    else:
        gorev = f"Go to {url} and {action}. Return the result clearly."
    return _browser_use_calistir(gorev)
