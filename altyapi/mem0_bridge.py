"""Mem0 semantik bellek bridge'i"""
import os
import json
from pathlib import Path
from datetime import datetime

class Mem0Bridge:
    def __init__(self, data_dir: str = "./altyapi/mem0_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "memory_store.jsonl"
        self.event_file = self.data_dir / "events.jsonl"
        self._ready = True

    def hazir_mi(self):
        return self._ready

    def hatirla(self, query: str, limit: int = 5, top_k: int = None):
        if top_k is not None:
            limit = top_k
        results = []
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if query.lower() in data.get("content", "").lower():
                                results.append(data)
                        except:
                            continue
            except:
                pass
        return results[:limit]

    def kaydet(self, content: str, metadata: dict = None):
        entry = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        try:
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except:
            return False

    def olay_kaydet(self, aciklama: str, tip: str = "bilgi", seviye: str = "info"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tip": tip,
            "seviye": seviye,
            "aciklama": aciklama
        }
        try:
            with open(self.event_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except:
            return False

def get_mem0():
    return Mem0Bridge()
