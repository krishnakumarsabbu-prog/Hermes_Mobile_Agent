@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d "%~dp0"

echo ==================================================
echo   Hermes Personal Banking - Backend Startup
echo ==================================================

REM 1. Locate Python and create venv if needed
if exist ".\.venv\Scripts\python.exe" goto :VENV_READY

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "BASE_PY=py"
    goto :CREATE_VENV
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "BASE_PY=python"
    goto :CREATE_VENV
)

echo [ERROR] Python not found. Please install Python 3.12+
pause
exit /b 1

:CREATE_VENV
echo [INFO] Creating virtual environment...
%BASE_PY% -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

:VENV_READY
set "PYTHON_EXE=.\.venv\Scripts\python.exe"

REM 2. Ensure .env exists
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example
        copy .env.example .env >nul
    )
)

REM 3. Dependencies
echo [INFO] Verifying dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet

REM 4. Migrations
echo [INFO] Applying database migrations...
".\.venv\Scripts\alembic.exe" upgrade head

REM 5. Seed if database does not exist
if not exist "data\hermes.db" (
    echo [INFO] Seeding initial synthetic data...
    "%PYTHON_EXE%" -m app.seed.seed_runner
)

REM 6. Launch Server
echo.
echo ==================================================
echo   Backend running at: http://localhost:8000
echo   Swagger Docs:       http://localhost:8000/docs
echo   OpenAPI Spec:       http://localhost:8000/openapi.json
echo ==================================================
echo.

".\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 --reload
