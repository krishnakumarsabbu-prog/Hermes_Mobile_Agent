#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=================================================="
echo "  Hermes Personal Banking - Backend Startup"
echo "=================================================="

# 1. Locate Python
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    ALEMBIC_CMD=".venv/bin/alembic"
    UVICORN_CMD=".venv/bin/uvicorn"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_CMD=".venv/Scripts/python.exe"
    ALEMBIC_CMD=".venv/Scripts/alembic.exe"
    UVICORN_CMD=".venv/Scripts/uvicorn.exe"
else
    if command -v python3 >/dev/null 2>&1; then
        BASE_PY="python3"
    elif command -v python >/dev/null 2>&1; then
        BASE_PY="python"
    else
        echo "[ERROR] Python 3.12+ is required but not installed."
        exit 1
    fi

    echo "[INFO] Creating virtual environment (.venv)..."
    "$BASE_PY" -m venv .venv
    if [ -f ".venv/bin/python" ]; then
        PYTHON_CMD=".venv/bin/python"
        ALEMBIC_CMD=".venv/bin/alembic"
        UVICORN_CMD=".venv/bin/uvicorn"
    else
        PYTHON_CMD=".venv/Scripts/python.exe"
        ALEMBIC_CMD=".venv/Scripts/alembic.exe"
        UVICORN_CMD=".venv/Scripts/uvicorn.exe"
    fi
fi

# 2. Ensure .env exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[INFO] Creating .env from .env.example..."
    cp .env.example .env
fi

# 3. Dependencies
echo "[INFO] Verifying Python dependencies..."
"$PYTHON_CMD" -m pip install -r requirements.txt --quiet

# 4. Migrations
echo "[INFO] Applying Alembic migrations..."
"$ALEMBIC_CMD" upgrade head

# 5. Seeding
if [ ! -f "data/hermes.db" ]; then
    echo "[INFO] Seeding initial synthetic data..."
    "$PYTHON_CMD" -m app.seed.seed_runner
fi

# 6. Launch Server
echo ""
echo "=================================================="
echo "  Backend running at: http://localhost:8000"
echo "  Swagger Docs:       http://localhost:8000/docs"
echo "  OpenAPI Spec:       http://localhost:8000/openapi.json"
echo "=================================================="
echo ""

"$UVICORN_CMD" app.main:app --host 0.0.0.0 --port 8000 --reload
