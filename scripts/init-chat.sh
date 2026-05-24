#!/usr/bin/env bash
# =============================================================================
# init-chat.sh — Convenience-Wrapper für deepchats CLI
# =============================================================================
# Nutzung:
#   ./scripts/init-chat.sh                          # interaktiv
#   ./scripts/init-chat.sh --type code --topic sunca --task "api bauen"
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== deepchats init ==="
echo ""

# Prüfe ob deepchats CLI installiert ist
if command -v deepchats &>/dev/null; then
    deepchats init "$@"
elif python -c "import app.cli" 2>/dev/null; then
    python -m app.cli init "$@"
else
    echo "[FEHLER] deepchats ist nicht installiert."
    echo "  pip install -e $PROJECT_DIR"
    exit 1
fi
