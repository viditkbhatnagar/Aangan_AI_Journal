#!/usr/bin/env bash
# Nightly Aangan backup: consistent SQLite snapshot + vector store + audio.
# Usage (from backend/):  ./scripts/backup.sh [target-dir]
# Restore: stop the server, copy aangan.db back, untar chroma+media, restart.
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-$BACKEND_DIR/../backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$TARGET/aangan-$STAMP"
mkdir -p "$DEST"

# consistent snapshot even while the server is running
if [ -f "$BACKEND_DIR/aangan.db" ]; then
  sqlite3 "$BACKEND_DIR/aangan.db" ".backup '$DEST/aangan.db'"
fi
[ -d "$BACKEND_DIR/chroma_data" ] && tar -czf "$DEST/chroma_data.tgz" -C "$BACKEND_DIR" chroma_data
[ -d "$BACKEND_DIR/data" ] && tar -czf "$DEST/media.tgz" -C "$BACKEND_DIR" data

# keep the last 14 backups
ls -1dt "$TARGET"/aangan-* 2>/dev/null | tail -n +15 | xargs rm -rf 2>/dev/null || true

echo "Backup written to $DEST"
