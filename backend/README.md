# Hermes Personal Banking — FastAPI Simulation Backend

A local FastAPI + SQLite simulation backend for the Hermes Personal Banking POC.
No real banking connectivity, real payment execution, or actual money movement.

## Requirements

- Python 3.12+
- The Python packages listed in `requirements.txt`

## Quick start

All commands assume you are in the `backend/` directory.

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run database migrations
alembic upgrade head

# 3. Seed synthetic data (idempotent; use --reset to wipe and reseed)
python -m app.seed.seed_runner

# 4. Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Run backend tests (uses isolated temp databases — safe to run anytime)
pytest
```

Swagger UI is available at `http://localhost:8000/docs`.
OpenAPI spec at `http://localhost:8000/openapi.json`.

## Configuration

Copy `.env.example` to `.env` and adjust as needed. Key settings:

- `HERMES_DB_PATH` — SQLite database file path (default: `data/hermes.db`)
- `HERMES_REPORTING_TIMEZONE` — IANA timezone for calendar-month filtering (default: `Asia/Kolkata`)
- `HERMES_CORS_ORIGINS` — Comma-separated allowed CORS origins
- `HERMES_DEV_USER_ID` — Demo user resolved by the dev auth adapter (default: `usr_01`)
- `HERMES_SEED_*` — Synthetic dataset sizing controls

## Device networking

- **Android emulator**: reach the dev host at `http://10.0.2.2:8000`
- **iOS simulator**: use `http://localhost:8000`
- **Physical device**: use your development machine's LAN address (e.g. `http://192.168.1.100:8000`)
- Do not expose the development server to the public internet.

## Authentication

This backend uses a development authentication adapter that resolves a seeded
demo user from a configurable header (`X-Hermes-Dev-User`) or a default. This is
NOT production authentication. The adapter is designed to be replaced by a
proper identity provider in a future phase.

## Important notes

- The local development auth adapter, local SQLite deployment, and simulated
  transfers are NOT sufficient for real financial production use.
- Monetary values are stored as integer paise. No floating-point is used for
  financial amounts.
- Transfer authorization uses conditional SQL updates to prevent double-debit
  under concurrency. A process-local lock is not relied upon.
- The seed runner is idempotent by default. `--reset` must be passed explicitly.
