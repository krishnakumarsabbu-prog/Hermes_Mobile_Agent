@echo off
setlocal

cd /d "%~dp0"

echo ==================================================
echo   Hermes Personal Banking - MCP Server Startup
echo ==================================================

REM 1. Set environment paths
set "MCP_DIR=%~dp0mcp_server"
set "VENV_DIR=%MCP_DIR%\.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

REM 2. Verify or create virtual environment
if exist "%PYTHON_EXE%" goto :VENV_READY

echo [INFO] Virtual environment not found at %VENV_DIR%.
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

echo [ERROR] Python not found on PATH. Please install Python 3.12+
pause
exit /b 1

:CREATE_VENV
echo [INFO] Creating virtual environment for MCP server...
%BASE_PY% -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

:VENV_READY
REM 3. Ensure mcp_server\.env exists
if not exist "%MCP_DIR%\.env" (
    if exist "%MCP_DIR%\.env.example" (
        echo [INFO] Creating mcp_server\.env from .env.example
        copy "%MCP_DIR%\.env.example" "%MCP_DIR%\.env" >nul
    )
)

REM 4. Verify dependencies
echo [INFO] Checking dependencies in MCP environment...
"%PYTHON_EXE%" -m pip install -r "%MCP_DIR%\requirements.txt" --quiet

REM 5. Warn if backend is not running
curl -s --connect-timeout 2 http://127.0.0.1:8000/health/live >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] FastAPI backend is not detected at http://127.0.0.1:8000.
    echo           Please ensure you start the backend using '.\start.bat' in a separate terminal.
) else (
    echo [INFO] Backend detected and healthy at http://127.0.0.1:8000
)

REM 6. Run the MCP server
echo [INFO] Starting Hermes MCP server (stdio transport)...
echo [INFO] Listening for JSON-RPC messages on stdio.
"%PYTHON_EXE%" -m mcp_server
