#!/usr/bin/env bash
# Prepares an Ubuntu Azure VM to serve Ollama and act as the private DB migration host.
set -euo pipefail

exec > >(tee -a /var/log/crumbwise-bootstrap.log) 2>&1

DISK=/dev/disk/azure/scsi1/lun0
if [ -e "$DISK" ]; then
  if ! blkid "$DISK" >/dev/null 2>&1; then
    mkfs.ext4 -F "$DISK"
  fi
  mkdir -p /data
  if ! mountpoint -q /data; then
    echo "UUID=$(blkid -s UUID -o value "$DISK") /data ext4 defaults,nofail 0 2" >> /etc/fstab
    mount -a
  fi
fi

mkdir -p /data/ollama/models

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates gnupg lsb-release

# Ollama
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/data/ollama/models"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
EOF

systemctl daemon-reload
systemctl enable ollama
systemctl restart ollama

# PostgreSQL 18 client for restoring the dump into the private flexible server
if ! command -v pg_restore >/dev/null 2>&1 || ! pg_restore --version | grep -q "18\."; then
  install -d /usr/share/postgresql-common/pgdg
  curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc
  echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql-client-18
fi

# Model weights are stored on the persistent data disk
sudo -u ollama ollama pull llama3.2:3b || ollama pull llama3.2:3b

echo "CRUMBWISE_BOOTSTRAP_COMPLETE"
