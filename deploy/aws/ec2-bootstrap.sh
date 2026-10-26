#!/usr/bin/env bash
# One-time setup of a fresh Amazon Linux 2023 EC2 server for EduRAG.
# Run as the normal user (ec2-user):   bash ec2-bootstrap.sh /dev/nvme1n1
# The argument is the EXTRA data disk (see `lsblk`). It is formatted ONLY if it is empty.
set -euo pipefail

DATA_DEV="${1:-}"
[ -n "$DATA_DEV" ] || { echo "Usage: bash ec2-bootstrap.sh <data-disk-device>   (find it with: lsblk)"; exit 1; }
[ -b "$DATA_DEV" ] || { echo "$DATA_DEV is not a block device. Run lsblk and pass the extra disk."; exit 1; }

echo "==> Installing Docker, Compose and git"
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

echo "==> Preparing the data disk ($DATA_DEV)"
if sudo blkid "$DATA_DEV" >/dev/null 2>&1; then
  echo "    disk already has a filesystem - keeping its data"
else
  sudo mkfs.xfs "$DATA_DEV"
fi
sudo mkdir -p /data
UUID="$(sudo blkid -s UUID -o value "$DATA_DEV")"
grep -q "$UUID" /etc/fstab || echo "UUID=$UUID /data xfs defaults,nofail 0 2" | sudo tee -a /etc/fstab >/dev/null
sudo mount -a
# The container runs as uid 1000 ("app"), so it must own these folders.
sudo mkdir -p /data/edurag/uploads /data/edurag/vector_db
sudo chown -R 1000:1000 /data/edurag

echo "==> Adding 2 GB swap (protects against out-of-memory during model loading/builds)"
if [ ! -f /swapfile ]; then
  sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
fi
sudo swapon -a || true

echo
echo "Done. Log out and back in (so the docker group applies), then continue with AWS_DEPLOY.md Part 6."
