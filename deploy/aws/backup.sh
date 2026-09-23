#!/usr/bin/env bash
# Snapshot uploads + vector index to /data/backups (keeps the last 7).  Run from cron, e.g.:
#   0 3 * * *  bash ~/EduRAG/deploy/aws/backup.sh
# (RDS backs up Postgres by itself. Also enable EBS snapshots for the data disk in the AWS console.)
set -euo pipefail
DEST=/data/backups; mkdir -p "$DEST"
STAMP="$(date +%Y%m%d-%H%M)"
# Stop writers briefly so the Chroma SQLite file is consistent.
cd "$(dirname "$0")"
docker compose -f docker-compose.prod.yml stop backend
tar -czf "$DEST/edurag-data-$STAMP.tar.gz" -C /data/edurag uploads vector_db
docker compose -f docker-compose.prod.yml start backend
ls -1t "$DEST"/edurag-data-*.tar.gz | tail -n +8 | xargs -r rm -f
echo "Backup written: $DEST/edurag-data-$STAMP.tar.gz"
