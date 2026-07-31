@echo off
title Project TALOS v5.8.1 -- Automated Batch Runner
chcp 65001 >nul 2>&1

REM ===========================================================================
REM run_talos.bat -- Automated Batch Runner for Project TALOS v5.8.1
REM
REM Provides a 9-option structured menu:
REM   Section 1: REST API & FRONTEND
REM     [1] Full Setup (Conda env + pip install + Frontend Provisioner)
REM     [2] Start FastAPI Server (uvicorn, port 8001)
REM     [3] Start MCP Server (python src/mcp_server.py)
REM     [4] Launch Interim UI (Cherry Studio)
REM   Section 2: CLI & STANDALONE DAEMONS
REM     [5] TALOS Terminal CLI (python talos.py)
REM     [6] Autonomous Research Daemon (python src/ai/drl/talos_service.py)
REM     [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)
REM   Section 3: TESTING & SYSTEM
REM     [8] Run Test Suite (pytest -v)
REM     [9] Exit
REM
REM TALOS FastAPI runs on port 8001 (port 8000 is reserved for SYNAPSE bus).
REM Legacy script preserved at: tools/start_talos.bat
REM ===========================================================================

:TOP
cls
echo =============================================
echo    Project TALOS v5.8.1
echo    Research Intelligence Platform
echo    SYNAPSE Protocol Active (Bus :8000 / API :8001)
echo =============================================
echo.
echo    -- Section 1: REST API and FRONTEND --
echo    [1] Full Setup (Conda + Pip + Frontend Provisioner)
echo    [2] Start FastAPI Server (uvicorn, port 8001)
echo    [3] Start MCP Server (python src/mcp_server.py)
echo    [4] Launch Interim UI (Cherry Studio)
echo.
echo    -- Section 2: CLI and STANDALONE DAEMONS --
echo    [5] TALOS Terminal CLI (python talos.py)
echo    [6] Autonomous Research Daemon (24/7 Service)
echo    [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)
echo.
echo    -- Section 3: TESTING and SYSTEM --
echo    [8] Run Test Suite (pytest -v)
echo    [9] Exit
echo.
set /p choice="    Select mode [1-9]: "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto SERVER
if "%choice%"=="3" goto MCP_SERVER
if "%choice%"=="4" goto PROVISION_UI
if "%choice%"=="5" goto CLI
if "%choice%"=="6" goto DAEMON
if "%choice%"=="7" goto LIVE_DRL
if "%choice%"=="8" goto TEST
if "%choice%"=="9" goto END
goto TOP

REM ---------------------------------------------------------------------------
REM Option 1: Full Setup (Conda, Pip, Frontend Provisioner)
REM ---------------------------------------------------------------------------
:SETUP
cls
echo =============================================
echo    Full Setup: Conda Environment + Pip Install + Frontend Provisioner
echo =============================================
echo.

echo [1/4] Checking for Conda...
where conda >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Conda not found on PATH.
    echo Please install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
    pause
    goto TOP
)
echo Conda found.

echo [2/4] Creating/Updating conda environment 'talosenv'...
call conda create -n talosenv python=3.11 -y 2>nul
call conda activate talosenv
IF ERRORLEVEL 1 (
    echo [ERROR] Could not activate talosenv conda environment.
    echo Please ensure Miniconda/Anaconda is installed correctly.
    pause
    goto TOP
)
echo Conda environment 'talosenv' is active.

echo [3/4] Installing Python dependencies...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo [WARNING] Some packages failed to install. Check the output above.
) ELSE (
    echo All dependencies installed successfully.
)

echo [4/4] Running Frontend Provisioner...
python src/utils/frontend_provisioner.py
IF ERRORLEVEL 1 (
    echo [WARNING] Frontend provisioner exited with errors. Check the output above.
) ELSE (
    echo Frontend provisioner completed successfully.
)

echo.
echo =============================================
echo    Setup complete. TALOS v5.8.1 is ready.
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
echo    Starting TALOS FastAPI Server (v5.8.1)
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
REM Option 3: Start MCP Server
REM ---------------------------------------------------------------------------
:MCP_SERVER
cls
echo =============================================
echo    Starting TALOS MCP Server (v5.8.1)
echo =============================================
echo.
echo    Press Ctrl+C to stop the MCP server.
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] Could not activate conda env. Using system Python.
)

REM -- Launch MCP server --
python src/mcp_server.py
goto TOP

REM ---------------------------------------------------------------------------
REM Option 4: Launch Interim UI (Cherry Studio)
REM ---------------------------------------------------------------------------
:PROVISION_UI
cls
echo =============================================
echo    Interim UI Provisioner (Cherry Studio)
echo =============================================
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] Could not activate conda env. Using system Python.
)

REM -- Run the provisioner --
python src/utils/frontend_provisioner.py %*

echo.
echo =============================================
echo    Provisioning complete.
echo    See cherry_ui_isolated/LAUNCH_INSTRUCTIONS.txt
echo =============================================
echo.
pause
goto TOP

REM ---------------------------------------------------------------------------
REM Option 5: TALOS Terminal CLI
REM ---------------------------------------------------------------------------
:CLI
cls
echo =============================================
echo    TALOS Terminal CLI (v5.8.1)
echo =============================================
echo.
echo    Launching the interactive TALOS command-line interface.
echo    Type 'help' inside the CLI for available commands.
echo    Press Ctrl+C to exit back to this menu.
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] Could not activate conda env. Using system Python.
)

REM -- Launch talos.py CLI --
python talos.py
goto TOP

REM ---------------------------------------------------------------------------
REM Option 6: Autonomous Research Daemon (24/7 Service)
REM ---------------------------------------------------------------------------
:DAEMON
cls
echo =============================================
echo    Autonomous Research Daemon (v5.8.1)
echo    24/7 Background Research Service
echo =============================================
echo.
echo    This daemon continuously discovers, evaluates, and enriches
echo    research papers in the background. It runs until interrupted.
echo.
echo    Press Ctrl+C to stop the daemon and return to this menu.
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] Could not activate conda env. Using system Python.
)

REM -- Launch talos_service.py --
python src/ai/drl/talos_service.py
goto TOP

REM ---------------------------------------------------------------------------
REM Option 7: Live DRL Agent
REM ---------------------------------------------------------------------------
:LIVE_DRL
cls
echo =============================================
echo    Live DRL Agent (v5.8.1)
echo    Deep Reinforcement Learning Agent -- Verbose Mode
echo =============================================
echo.
echo    The Live DRL Agent interacts with the environment in real-time,
echo    making decisions about paper discovery, evaluation, and enrichment.
echo    Verbose mode is enabled for detailed step-by-step output.
echo.
echo    Press Ctrl+C to stop the agent and return to this menu.
echo.

REM -- Activate conda environment first --
call conda activate talosenv >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARNING] Could not activate conda env. Using system Python.
)

REM -- Launch talos_live_agent.py with verbose flag --
python src/ai/drl/talos_live_agent.py --verbose
goto TOP

REM ---------------------------------------------------------------------------
REM Option 8: Run Test Suite
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
REM Option 9: Exit
REM ---------------------------------------------------------------------------
:END
echo.
echo =============================================
echo    Closing Project TALOS v5.8.1...
echo =============================================
exit /b