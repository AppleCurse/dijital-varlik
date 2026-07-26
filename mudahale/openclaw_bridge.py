"""
OpenClaw Bridge - Telegram Entegrasyonu
Aspasia'nin WhatsApp alternatifi olarak Telegram uzerinden erisim
"""

import os
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime


class OpenClawBridge:
    """
    Telegram Bot entegrasyonu.
    Aspasia'nin kullanici ile iletisim kanali.
    """
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.bot_id: Optional[str] = None
        self.username: Optional[str] = None
        self.webhook_url: Optional[str] = None
        self._message_handler: Optional[Callable] = None
        
        # Bot bilgilerini yukle
        if self.token:
            self._bot_info_yukle()
    
    def _bot_info_yukle(self):
        """Bot bilgilerini Telegram API'den cek"""
        try:
            import urllib.request
            
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.token}/getMe",
                method='GET'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('ok'):
                    result = data['result']
                    self.bot_id = result['id']
                    self.username = result['username']
                    print(f"OpenClaw: Bot @{self.username} aktif")
        except Exception as e:
            print(f"OpenClaw: Bot info yukleme hatasi: {e}")
    
    def hazir_mi(self) -> bool:
        """Bot kullanima hazir mi?"""
        return bool(self.token and self.username)
    
    def token_set(self, yeni_token: str) -> bool:
        """
        Yeni token ayarla.
        
        Args:
            yeni_token: Telegram bot token
            
        Returns:
            Basari durumu
        """
        self.token = yeni_token
        self._bot_info_yukle()
        return self.hazir_mi()
    
    def telegram_baslat(self, webhook_url: Optional[str] = None) -> bool:
        """
        Telegram bot'u baslat.
        
        Args:
            webhook_url: Webhook URL (opsiyonel, polling icin gerek yok)
            
        Returns:
            Basari durumu
        """
        if not self.hazir_mi():
            print("OpenClaw: Token yok, bot baslatilamadi")
            return False
        
        if webhook_url:
            # Webhook kur
            return self._webhook_kur(webhook_url)
        else:
            print("OpenClaw: Polling mode - manuel polling gerekiyor")
            return True
    
    def _webhook_kur(self, url: str) -> bool:
        """Webhook kurulumu"""
        try:
            import urllib.request
            
            payload = {"url": url}
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.token}/setWebhook",
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('ok', False)
                
        except Exception as e:
            print(f"OpenClaw: Webhook kurma hatasi: {e}")
            return False
    
    def mesaj_gonder(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Telegram mesaji gonder.
        
        Args:
            chat_id: Hedef chat ID
            text: Mesaj metni
            parse_mode: Format (Markdown, HTML)
            
        Returns:
            Basari durumu
        """
        if not self.hazir_mi():
            return False
        
        try:
            import urllib.request
            
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('ok', False)
                
        except Exception as e:
            print(f"OpenClaw: Mesaj gonderme hatasi: {e}")
            return False
    
    def mesaj_isleyici_ayarla(self, handler: Callable):
        """
        Mesaj isleyici fonksiyonu ayarla.
        
        Args:
            handler: Fonksiyon(update, context)
        """
        self._message_handler = handler
    
    def polling_baslat(self):
        """
        Manuel polling baslat (long polling).
        Not: Gercek zamanli polling icin loop gerekir.
        """
        if not self.hazir_mi():
            print("OpenClaw: Token yok, polling baslatilamadi")
            return
        
        print(f"OpenClaw: @{self.username} icin polling hazir")
        # Gercek polling implementasyonu ici loop gerekir
    
    def durdur(self):
        """Bot'u durdur (webhook sil)"""
        if not self.hazir_mi():
            return
        
        try:
            import urllib.request
            
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.token}/deleteWebhook",
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"OpenClaw: Webhook silindi: {data.get('ok')}")
                
        except Exception as e:
            print(f"OpenClaw: Durdurma hatasi: {e}")
    
    def durum(self) -> Dict:
        """Bot durumunu dondur"""
        return {
            "token_set": bool(self.token),
            "username": self.username,
            "bot_id": self.bot_id,
            "ready": self.hazir_mi(),
            "webhook": self.webhook_url
        }


# Singleton instance
_openclaw_instance: Optional[OpenClawBridge] = None

def get_openclaw() -> OpenClawBridge:
    """OpenClaw instance'ini al veya olustur"""
    global _openclaw_instance
    if _openclaw_instance is None:
        _openclaw_instance = OpenClawBridge()
    return _openclaw_instance
