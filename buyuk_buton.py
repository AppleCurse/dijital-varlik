#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basit Büyük Buton Uygulaması
Tam ekran benzeri büyük bir buton, mouse ile tıklayınca tepki verir.
"""

import sys
import tkinter as tk
from tkinter import messagebox

def on_button_click():
    """Butona tıklandığında çalışır."""
    print("✅ BUTONA TIKLANDI!")
    # Konsola da yaz, kullanıcıya bildir
    try:
        messagebox.showinfo("Başarılı", "🎉 Butona başarıyla tıkladınız!")
    except:
        pass  # Bazı ortamlarda messagebox çalışmayabilir

def main():
    # Ana pencere
    root = tk.Tk()
    root.title("Dijital Varlık - Basit Buton")
    # Pencereyi büyük yap
    root.geometry("800x600")  # Genişlik x Yükseklik
    root.configure(bg="#1a1a1a")  # Koyu arkaplan

    # Pencereyi ortalamaya çalış
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # Başlık etiketi
    label = tk.Label(
        root,
        text="BUTONU TIKLAYIN",
        font=("Arial", 28, "bold"),
        fg="#00ff00",
        bg="#1a1a1a"
    )
    label.pack(pady=50)

    # Büyük buton
    button = tk.Button(
        root,
        text="TIKLA",
        font=("Arial", 48, "bold"),
        bg="#006600",
        fg="white",
        activebackground="#009900",
        activeforeground="white",
        width=12,
        height=3,
        cursor="hand2",
        relief="raised",
        bd=5,
        command=on_button_click
    )
    button.pack(pady=80)

    # Alt bilgi
    info = tk.Label(
        root,
        text="Mouse ile bu butona tıklayın",
        font=("Arial", 14),
        fg="#888888",
        bg="#1a1a1a"
    )
    info.pack(pady=30)

    # Kapat butonu (küçük)
    close_btn = tk.Button(
        root,
        text="Kapat (X)",
        font=("Arial", 10),
        bg="#660000",
        fg="white",
        command=root.quit
    )
    close_btn.pack(side="bottom", pady=20)

    print("✅ Uygulama başlatıldı. Pencereyi görmelisiniz.")
    print("   Büyük yeşil butona mouse ile tıklayın.")
    print("   Pencereyi kapatmak için altındaki 'Kapat (X)' butonunu kullanın.")

    # Tkinter mainloop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nUygulama kapatıldı.")
        sys.exit(0)

if __name__ == "__main__":
    main()