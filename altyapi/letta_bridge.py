"""
Letta Bridge - Oturum ve Bagcam Yonetimi
Lokal dosya tabanli hafif implementasyon
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


class LettaBridge:
    """
    Letta alternatifi - Dosya tabanli oturum ve baglam yonetimi.
    Aspasia'nin kullanici ozelinde durum takibi icin kullanilir.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            base_dir = Path(__file__).parent.parent
            storage_path = base_dir / "bellek" / "letta_sessions.json"
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Aktif oturum
        self.active_session: Optional[str] = None
        self.session_data: Dict = {}
        
        # Yukle
        self._yukle()
    
    def _yukle(self):
        """Tum oturumlari yukle"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.session_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.session_data = {}
        else:
            self.session_data = {}
    
    def _kaydet(self):
        """Tum oturumlari diske kaydet"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Letta kaydet hatasi: {e}")
    
    def oturum_baslat(self, agent_adi: str, kullanici_id: Optional[str] = None) -> str:
        """
        Yeni oturum baslat veya mevcut oturumu getir.
        
        Args:
            agent_adi: Agent adi (orn. "aspasia")
            kullanici_id: Kullanici ID (opsiyonel)
            
        Returns:
            Session ID
        """
        session_id = f"{agent_adi}_{kullanici_id or 'default'}"
        
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": [],
                "context": {},
                "metadata": {
                    "agent": agent_adi,
                    "user": kullanici_id
                }
            }
        
        self.active_session = session_id
        self._kaydet()
        
        return session_id
    
    def oturum_getir(self, session_id: str) -> Optional[Dict]:
        """
        Oturum bilgilerini getir.
        
        Args:
            session_id: Oturum ID
            
        Returns:
            Oturum verisi veya None
        """
        return self.session_data.get(session_id)
    
    def mesaj_ekle(self, rol: str, icerik: str, metadata: Optional[Dict] = None) -> bool:
        """
        Mesaji aktif oturuma ekle.
        
        Args:
            rol: Mesaj rolu (user, assistant, system)
            icerik: Mesaj icerigi
            metadata: Ek meta veriler
            
        Returns:
            Basari durumu
        """
        if not self.active_session:
            print("Letta: Aktif oturum yok")
            return False
        
        mesaj = {
            "role": rol,
            "content": icerik,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.session_data[self.active_session]["messages"].append(mesaj)
        self.session_data[self.active_session]["updated_at"] = datetime.now().isoformat()
        
        self._kaydet()
        return True
    
    def context_guncelle(self, anahtar: str, deger: Any) -> bool:
        """
        Oturum context'ini guncelle.
        
        Args:
            anahtar: Context anahtari
            deger: Deger
            
        Returns:
            Basari durumu
        """
        if not self.active_session:
            print("Letta: Aktif oturum yok")
            return False
        
        self.session_data[self.active_session]["context"][anahtar] = deger
        self.session_data[self.active_session]["updated_at"] = datetime.now().isoformat()
        
        self._kaydet()
        return True
    
    def get_context(self) -> Dict:
        """
        Aktif oturumun context'ini getir.
        
        Returns:
            Context sozlugu
        """
        if not self.active_session:
            return {}
        
        return self.session_data[self.active_session].get("context", {})
    
    def agent_durumu_kaydet(self, durum: Dict) -> bool:
        """
        Agent durumunu kaydet.
        
        Args:
            durum: Agent durum verisi
            
        Returns:
            Basari durumu
        """
        if not self.active_session:
            print("Letta: Aktif oturum yok")
            return False
        
        self.session_data[self.active_session]["agent_state"] = durum
        self.session_data[self.active_session]["updated_at"] = datetime.now().isoformat()
        
        self._kaydet()
        return True
    
    def gecmis_al(self, limit: int = 50) -> List[Dict]:
        """
        Son mesajlari getir.
        
        Args:
            limit: Maksimum mesaj sayisi
            
        Returns:
            Mesaj listesi
        """
        if not self.active_session:
            return []
        
        messages = self.session_data[self.active_session].get("messages", [])
        return messages[-limit:]
    
    def oturum_sil(self, session_id: str) -> bool:
        """
        Oturumu sil.
        
        Args:
            session_id: Oturum ID
            
        Returns:
            Basari durumu
        """
        if session_id in self.session_data:
            del self.session_data[session_id]
            self._kaydet()
            
            if self.active_session == session_id:
                self.active_session = None
            
            return True
        
        return False
    
    def tum_oturumlar(self) -> List[str]:
        """
        Tum oturum ID'lerini dondur.
        
        Returns:
            Session ID listesi
        """
        return list(self.session_data.keys())
    
    def istatistik(self) -> Dict:
        """Oturum istatistikleri"""
        total_messages = sum(
            len(s.get("messages", [])) 
            for s in self.session_data.values()
        )
        
        return {
            "total_sessions": len(self.session_data),
            "total_messages": total_messages,
            "active_session": self.active_session,
            "storage_path": str(self.storage_path)
        }


# Singleton instance
_letta_instance: Optional[LettaBridge] = None

def get_letta() -> LettaBridge:
    """Letta instance'ini al veya olustur"""
    global _letta_instance
    if _letta_instance is None:
        _letta_instance = LettaBridge()
    return _letta_instance
