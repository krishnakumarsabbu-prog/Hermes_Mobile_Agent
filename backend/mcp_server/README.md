# Hermes Personal Banking MCP Server

A standalone [Model Context Protocol](https://modelcontextprotocol.io) server
that exposes the Hermes Personal Banking simulation backend's financial tools
to an MCP client such as Hermes Agent.

The server runs as a **separate process** from the FastAPI backend and
communicates with it over authenticated HTTP. It does **not** import backend
internals, duplicate business logic, or bypass authentication.

## Architecture

```
Hermes Agent
  → MCP client
    → Standalone Python MCP server (stdio transport)
      → Authenticated async HTTP client
        → Existing FastAPI REST API
          → Existing business logic, database, simulated ledger
```

- **Transport:** stdio (standard input/output) for local Hermes installations.
- **Protocol messages:** stdout. **Diagnostic logs:** stderr.
- **Auth:** reuses the backend's existing development auth adapter via the
  `X-Hermes-Dev-User` header. This is NOT production authentication.
- **Authorization of transfers:** disabled by default. The server exposes
  read-only tools, transfer **preparation** (no debit), transfer **status**,
  and transfer **cancellation** only.

## Tools exposed

| Tool | Type | Backend endpoint |
|------|------|------------------|
| `get_account_balance` | read-only | `GET /api/v1/account/balance` |
| `get_account_summary` | read-only | `GET /api/v1/account` |
| `list_beneficiaries` | read-only | `GET /api/v1/beneficiaries` |
| `get_monthly_spending` | read-only | `GET /api/v1/spending/monthly` |
| `get_category_spending` | read-only | `GET /api/v1/spending/categories` |
| `list_transactions` | read-only | `GET /api/v1/transactions` |
| `get_transaction_details` | read-only | `GET /api/v1/transactions/{id}` |
| `get_transfer_status` | read-only | `GET /api/v1/transfers/{id}` |
| `prepare_transfer` | state-changing (no debit) | `POST /api/v1/transfers/prepare` |
| `cancel_transfer` | state-changing | `POST /api/v1/transfers/{id}/cancel` |

**Not exposed by default:** `POST /api/v1/transfers/{id}/authorize`. This is
the two-phase ledger debit. Enabling it requires a separately reviewed feature
flag and verification of the backend's simulation-only enforcement.

## Prerequisites

- Python 3.12+ (developed against 3.13)
- The Hermes FastAPI backend running locally (see backend `README.md`)

## 1. Install dependencies

From the `backend/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r mcp_server/requirements.txt
```

If you share the backend's virtual environment, install the MCP requirements
into it directly:

```bash
pip install -r backend/mcp_server/requirements.txt
```

## 2. Configure the backend base URL

Copy the example env file and adjust if your backend runs elsewhere:

```bash
cp backend/mcp_server/.env.example backend/mcp_server/.env
```

Key variables (all prefixed `HERMES_MCP_`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `HERMES_MCP_BACKEND_BASE_URL` | `http://127.0.0.1:8000` | FastAPI base URL |
| `HERMES_MCP_DEV_USER_ID` | `usr_01` | Dev-auth user id sent via header |
| `HERMES_MCP_SEND_DEV_USER_HEADER` | `true` | Whether to send the header |
| `HERMES_MCP_ENABLE_AUTHORIZE_TOOL` | `false` | Authorization tool toggle (disabled) |

## 3. Configure authentication securely

The server reuses the backend's development auth adapter. The user identity is
**always** derived from server configuration, never from an LLM tool argument.

- Set `HERMES_MCP_DEV_USER_ID` to the intended demo user.
- Never hardcode tokens or user ids in source.
- Never log authorization headers (the server does not).
- The server fails closed if the configured identity is rejected by the backend.

> This dev adapter is explicitly not production auth. A future phase must
> replace it with a verified-token scheme.

## 4. Start the FastAPI backend

```bash
cd backend
./start.sh                 # Linux/macOS/WSL
# or
./start.ps1                # Windows PowerShell
```

The backend runs at `http://localhost:8000`. Verify:

```bash
curl http://localhost:8000/health/live
# {"status":"ok"}
```

## 5. Register the MCP server in Hermes

Hermes Agent discovers MCP servers via its configuration file. Add an entry
pointing at the server's launch command.

### Hermes MCP configuration example

Hermes supports stdio-based MCP servers launched by a command. Add this to your
Hermes MCP servers configuration (location depends on your Hermes installation;
commonly `~/.hermes/mcp.json` or the Hermes settings UI):

```json
{
  "mcpServers": {
    "hermes-personal-banking": {
      "command": "/absolute/path/to/backend/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "/absolute/path/to/backend",
      "env": {
        "HERMES_MCP_BACKEND_BASE_URL": "http://127.0.0.1:8000",
        "HERMES_MCP_DEV_USER_ID": "usr_01",
        "HERMES_MCP_SEND_DEV_USER_HEADER": "true"
      }
    }
  }
}
```

> **Use absolute paths.** If Hermes runs inside WSL, Docker, or another
> isolated environment, the `command`, `cwd`, and `env` paths must be valid
> *inside that environment*. `http://127.0.0.1:8000` refers to localhost as
> seen by the MCP server process — if the backend runs on the Windows host and
> Hermes runs in WSL, use the WSL host IP (often `http://host.docker.internal`
> in Docker, or the Windows host IP) instead of `127.0.0.1`.

### Manual run (no Hermes)

```bash
cd backend
.venv/bin/python -m mcp_server
```

The server reads JSON-RPC over stdio. You can pipe an initialize request to
test it:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | .venv/bin/python -m mcp_server
```

## 6. Restart or reload Hermes

After editing the MCP configuration, restart Hermes (or reload its MCP server
list via its UI/command) so it spawns the new server process.

## 7. Verify that tools are discoverable

With the backend running and Hermes restarted, ask Hermes to list available
tools, or use the MCP inspector:

```bash
npx @modelcontextprotocol/inspector .venv/bin/python -m mcp_server
```

You should see 10 tools listed (the table above).

## 8. Invoke a read-only tool

Ask Hermes: "What is my current account balance?" This invokes
`get_account_balance`, which calls `GET /api/v1/account/balance` and returns
the balance in paise and the formatted INR string.

## 9. Verify transfer preparation does not execute a debit

1. Note your balance (invoke `get_account_balance`).
2. Invoke `prepare_transfer` with a beneficiary id, amount in paise, and an
   idempotency key.
3. Invoke `get_account_balance` again. The balance must be **unchanged** —
   preparation creates a pending approval but never debits.

You can confirm with the backend test suite:

```bash
cd backend && .venv/bin/pytest tests/test_transfers.py::test_prepare_does_not_debit -v
```

## 10. Diagnose failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `BACKEND_UNREACHABLE` | Backend not running or wrong URL | Start backend; check `HERMES_MCP_BACKEND_BASE_URL` |
| `BACKEND_TIMEOUT` | Backend slow or network issue | Increase `HERMES_MCP_READ_TIMEOUT`; check backend health |
| `UNAUTHORIZED` (401) | Dev user id rejected | Set a valid `HERMES_MCP_DEV_USER_ID` |
| `FORBIDDEN` (403) | User lacks permission | Use a user id the backend authorizes |
| `NOT_FOUND` (404) | Resource doesn't exist or belongs to another user | Check the id; ownership is enforced server-side |
| Tools not listed in Hermes | Wrong command path / cwd / env | Use absolute paths; ensure `cwd` is the `backend/` dir |
| Python `ModuleNotFoundError: mcp` | MCP SDK not installed | Run `pip install -r mcp_server/requirements.txt` |

Check stderr logs for diagnostics (protocol stays on stdout):

```bash
.venv/bin/python -m mcp_server 2>mcp_stderr.log
```

## Testing

```bash
cd backend
.venv/bin/pytest mcp_server/tests/ -v
```

Tests use mocked HTTP responses for unit tests and an in-process FastAPI
`TestClient` for integration tests. No real credentials or live services are
required.

## Safety assumptions and limitations

- The server connects only to the configured `HERMES_MCP_BACKEND_BASE_URL`,
  which must be `http` or `https` and is validated at startup. Redirects are
  disabled to avoid leaking credentials to unexpected hosts.
- No tool accepts an arbitrary destination URL, shell command, or user identity
  from the model. User identity comes solely from server configuration.
- `prepare_transfer` does not authorize or execute a transfer. Authorization is
  disabled by default and not registered as a tool.
- The backend's dev auth adapter is a simulation; this server inherits that
  limitation. Production deployment requires a verified-token auth scheme.
- This POC must never be connected to live bank APIs, UPI rails, wallets, or
  payment processors.
- Monetary precision is preserved as integer paise throughout; no floating-point
  arithmetic is used for money.
