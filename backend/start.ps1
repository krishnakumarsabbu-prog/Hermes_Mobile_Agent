param (
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Seed,
    [switch]$Reset,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Hermes Personal Banking - Backend Startup " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Determine Python command
$PythonCmd = $null
if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonCmd = ".\.venv\Scripts\python.exe"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} else {
    Write-Host "[ERROR] Python is not found. Please install Python 3.12+ from python.org or the Microsoft Store." -ForegroundColor Red
    exit 1
}

# 2. Check and initialize virtual environment
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "[INFO] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    & $PythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}
$VenvPython = ".\.venv\Scripts\python.exe"

# 3. Ensure .env exists
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "[INFO] Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
    }
}

# 4. Verify & Install dependencies
Write-Host "[INFO] Checking Python dependencies..." -ForegroundColor Cyan
& $VenvPython -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] pip install returned non-zero code. Trying to proceed..." -ForegroundColor Yellow
}

# 5. Database migrations
Write-Host "[INFO] Applying Alembic database migrations..." -ForegroundColor Cyan
& ".\.venv\Scripts\alembic.exe" upgrade head

# 6. Seed database if not already seeded or requested
$DbPath = "data\hermes.db"
$NeedSeed = $false
if ($Reset) {
    Write-Host "[INFO] Resetting and re-seeding synthetic database..." -ForegroundColor Yellow
    & $VenvPython -m app.seed.seed_runner --reset
} elseif ($Seed -or (-not (Test-Path $DbPath))) {
    Write-Host "[INFO] Seeding initial synthetic data..." -ForegroundColor Yellow
    & $VenvPython -m app.seed.seed_runner
}

# 7. Start FastAPI / Uvicorn server
$ReloadArg = if ($NoReload) { @() } else { @("--reload") }
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Backend running at: http://localhost:$Port" -ForegroundColor Green
Write-Host "  Swagger Docs:       http://localhost:$Port/docs" -ForegroundColor Green
Write-Host "  OpenAPI Spec:       http://localhost:$Port/openapi.json" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

& ".\.venv\Scripts\uvicorn.exe" app.main:app --host $HostAddress --port $Port @ReloadArg
