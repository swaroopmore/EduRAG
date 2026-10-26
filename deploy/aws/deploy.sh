#!/usr/bin/env bash
# Update the running server to the latest code:   bash deploy/aws/deploy.sh [branch]
set -euo pipefail
cd "$(dirname "$0")"
BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

[ -f .env.prod ] || { echo "Missing deploy/aws/.env.prod (copy .env.prod.example and fill it in)."; exit 1; }

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker image prune -f >/dev/null

echo "Waiting for the API to become healthy..."
DOMAIN="$(grep -E '^API_DOMAIN=' .env.prod | cut -d= -f2-)"
for i in $(seq 1 40); do
  if curl -fsS "https://$DOMAIN/health" >/dev/null 2>&1; then echo "API is up: https://$DOMAIN/health"; exit 0; fi
  sleep 5
done
echo "API did not answer in time. Check:  docker compose -f docker-compose.prod.yml logs --tail=100"
exit 1
