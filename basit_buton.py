#!/usr/bin/env python3
"""
Basit Tıklanabilir Buton Uygulaması
Tamamen karşıda duran büyük bir buton, mouse ile tıklayınca tepki verir.
"""
import tkinter as tk
from tkinter import messagebox

def buton_tiklandi():
    """Butona tıklandığında çalışır."""
    print("✅ BUTONA TIKLANDI!")
    messagebox.showinfo("Tıklandı", "🎉 Butona başarıyla tıkladınız!")

# Ana pencere oluştur
pencere = tk.Tk()
pencere.title("Basit Buton Uygulaması")
pencere.geometry("400x300")
pencere.configure(bg="#2c3e50")

# Başlık etiketi
baslik = tk.Label(
    pencere,
    text="Aşağıdaki Butona Tıklayın",
    font=("Arial", 16, "bold"),
    fg="white",
    bg="#2c3e50"
)
baslik.pack(pady=30)

# Büyük tıklanabilir buton
buton = tk.Button(
    pencere,
    text="TIKLA",
    command=buton_tiklandi,
    font=("Arial", 24, "bold"),
    bg="#27ae60",
    fg="white",
    activebackground="#2ecc71",
    activeforeground="white",
    width=15,
    height=3,
    cursor="hand2"
)
buton.pack(pady=40)

# Çıkış butonu
cikis = tk.Button(
    pencere,
    text="Kapat",
    command=pencere.quit,
    font=("Arial", 10),
    bg="#e74c3c",
    fg="white",
    width=10
)
cikis.pack(pady=10)

print("✅ Uygulama başlatıldı. Pencereyi kapatmak için 'Kapat' butonuna tıklayın.")
pencere.mainloop()
