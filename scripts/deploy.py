"""
EC2 Deploy araci.
dijital-varlik Faz 4 — Kod ve konfigurasyonu EC2'ye tasir, servis durumunu kontrol eder.

Kullanim:
  python scripts/deploy.py check       SSH baglanti testi
  python scripts/deploy.py status      EC2 servis saglik kontrolu
  python scripts/deploy.py litellm     LiteLLM docker-compose deploy
  python scripts/deploy.py config      .env dosyasini EC2'ye kopyala
  python scripts/deploy.py grounding   UI-TARS grounding model deploy (vLLM)
  python scripts/deploy.py all         Tum adimlari calistir
"""
import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config.config import config


def _get_ssh_client():
    """Paramiko SSH istemcisi olustur."""
    from paramiko import SSHClient, AutoAddPolicy

    key_path = os.path.expanduser(config.SSH_KEY_PATH)
    for alt in ["~/.ssh/id_ed25519", "~/.ssh/id_ecdsa"]:
        if not os.path.exists(key_path):
            alt_path = os.path.expanduser(alt)
            if os.path.exists(alt_path):
                key_path = alt_path

    if not os.path.exists(key_path):
        raise FileNotFoundError(f"SSH anahtari bulunamadi: {key_path}")

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(
        hostname=config.EC2_HOST,
        port=config.SSH_PORT,
        username=config.EC2_USER,
        key_filename=key_path,
        timeout=15,
    )
    return client


def _run_remote(cmd: str, timeout: int = 30) -> tuple[str, str]:
    """EC2'de komut calistir, (stdout, stderr) dondur."""
    client = _get_ssh_client()
    try:
        _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err
    finally:
        client.close()


def cmd_check():
    """SSH baglanti testi."""
    print(f"SSH baglanti testi: {config.EC2_USER}@{config.EC2_HOST}")
    try:
        out, err = _run_remote("echo 'baglanti basarili' && hostname && uptime -p")
        print(f"✅ Baglanti basarili!\n{out}")
        if err:
            print(f"stderr: {err}")
        return True
    except Exception as e:
        print(f"❌ Baglanti basarisiz: {e}")
        return False


def cmd_status():
    """EC2 servis saglik kontrolu."""
    print(f"EC2 Servis Durumu: {config.EC2_HOST}")
    print("=" * 55)

    checks = {
        "LiteLLM": f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:4000/health 2>/dev/null || echo 'kapali'",
        "Browserless": f"curl -s http://localhost:3001/json/version 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"Browser\",\"kapali\"))' 2>/dev/null || echo 'kapali'",
        "Open WebUI": f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:3000 2>/dev/null || echo 'kapali'",
        "Docker": "docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null | head -10 || echo 'kapali'",
    }

    for name, cmd in checks.items():
        out, err = _run_remote(cmd)
        status = "✅" if out and out != "kapali" and "error" not in out.lower() else "❌"
        print(f"  {status} {name}: {out[:100]}")
        if err and "error" in err.lower():
            print(f"     hata: {err[:80]}")

    print("=" * 55)


def cmd_litellm():
    """LiteLLM config ve docker-compose'u EC2'ye kopyala."""
    print("LiteLLM deploy ediliyor...")

    import paramiko

    key_path = os.path.expanduser(config.SSH_KEY_PATH)
    for alt in ["~/.ssh/id_ed25519", "~/.ssh/id_ecdsa"]:
        if not os.path.exists(key_path):
            alt_path = os.path.expanduser(alt)
            if os.path.exists(alt_path):
                key_path = alt_path

    transport = paramiko.Transport((config.EC2_HOST, config.SSH_PORT))
    transport.connect(username=config.EC2_USER, pkey=paramiko.RSAKey.from_private_key_file(key_path))

    sftp = paramiko.SFTPClient.from_transport(transport)

    # Kopyalanacak dosyalar
    files_to_copy = {
        "litellm-config.yaml": "/home/ubuntu/litellm-config.yaml",
        "docker-compose.yml": "/home/ubuntu/docker-compose.yml",
    }

    for local_rel, remote_path in files_to_copy.items():
        local_path = os.path.join(ROOT, local_rel)
        if os.path.exists(local_path):
            try:
                sftp.put(local_path, remote_path)
                print(f"  ✅ {local_rel} → {remote_path}")
            except Exception as e:
                print(f"  ❌ {local_rel} kopyalanamadi: {e}")
        else:
            print(f"  ⚠️  {local_rel} bulunamadi, atlaniyor")

    sftp.close()
    transport.close()

    # Docker compose restart
    out, err = _run_remote(
        "cd /home/ubuntu && docker compose up -d litellm 2>&1 || docker-compose up -d litellm 2>&1"
    )
    print(f"  Docker compose: {out[:200]}")
    if err:
        print(f"  hata: {err[:200]}")

    print("LiteLLM deploy tamamlandi.")


def cmd_config():
    """.env dosyasini EC2'ye kopyala."""
    print("Config deploy ediliyor...")
    import paramiko

    key_path = os.path.expanduser(config.SSH_KEY_PATH)
    for alt in ["~/.ssh/id_ed25519", "~/.ssh/id_ecdsa"]:
        if not os.path.exists(key_path):
            alt_path = os.path.expanduser(alt)
            if os.path.exists(alt_path):
                key_path = alt_path

    transport = paramiko.Transport((config.EC2_HOST, config.SSH_PORT))
    transport.connect(username=config.EC2_USER, pkey=paramiko.RSAKey.from_private_key_file(key_path))
    sftp = paramiko.SFTPClient.from_transport(transport)

    local_env = os.path.join(ROOT, "config", ".env")
    remote_env = "/home/ubuntu/dijital-varlik-config.env"

    try:
        sftp.put(local_env, remote_env)
        print(f"  ✅ config/.env → {remote_env}")
    except Exception as e:
        print(f"  ❌ Kopyalanamadi: {e}")

    sftp.close()
    transport.close()
    print("Config deploy tamamlandi.")


def cmd_grounding():
    """UI-TARS grounding modelini EC2'ye vLLM konteyneri olarak deploy et."""
    print("Grounding model (UI-TARS) deploy ediliyor...")
    print("  UYARI: Bu islem ~14GB GPU RAM gerektirir.")

    vllm_cmd = (
        "docker run -d --name ui-tars-grounding "
        "--gpus all "
        "-p 8080:8000 "
        "vllm/vllm-openai:latest "
        "--model ByteDance/UI-TARS-1.5-7B "
        "--max-model-len 4096 "
        "--gpu-memory-utilization 0.85 "
        "2>&1 || echo 'docker run basarisiz (container zaten var olabilir)'"
    )

    out, err = _run_remote(vllm_cmd, timeout=60)
    print(f"  {out[:300]}")
    if err:
        print(f"  hata: {err[:200]}")

    print("Grounding model deploy tamamlandi.")


def cmd_all():
    """Tum deploy adimlarini calistir."""
    print("=" * 55)
    print("TUM DEPLOY BASLATILIYOR")
    print("=" * 55)

    for name, fn in [
        ("1/4 SSH Kontrol", cmd_check),
        ("2/4 Servis Durumu", cmd_status),
        ("3/4 LiteLLM Deploy", cmd_litellm),
        ("4/4 Config Deploy", cmd_config),
    ]:
        print(f"\n--- {name} ---")
        fn()

    print("\n" + "=" * 55)
    print("DEPLOY TAMAMLANDI")
    print("=" * 55)


def print_usage():
    print(__doc__)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]
    commands = {
        "check": cmd_check,
        "status": cmd_status,
        "litellm": cmd_litellm,
        "config": cmd_config,
        "grounding": cmd_grounding,
        "all": cmd_all,
    }

    fn = commands.get(cmd)
    if fn:
        success = fn()
        if success is False:
            sys.exit(1)
    else:
        print(f"Bilinmeyen komut: {cmd}")
        print_usage()
        sys.exit(1)
