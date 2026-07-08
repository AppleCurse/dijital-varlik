"""Letta kalıcı durum bridge'i"""
import json
from pathlib import Path
from datetime import datetime

class LettaBridge:
    def __init__(self, data_dir: str = "./altyapi/letta_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.data_dir / "session.json"
        self._ready = True
        self._load_session()

    def _load_session(self):
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    self.session = json.load(f)
            except:
                self.session = {"history": [], "created": datetime.now().isoformat()}
        else:
            self.session = {"history": [], "created": datetime.now().isoformat()}

    def _save_session(self):
        with open(self.session_file, 'w') as f:
            json.dump(self.session, f, indent=2)

    def hazir_mi(self):
        return self._ready

    def oturum_baslat(self, session_id: str, metadata: dict = None):
        self.session["session_id"] = session_id
        self.session["metadata"] = metadata or {}
        self.session["started"] = datetime.now().isoformat()
        self.session["history"] = []
        self._save_session()
        return True

    def oturum_kapat(self, session_id: str = None, metadata: dict = None):
        self.session["closed_at"] = datetime.now().isoformat()
        if session_id:
            self.session["session_id"] = session_id
        if metadata:
            self.session.setdefault("close_metadata", {}).update(metadata)
        self.session["active"] = False
        self._save_session()
        return True

    def agent_durumu_kaydet(self, session_id: str, durum: dict):
        entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "durum": durum
        }
        self.session.setdefault("agent_durumlari", []).append(entry)
        self.session["session_id"] = session_id
        self._save_session()
        return True

    def guncelle(self, context: str):
        self.session["history"].append({
            "timestamp": datetime.now().isoformat(),
            "context": context[:500]
        })
        self._save_session()

    def get_context(self):
        if self.session["history"]:
            return self.session["history"][-1].get("context", "")
        return ""

def get_letta():
    return LettaBridge()
