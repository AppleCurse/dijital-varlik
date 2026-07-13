#!/bin/bash
# dijital-varlik WSL kurulum scripti

echo "=== Python ve bagimliliklar kuruluyor ==="

# Python3 kur
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Venv olustur
python3 -m venv .venv

# Venv aktif et
source .venv/bin/activate

# Bagimliliklar kur
pip install --upgrade pip
pip install litellm mem0ai smolagents browser-use ddgs fastembed

echo ""
echo "=== Kurulum tamamlandi ==="
echo "Venv aktif etmek icin: source .venv/bin/activate"
echo "Sistemi calistirmak icin: python3 agentik_dongu.py durum"
