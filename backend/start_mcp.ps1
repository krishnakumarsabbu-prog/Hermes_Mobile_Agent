# Hermes Personal Banking - MCP Server Startup Script (PowerShell)
[CmdletBinding()]
param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Hermes Personal Banking - MCP Server Startup   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$McpDir = Join-Path $ScriptDir "mcp_server"
$VenvDir = Join-Path $McpDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

# 1. Virtual environment setup
if (-not (Test-Path $PythonExe)) {
    Write-Host "[INFO] Creating virtual environment at $VenvDir..." -ForegroundColor Yellow
    $basePy = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { $null }
    if (-not $basePy) {
        Write-Error "Python 3.12+ was not found on PATH. Please install Python."
        exit 1
    }
    & $basePy -m venv $VenvDir
}

# 2. Ensure .env exists
$EnvFile = Join-Path $McpDir ".env"
$EnvExample = Join-Path $McpDir ".env.example"
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Write-Host "[INFO] Creating mcp_server/.env from .env.example..." -ForegroundColor Yellow
    Copy-Item $EnvExample $EnvFile
}

# 3. Verify dependencies
Write-Host "[INFO] Verifying MCP dependencies..." -ForegroundColor Gray
$ReqFile = Join-Path $McpDir "requirements.txt"
& $PythonExe -m pip install -r $ReqFile --quiet

# 4. Check backend connectivity
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/live" -TimeoutSec 2 -ErrorAction Stop
    if ($resp.status -eq "ok") {
        Write-Host "[INFO] Backend is running and healthy at http://127.0.0.1:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] FastAPI backend was not reached at http://127.0.0.1:8000." -ForegroundColor Yellow
    Write-Host "          Ensure backend is running (e.g. via .\start.ps1 in another terminal)." -ForegroundColor Yellow
}

if ($CheckOnly) {
    Write-Host "[INFO] Verification complete." -ForegroundColor Green
    exit 0
}

# 5. Launch MCP server
Write-Host "[INFO] Starting Hermes MCP server (stdio transport)..." -ForegroundColor Cyan
& $PythonExe -m mcp_server
