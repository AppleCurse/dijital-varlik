"""
Firecrawl Bridge — Profesyonel Web Kazima ve Arama.

BrowserUse'un yerine gecer: 10x hizli, markdown cikti, API tabanli.
Self-host veya cloud API ile calisir.

Kullanim:
    from mudahale.firecrawl_bridge import get_firecrawl
    fc = get_firecrawl()
    fc.scrape("https://example.com")  → markdown
    fc.search("python haberleri")     → sonuclar
"""
import os, json
from typing import Optional


class FirecrawlBridge:
    """Firecrawl web kazima ve arama motoru."""

    def __init__(self):
        self._ready = False
        self._client = None
        self._api_key = os.getenv("FIRECRAWL_API_KEY", "")
        if self._api_key:
            self._init_client()

    def _init_client(self):
        try:
            from firecrawl import FirecrawlApp
            self._client = FirecrawlApp(api_key=self._api_key)
            self._ready = True
        except Exception as e:
            print(f"[Firecrawl] Init hatasi: {e}")
            self._ready = False

    def set_api_key(self, key: str):
        self._api_key = key
        self._init_client()

    def hazir_mi(self) -> bool:
        if not self._ready and self._api_key:
            self._init_client()
        return self._ready

    def scrape(self, url: str) -> dict:
        """URL'yi kazi, markdown dondur."""
        if not self._ready:
            return {"status": "error", "message": "FIRECRAWL_API_KEY gerekli."}
        try:
            result = self._client.scrape_url(url, formats=["markdown"])
            title = ""
            if result.metadata:
                try: title = result.metadata.get("title", "")
                except: title = getattr(result.metadata, "title", "")
            return {"status": "ok",
                    "markdown": result.markdown[:5000] if result.markdown else "",
                    "title": title,
                    "url": url}
        except Exception as e:
            return {"status": "error", "message": str(e)[:300]}

    def search(self, query: str, limit: int = 5) -> dict:
        """Web'de arama yap."""
        if not self._ready:
            return {"status": "error", "message": "FIRECRAWL_API_KEY gerekli."}
        try:
            result = self._client.search(query, limit=limit)
            items = []
            for r in (result.get("data", []) if isinstance(result, dict) else [])[:limit]:
                items.append({"title": r.get("title", ""), "url": r.get("url", ""),
                              "description": r.get("description", "")[:300]})
            return {"status": "ok", "results": items, "count": len(items)}
        except Exception as e:
            return {"status": "error", "message": str(e)[:300]}

    def crawl(self, url: str, max_pages: int = 10) -> dict:
        """Siteyi tara."""
        if not self._ready:
            return {"status": "error", "message": "FIRECRAWL_API_KEY gerekli."}
        try:
            result = self._client.crawl_url(url, limit=max_pages,
                                            scrape_options={"formats": ["markdown"]})
            return {"status": "ok", "pages": result.get("data", [])[:max_pages] if isinstance(result, dict) else [],
                    "total": result.get("total", 0) if isinstance(result, dict) else 0}
        except Exception as e:
            return {"status": "error", "message": str(e)[:300]}

    def calistir(self, gorev: str) -> dict:
        """BrowserUse uyumlu arayuz. 'url' veya 'ara:kelime' formatinda."""
        g = gorev.strip()
        if g.startswith("http"):
            return self.scrape(g)
        elif g.startswith("ara:") or g.startswith("search:"):
            query = g.split(":", 1)[1].strip()
            return self.search(query)
        elif g.startswith("tara:") or g.startswith("crawl:"):
            url = g.split(":", 1)[1].strip()
            return self.crawl(url)
        else:
            return self.search(g)


_firecrawl: Optional[FirecrawlBridge] = None

def get_firecrawl() -> FirecrawlBridge:
    global _firecrawl
    if _firecrawl is None:
        _firecrawl = FirecrawlBridge()
    return _firecrawl
