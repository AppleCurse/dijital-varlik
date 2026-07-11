#!/usr/bin/env python3
"""
event_bus.py'nin GERÇEK API'sini çıkarır — main.py'yi buna göre yazacağım.
Çalıştır: cd /home/administrator/dijital-varlik && source .venv/bin/activate && python3 teshis_event_bus.py
Çıktıyı olduğu gibi yapıştır.
"""
import runtime.event_bus as eb
import runtime.events as ev

print("=== BUS NESNESİNİN METOD/ATTRİBUTE LİSTESİ ===")
print([x for x in dir(eb.bus) if not x.startswith('_')])

print("\n=== EVENTS.PY İÇİNDEKİ TÜM OLAY TİPLERİ ===")
print([x for x in dir(ev) if not x.startswith('_')])

print("\n=== HISTORY'DEN ÖRNEK OLAY (varsa) ===")
if hasattr(eb.bus, 'history') and len(eb.bus.history) > 0:
    ornek = eb.bus.history[-1]
    print(f"Tip: {type(ornek)}")
    print(f"İçerik: {ornek}")
    if hasattr(ornek, '__dict__'):
        print(f"Alanlar: {ornek.__dict__}")
else:
    print("History boş, yeni bir olay tetikleyip tekrar dene (örn: bir komut çalıştır).")

print("\n=== SUBSCRIBE/ON BENZERİ METODLARIN İMZASI ===")
import inspect
for isim in ['subscribe', 'on', 'listen', 'register', 'add_listener']:
    if hasattr(eb.bus, isim):
        try:
            print(f"{isim}{inspect.signature(getattr(eb.bus, isim))}")
        except Exception as e:
            print(f"{isim}: imza alınamadı ({e})")
