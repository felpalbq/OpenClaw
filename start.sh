#!/usr/bin/env bash
# OpenClaw startup — sets PYTHONPATH and launches the system
# Requires: Python 3.10+, ahri/ repo cloned alongside openclaw/

OPENCLAW_DIR="$(cd "$(dirname "$0")" && pwd)"
AHRI_DIR="$(dirname "$OPENCLAW_DIR")/ahri"

export PYTHONPATH="$OPENCLAW_DIR:$AHRI_DIR"

# Load .env if present
if [ -f "$OPENCLAW_DIR/.env" ]; then
    set -a
    source "$OPENCLAW_DIR/.env"
    set +a
fi

echo "Starting OpenClaw..."
python -m scheduler