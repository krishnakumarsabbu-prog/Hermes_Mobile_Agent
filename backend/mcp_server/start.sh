#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=================================================="
echo "  Hermes Personal Banking - MCP Server Startup   "
echo "=================================================="

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
fi

if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    echo "[INFO] Creating mcp_server/.env from .env.example..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

echo "[INFO] Verifying MCP dependencies..."
"$PYTHON_BIN" -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet

if curl -s --connect-timeout 2 http://127.0.0.1:8000/health/live >/dev/null 2>&1; then
    echo "[INFO] Backend is running and healthy at http://127.0.0.1:8000"
else
    echo "[WARNING] Backend is not reachable at http://127.0.0.1:8000. Start it in another terminal."
fi

echo "[INFO] Starting Hermes MCP server (stdio transport)..."
cd "$BACKEND_DIR"
exec "$PYTHON_BIN" -m mcp_server
