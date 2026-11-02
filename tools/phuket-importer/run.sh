#!/usr/bin/env bash
# Starts Phuket Importer in Docker (macOS / Linux): ./run.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
cd "$HERE"
docker build -t thaivillas-phuket-importer .
echo "Open http://localhost:8093  (results -> $REPO/imports)"
docker run --rm --name thaivillas-phuket-importer -p 8093:8090 \
  -e "THAIVILLAS_HOST_WORKSPACE=$REPO" \
  -v "$REPO:/workspace" thaivillas-phuket-importer
