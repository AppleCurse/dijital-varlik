#!/usr/bin/env python3
"""
Agent Reach - Agentik Döngü Köprüsü (Tam Entegrasyon)
Tüm sosyal medya yeteneklerini ajanınıza kazandırır
"""

import os
import sys
import json
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AgentReachBridge:
    """Agent Reach ile Agentik Döngü arasında köprü"""
    
    def __init__(self):
        self.name = "Agent-Reach"
        self.ready = False
        self.channels = {}
        self._check_all_channels()
    
    def _check_all_channels(self):
        """Tüm kanalları kontrol et"""
        try:
            result = subprocess.run(
                ["agent-reach", "doctor", "--json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self.channels = data.get("channels", {})
                self.ready = True
                logger.info("✅ Agent Reach hazır")
                logger.info(f"   Kanal sayısı: {len(self.channels)}")
            else:
                self.ready = False
                logger.warning("⚠️ Agent Reach doctor çalışmadı")
        except Exception as e:
            self.ready = False
            logger.warning(f"⚠️ Agent Reach hatası: {e}")
    
    def hazir_mi(self) -> bool:
        """Agent Reach'in hazır olup olmadığını döndür"""
        return self.ready
    
    def read_url(self, url: str) -> Dict[str, Any]:
        """Web sayfasını Jina Reader ile oku"""
        try:
            import requests
            r = requests.get(f"https://r.jina.ai/{url}", timeout=15)
            if r.ok:
                return {
                    "status": "success",
                    "title": self._extract_title(r.text),
                    "content": r.text[:2000],
                    "length": len(r.text)
                }
            else:
                return {"status": "error", "message": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _extract_title(self, content: str) -> str:
        """Jina Reader çıktısından başlığı çıkar"""
        try:
            for line in content.split("\n"):
                if "Title:" in line:
                    return line.replace("Title:", "").strip()
        except:
            pass
        return "Başlık bulunamadı"
    
    def youtube_summary(self, url: str) -> Dict[str, Any]:
        """YouTube videosunu özetle"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", url],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "title": data.get("title", ""),
                    "channel": data.get("uploader", ""),
                    "duration": data.get("duration", 0),
                    "views": data.get("view_count", 0),
                    "description": data.get("description", "")[:500]
                }
            else:
                return {"status": "error", "message": result.stderr[:200]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def github_repo(self, repo: str) -> Dict[str, Any]:
        """GitHub repo bilgisi al"""
        try:
            # gh CLI ile kontrol
            result = subprocess.run(
                ["gh", "repo", "view", repo, "--json", "name,description,stargazerCount,forksCount,language"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "stars": data.get("stargazerCount", 0),
                    "forks": data.get("forksCount", 0),
                    "language": data.get("language", "Bilinmiyor")
                }
            else:
                # gh CLI yoksa API ile dene
                import requests
                r = requests.get(f"https://api.github.com/repos/{repo}", timeout=10)
                if r.ok:
                    data = r.json()
                    return {
                        "status": "success",
                        "name": data.get("name", ""),
                        "description": data.get("description", ""),
                        "stars": data.get("stargazers_count", 0),
                        "forks": data.get("forks_count", 0),
                        "language": data.get("language", "Bilinmiyor")
                    }
                return {"status": "error", "message": "Repo bulunamadı"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def rss_read(self, url: str) -> Dict[str, Any]:
        """RSS/Atom feed oku"""
        try:
            import feedparser
            feed = feedparser.parse(url)
            if feed.entries:
                return {
                    "status": "success",
                    "title": feed.feed.get("title", ""),
                    "entries": [
                        {
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "summary": entry.get("summary", "")[:200]
                        }
                        for entry in feed.entries[:5]
                    ],
                    "count": len(feed.entries)
                }
            else:
                return {"status": "error", "message": "Feed boş veya geçersiz"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """Web araması (Exa)"""
        try:
            result = subprocess.run(
                ["mcporter", "exa", "search", query],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "results": result.stdout[:1000],
                    "count": len(result.stdout.split("\n"))
                }
            else:
                # Exa yoksa, Jina ile dene
                import requests
                r = requests.get(f"https://r.jina.ai/search?q={query}", timeout=10)
                if r.ok:
                    return {
                        "status": "success",
                        "results": r.text[:1000],
                        "source": "jina-search"
                    }
                return {"status": "error", "message": result.stderr[:200]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def calistir(self, gorev: str) -> Dict[str, Any]:
        """Ana metod - görevi işle"""
        import re
        
        # 1. YouTube kontrolü
        if "youtube.com" in gorev.lower() or "youtu.be" in gorev.lower():
            url_match = re.search(r'(https?://[^\s]+)', gorev)
            if url_match:
                return self.youtube_summary(url_match.group(1))
        
        # 2. GitHub kontrolü
        if "github.com" in gorev.lower():
            repo_match = re.search(r'github\.com/([^\s/]+/[^\s/]+)', gorev)
            if repo_match:
                return self.github_repo(repo_match.group(1))
        
        # 3. RSS kontrolü
        if "rss" in gorev.lower() or "feed" in gorev.lower():
            url_match = re.search(r'(https?://[^\s]+)', gorev)
            if url_match:
                return self.rss_read(url_match.group(1))
        
        # 4. Web sayfası kontrolü
        if "http" in gorev.lower():
            url_match = re.search(r'(https?://[^\s]+)', gorev)
            if url_match:
                return self.read_url(url_match.group(1))
        
        # 5. Arama kontrolü
        if any(kw in gorev.lower() for kw in ["ara", "search", "bul", "öğren"]):
            return self.search_web(gorev)
        
        # 6. Genel
        return {
            "status": "info",
            "message": f"Agent Reach: '{gorev[:50]}...' işleniyor",
            "channels": self.channels,
            "hazir": self.ready
        }

# Singleton instance
_agent_reach_instance = None

def get_agent_reach() -> AgentReachBridge:
    """Agent Reach instance'ını döndür"""
    global _agent_reach_instance
    if _agent_reach_instance is None:
        _agent_reach_instance = AgentReachBridge()
    return _agent_reach_instance
