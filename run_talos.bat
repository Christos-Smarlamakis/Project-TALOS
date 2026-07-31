@echo off
title Project TALOS v5.7.0 — Automated Batch Runner
chcp 65001 >nul 2>&1

REM ===========================================================================
REM run_talos.bat — Automated Batch Runner for Project TALOS v5.7.0
REM
REM Provides a 3-option menu for setup, server launch, and testing.
REM TALOS FastAPI now runs on port 8001 (port 8000 is reserved for SYNAPSE bus).
REM
REM Legacy script preserved at: tools/start_talos.bat
REM ===========================================================================

:TOP
cls
echo =============================================
echo    Project TALOS v5.7.0
echo    Research Intelligence Platform
echo    SYNAPSE Protocol Active (Bus :8000 / API :8001)
echo =============================================
echo.
echo    [1] Full Setup (Conda env + pip install)
echo    [2] Start FastAPI Server (uvicorn, port 8001)
echo    [3] Run Test Suite (pytest -v)
echo    [4] Exit
echo.
set /p choice="    Select mode [1-4]: "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto SERVER
if "%choice%"=="3" goto TEST
if "%choice%"=="4" goto END
goto TOP

REM ---------------------------------------------------------------------------
REM Option 1: Full Setup
REM ---------------------------------------------------------------------------
:SETUP
cls
echo =============================================
echo    Full Setup: Conda Environment + Pip Install
echo =============================================
echo.

echo [1/3] Checking for Conda...
where conda >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Conda not found on PATH.
    echo Please install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
    pause
    goto TOP
)
echo Conda found.

echo [2/3] Creating/Updating conda environment 'talosenv'...
call conda create -n talosenv python=3.11 -y 2>nul
call conda activate talosenv
IF ERRORLEVEL 1 (
    echo [ERROR] Could not activate talosenv conda environment.
    echo Please ensure Miniconda/Anaconda is installed correctly.
    pause
    goto TOP
)
echo Conda environment 'talosenv' is active.

echo [3/3] Installing Python dependencies...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo [WARNING] Some packages failed to install. Check the output above.
) ELSE (
    echo All dependencies installed successfully.
)

echo.
echo =============================================
echo    Setup complete. TALOS v5.7.0 is ready.
echo =============================================
echo.
echo    TALOS API will start on port 8001.
echo    SYNAPSE bus is expected on port 8000.
echo.
pause
goto TOP

REM ---------------------------------------------------------------------------
REM Option 2: Start FastAPI Server (port 8001)
REM ---------------------------------------------------------------------------
:SERVER
cls
echo =============================================
echo    Starting TALOS FastAPI Server (v5.7.0)
echo    Port: 8001
echo    API Docs: http://localhost:8001/docs
echo    Health:   http://localhost:8001/api/v1/health
echo    Synapse:  http://localhost:8001/api/v1/synapse/webhook
echo =============================================
echo.
echo    Press Ctrl+C to stop the server.
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] Could not activate conda env. Using system Python.
)

REM -- Launch uvicorn --
python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001
goto TOP

REM ---------------------------------------------------------------------------
REM Option 3: Run Test Suite
REM ---------------------------------------------------------------------------
:TEST
cls
echo =============================================
echo    Running TALOS Test Suite (pytest)
echo =============================================
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1

REM -- Check if pytest is installed --
python -m pytest --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] pytest not found. Installing...
    pip install pytest >nul 2>&1
)

echo Running tests...
echo.
python -m pytest -v --tb=short 2>&1

IF ERRORLEVEL 1 (
    echo.
    echo =============================================
    echo    Some tests FAILED. Review output above.
    echo =============================================
) ELSE (
    echo.
    echo =============================================
    echo    All tests PASSED.
    echo =============================================
)

echo.
pause
goto TOP

REM ---------------------------------------------------------------------------
REM Option 4: Exit
REM ---------------------------------------------------------------------------
:END
echo.
echo =============================================
echo    Closing Project TALOS v5.7.0...
echo =============================================
exit /b