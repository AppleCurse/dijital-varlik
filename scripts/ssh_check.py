"""
EC2 SSH baglanti testi.
dijital-varlik Faz 4 — EC2'ye deploy oncesi baglanti kontrolu.
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config.config import config


def check_ssh():
    """EC2'ye SSH baglantisini test et ve docker ps calistir."""
    try:
        from paramiko import SSHClient, AutoAddPolicy
    except ImportError:
        print("HATA: paramiko kurulu degil. pip install paramiko")
        return False

    key_path = os.path.expanduser(config.SSH_KEY_PATH)
    if not os.path.exists(key_path):
        print(f"HATA: SSH anahtari bulunamadi: {key_path}")
        print("Alternatif anahtarlar deneniyor...")
        for alt in ["~/.ssh/id_ed25519", "~/.ssh/id_ecdsa"]:
            alt_path = os.path.expanduser(alt)
            if os.path.exists(alt_path):
                key_path = alt_path
                print(f"  Bulundu: {key_path}")
                break
        else:
            print("  Hicbir SSH anahtari bulunamadi.")
            return False

    print(f"Baglaniliyor: {config.EC2_USER}@{config.EC2_HOST}:{config.SSH_PORT}")
    print(f"Anahtar: {key_path}")

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())

    try:
        client.connect(
            hostname=config.EC2_HOST,
            port=config.SSH_PORT,
            username=config.EC2_USER,
            key_filename=key_path,
            timeout=10,
        )
        print("✅ SSH baglantisi basarili!")

        # Docker durumunu kontrol et
        _, stdout, _ = client.exec_command(
            'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "docker calismiyor"'
        )
        docker_out = stdout.read().decode().strip()
        print(f"\nEC2 Docker Konteynerleri:\n{docker_out}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Baglanti basarisiz: {e}")
        return False


if __name__ == "__main__":
    success = check_ssh()
    sys.exit(0 if success else 1)
