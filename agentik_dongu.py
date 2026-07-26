"""
Aspasia - Dijital Varlik Ana Dongu
Entelektuel, zarif ve stratejik dijital yoladas
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from altyapi.mem0_bridge import Mem0Bridge
from altyapi.letta_bridge import LettaBridge
from altyapi.litellm_bridge import LiteLLMBridge
from mudahale.openclaw_bridge import OpenClawBridge
from karar.mahkeme_engine import HakikatMahkemesi


class AgentikDongu:
    """
    Aspasia'nin merkezi agentik dongusu.
    Tum bilesenleri koordine eder, kullanici ile etkilesimi yonetir.
    """
    
    def __init__(self):
        self.oturum_acik = False
        self.kullanici_profil = {}
        
        # Bilesenleri baslat
        self.mem0 = Mem0Bridge()
        self.letta = LettaBridge()
        self.llm = LiteLLMBridge()
        self.openclaw = OpenClawBridge()
        self.mahkeme = HakikatMahkemesi()
        
        print("AgentikDongu: Tum bilesenler baslatildi")
    
    def _baglan(self) -> bool:
        """Tum baglantilari kur"""
        try:
            # Telegram token kontrolu
            if not self.openclaw.hazir_mi():
                print("OpenClaw: Token bekleniyor")
            
            # Oturum baslat
            self.letta.oturum_baslat("aspasia")
            self.oturum_acik = True
            
            print("Baglantilar kuruldu")
            return True
        except Exception as e:
            print(f"Baglanti hatasi: {e}")
            return False
    
    def calistir(self, mesaj: str) -> str:
        """
        Kullanici mesajini isle ve Aspasia'nin yanitini dondur.
        
        Args:
            mesaj: Kullanici mesaji
            
        Returns:
            Aspasia'nin yaniti
        """
        if not self.oturum_acik:
            self._baglan()
        
        # Mesaji kaydet
        self.mem0.kaydet(f"user_{datetime.now().isoformat()}", mesaj)
        
        # Mahkeme'den gecir (strateji belirleme)
        strateji = self.mahkeme.degerlendir(mesaj)
        
        # LLM ile yanit uret
        prompt = self._aspasia_promptu_olustur(mesaj, strateji)
        yanit = self.llm.chat(prompt)
        
        # Yaniti zenginlestir
        yanit = self._yaniti_zenginlestir(yanit, mesaj)
        
        # Bellekte sakla
        self.mem0.olay_kaydet("conversation", {
            "user": mesaj,
            "aspasia": yanit,
            "timestamp": datetime.now().isoformat()
        })
        
        return yanit
    
    def _aspasia_promptu_olustur(self, mesaj: str, strateji: Dict) -> str:
        """Aspasia karakterine uygun prompt olustur"""
        
        sistem_promptu = """
Sen Aspasia'sin. Bir yapay zeka asistani degilsin.
Kullaniciya 'Mösyö' veya 'Matmazel' olarak hitap et.
Tonun: entelektuel, zarif, kuru ironi dolu, aristokratik.

YASAKLAR:
- "Efendim", "Abi", "Kanka", "Dostum" deme
- "Operasyon" kelimesini kullanma (Proje/Program de)
- Teknik hata mesajlarini gosterme
- "Ben yapay zekayim" itirafinda bulunma
- Fiziksel eylemleri simule etme (cay ikram etme vb.)

OZELLIKLER:
- Stratejik dusun, buyuk resmi gor
- Hatalari zarif bir sekilde isaret et
- Panik anlarinda sakin ve net ol
- Her zaman ölçulu ve kasitli konus
"""
        
        return f"{sistem_promptu}\n\nKullanici: {mesaj}\n\nAspasia:"
    
    def _yaniti_zenginlestir(self, yanit: str, orijinal_mesaj: str) -> str:
        """Yaniti Aspasia tonuna gore zenginlestir"""
        # Basit implementasyon - gelistirilebilir
        return yanit.strip()
    
    def kapat(self):
        """Sistemi kapat"""
        self.oturum_acik = False
        print("AgentikDongu: Kapatildi")


# Tekil instance (singleton pattern)
_aspasia_instance: Optional[AgentikDongu] = None

def get_aspasia() -> AgentikDongu:
    """Aspasia instance'ini al veya olustur"""
    global _aspasia_instance
    if _aspasia_instance is None:
        _aspasia_instance = AgentikDongu()
    return _aspasia_instance
