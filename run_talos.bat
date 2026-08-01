@echo off
title Project TALOS v5.9.7 -- Automated Batch Runner
chcp 65001 >nul 2>&1

REM ===========================================================================
REM run_talos.bat -- Automated Batch Runner for Project TALOS v5.9.7
REM
REM Provides a 10-option structured menu:
REM   Section 1: REST API & FRONTEND
REM     [1] Full Setup (Conda env + pip install + Frontend Provisioner)
REM     [2] Start FastAPI Server (uvicorn, port 8001) -- background window
REM     [3] Start MCP Server (python src/mcp_server.py) -- background window
REM     [4] Launch Interim UI (Cherry Studio)
REM   Section 2: CLI & STANDALONE DAEMONS
REM     [5] TALOS Terminal CLI (python talos.py)
REM     [6] Autonomous Research Daemon (python src/ai/drl/talos_service.py)
REM     [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)
REM   Section 3: TESTING & SYSTEM
REM     [8] Autonomous System Tester (RL Chaos Fuzzer)
REM     [9] Run Test Suite (pytest -v)
REM     [10] Exit
REM
REM TALOS FastAPI runs on port 8001 (port 8000 is reserved for SYNAPSE bus).
REM Features (v5.9.3): Autonomous System Tester (RL-Driven Chaos Engineering with
REM LLM-as-a-Judge diagnostics), Auto-Conda path detection, background windows,
REM auto-start chain, automatic Fermion CPU server spawning.
REM ===========================================================================

REM ---------------------------------------------------------------------------
REM -- Auto-Conda Path Detection (v5.8.9) --
REM Scans common Miniconda/Anaconda installation directories for activate.bat.
REM If found, the full path is stored in CONDA_ACTIVATE_PATH and used for all
REM subsequent conda activation calls. Falls back to standard "conda" command
REM if no activate.bat is found at any known location.
REM ---------------------------------------------------------------------------
set "CONDA_ACTIVATE_PATH="

REM -- Scan for activate.bat in priority order --
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE_PATH=%USERPROFILE%\miniconda3\Scripts\activate.bat"
    goto :CONDA_FOUND
)
if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE_PATH=%USERPROFILE%\anaconda3\Scripts\activate.bat"
    goto :CONDA_FOUND
)
if exist "C:\ProgramData\miniconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE_PATH=C:\ProgramData\miniconda3\Scripts\activate.bat"
    goto :CONDA_FOUND
)
if exist "C:\ProgramData\anaconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE_PATH=C:\ProgramData\anaconda3\Scripts\activate.bat"
    goto :CONDA_FOUND
)
if exist "%LOCALAPPDATA%\Continuum\anaconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE_PATH=%LOCALAPPDATA%\Continuum\anaconda3\Scripts\activate.bat"
    goto :CONDA_FOUND
)

REM -- Fallback: rely on conda being on PATH --
echo [INFO] Auto-Conda detection: no activate.bat found at known paths.
echo [INFO] Falling back to standard 'conda' command on PATH.
goto :CONDA_DETECT_DONE

:CONDA_FOUND
echo [INFO] Auto-Conda detection: found activate.bat at "%CONDA_ACTIVATE_PATH%"
goto :CONDA_DETECT_DONE

:CONDA_DETECT_DONE

REM ===========================================================================
REM -- Subroutine: Activate the talosenv Conda environment --
REM Uses the detected activate.bat path if available; falls back to
REM standard 'call conda activate talosenv' otherwise.
REM ===========================================================================
goto :TOP

:ACTIVATE_CONDA
if defined CONDA_ACTIVATE_PATH (
    call "%CONDA_ACTIVATE_PATH%" talosenv >nul 2>&1
    IF ERRORLEVEL 1 (
        echo [WARNING] Could not activate conda env via "%CONDA_ACTIVATE_PATH%". Trying fallback...
        call conda activate talosenv >nul 2>&1
    )
) else (
    call conda activate talosenv >nul 2>&1
    IF ERRORLEVEL 1 (
        echo [WARNING] Could not activate conda env. Using system Python.
    )
)
goto :EOF

:TOP
cls
echo =============================================
echo    Project TALOS v5.9.7
echo    Research Intelligence Platform
echo    SYNAPSE Protocol Active (Bus :8000 / API :8001)
echo =============================================
echo.
echo    -- Section 1: REST API and FRONTEND --
echo    [1] Full Setup (Conda + Pip + Frontend Provisioner)
echo    [2] Start FastAPI Server (uvicorn, port 8001 -- background)
echo    [3] Start MCP Server (python src/mcp_server.py -- background)
echo    [4] Launch Interim UI (Cherry Studio)
echo.
echo    -- Section 2: CLI and STANDALONE DAEMONS --
echo    [5] TALOS Terminal CLI (python talos.py)
echo    [6] Autonomous Research Daemon (24/7 Service)
echo    [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)
echo.
echo    -- Section 3: TESTING and SYSTEM --
echo    [8] Autonomous System Tester (RL Chaos Fuzzer)
echo    [9] Run Test Suite (pytest -v)
echo    [10] Exit
echo.
set /p choice="    Select mode [1-10]: "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto SERVER
if "%choice%"=="3" goto MCP_SERVER
if "%choice%"=="4" goto PROVISION_UI
if "%choice%"=="5" goto CLI
if "%choice%"=="6" goto DAEMON
if "%choice%"=="7" goto LIVE_DRL
if "%choice%"=="8" goto AUTO_TESTER
if "%choice%"=="9" goto TEST
if "%choice%"=="10" goto END
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
echo    TALOS v5.9.7 -- Data Directory Consolidation & Dynamic Target Discovery
echo.

echo [1/4] Checking for Conda...
if defined CONDA_ACTIVATE_PATH (
    echo Conda found at: "%CONDA_ACTIVATE_PATH%"
) else (
    where conda >nul 2>&1
    IF ERRORLEVEL 1 (
        echo [ERROR] Conda not found on PATH.
        echo Please install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
        pause
        goto TOP
    )
    echo Conda found on PATH.
)

echo [2/4] Creating/Updating conda environment 'talosenv'...
if defined CONDA_ACTIVATE_PATH (
    call "%CONDA_ACTIVATE_PATH%" && conda create -n talosenv python=3.11 -y 2>nul
) else (
    call conda create -n talosenv python=3.11 -y 2>nul
)
call :ACTIVATE_CONDA
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
echo    Setup complete. TALOS v5.9.7 is ready.
echo =============================================
echo.
echo    TALOS API will start on port 8001.
echo    SYNAPSE bus is expected on port 8000.
echo.
pause
goto TOP

REM ---------------------------------------------------------------------------
REM Option 2: Start FastAPI Server (port 8001) -- Background Minimized Window
REM ---------------------------------------------------------------------------
:SERVER
cls
echo =============================================
echo    Starting TALOS FastAPI Server (v5.9.7)
echo    Port: 8001
echo    API Docs: http://localhost:8001/docs
echo    Health:   http://localhost:8001/api/v1/health
echo    Synapse:  http://localhost:8001/api/v1/synapse/webhook
echo =============================================
echo.
echo    Launching FastAPI server in a separate minimized window...
echo    Close the background window or press Ctrl+C there to stop.
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

REM -- Launch uvicorn in a new minimized window --
start "TALOS FastAPI Server" /min cmd /c "python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001"
echo.
echo [INFO] TALOS FastAPI server launched in background window.

REM -- Auto-start Fermion CPU server if FAST_EDGE_MODEL is Neutrino/local --
call :CHECK_FERMION

echo [INFO] Wait a few seconds then visit http://localhost:8001/docs
echo.
echo Press any key to return to the main menu...
pause >nul
goto TOP

REM ---------------------------------------------------------------------------
REM Option 3: Start MCP Server -- Background Minimized Window
REM ---------------------------------------------------------------------------
:MCP_SERVER
cls
echo =============================================
echo    Starting TALOS MCP Server (v5.9.7)
echo =============================================
echo.
echo    Launching MCP server in a separate minimized window...
echo    Close the background window or press Ctrl+C there to stop.
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

REM -- Launch MCP server in a new minimized window --
start "TALOS MCP Server" /min cmd /c "python src/mcp_server.py"
echo.
echo [INFO] TALOS MCP server launched in background window.
echo.
echo Press any key to return to the main menu...
pause >nul
goto TOP

REM ---------------------------------------------------------------------------
REM Option 4: Launch Interim UI (Cherry Studio) -- Auto-Start Backend Chain
REM ---------------------------------------------------------------------------
:PROVISION_UI
cls
echo =============================================
echo    Interim UI Provisioner (Cherry Studio)
echo    Auto-Start Chain: FastAPI Backend -> UI
echo =============================================
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

REM -- Step 1: Start FastAPI server in a background minimized window --
echo [1/3] Starting TALOS FastAPI server in background (port 8001)...
start "TALOS FastAPI Server" /min cmd /c "python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001"
echo [INFO] FastAPI server launched in background window.

REM -- Step 2: Wait for server to initialize --
echo [2/3] Waiting 2 seconds for server to initialize...
timeout /t 2 /nobreak >nul
echo [INFO] Wait complete.

REM -- Step 3: Run the frontend provisioner --
echo [3/3] Running Frontend Provisioner...
python src/utils/frontend_provisioner.py %*

echo.
echo =============================================
echo    Provisioning complete.
echo    FastAPI server running in background on port 8001.
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
echo    TALOS Terminal CLI (v5.9.7)
echo =============================================
echo.
echo    Launching the interactive TALOS command-line interface.
echo    Press Ctrl+C to exit back to this menu.
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

REM -- Launch talos.py CLI --
python talos.py
goto TOP

REM ---------------------------------------------------------------------------
REM Option 6: Autonomous Research Daemon (24/7 Service)
REM ---------------------------------------------------------------------------
:DAEMON
cls
echo =============================================
echo    Autonomous Research Daemon (v5.9.7)
echo    24/7 Background Research Service
echo =============================================
echo.
echo    This daemon continuously discovers, evaluates, and enriches
echo    research papers in the background. It runs until interrupted.
echo.
echo    Press Ctrl+C to stop the daemon and return to this menu.
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

REM -- Launch talos_service.py --
python src/ai/drl/talos_service.py
goto TOP

REM ---------------------------------------------------------------------------
REM Option 7: Live DRL Agent
REM ---------------------------------------------------------------------------
:LIVE_DRL
cls
echo =============================================
echo    Live DRL Agent (v5.9.7)
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
call :ACTIVATE_CONDA

REM -- Launch talos_live_agent.py with verbose flag --
python src/ai/drl/talos_live_agent.py --verbose
goto TOP

REM ---------------------------------------------------------------------------
REM Option 8: Autonomous System Tester (RL Chaos Fuzzer)
REM ---------------------------------------------------------------------------
:AUTO_TESTER
cls
echo =============================================
echo    Autonomous System Tester (v5.9.7)
echo    RL-Driven Chaos Engineering with LLM-as-a-Judge
echo =============================================
echo.
echo    Stress-tests TALOS system components using a Non-Stationary
echo    Epsilon-Greedy Multi-Armed Bandit. Diagnoses crashes with the
echo    Fast Edge LLM and saves Markdown reports in data/reports/autonomous_tester/.
echo.
echo    Dynamic target discovery: all .py files under src/ are registered
echo    as test arms (70+ targets). Q-table saved to data/tester_q_table.json.
echo.
echo    Press Ctrl+C to abort the test run early.
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

REM -- Launch autonomous tester --
python src/ai/testing/autonomous_tester.py %*
goto TOP

REM ---------------------------------------------------------------------------
REM Option 9: Run Test Suite
REM ---------------------------------------------------------------------------
:TEST
cls
echo =============================================
echo    Running TALOS Test Suite (pytest)
echo =============================================
echo.

REM -- Activate conda environment first --
call :ACTIVATE_CONDA

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

REM ===========================================================================
REM -- Fermion Auto-Start Subroutine --
REM Reads .env for FAST_EDGE_MODEL; if it contains "Neutrino" or equals
REM "local", spawns fermion serve in a background minimized window.
REM ===========================================================================
:CHECK_FERMION
REM -- Parse .env file for FAST_EDGE_MODEL --
if not exist ".env" goto :EOF
for /f "tokens=1,2 delims==" %%a in ('type .env 2^>nul') do (
    if "%%a"=="FAST_EDGE_MODEL" set "FAST_EDGE=%%b"
)
if not defined FAST_EDGE goto :EOF
echo %FAST_EDGE% | findstr /i "Neutrino" >nul
if %ERRORLEVEL% equ 0 goto :FERMION_START
echo %FAST_EDGE% | findstr /i "local" >nul
if %ERRORLEVEL% equ 0 goto :FERMION_START
goto :EOF

:FERMION_START
echo.
echo [FERMION] Fast Edge model requires CPU accelerator -- starting fermion serve...
echo [FERMION] Model: %FAST_EDGE% on port 11435
start "TALOS Fast Edge Server" /min cmd /c "fermion serve --port 11435"
echo [FERMION] Background window launched (minimized).
echo [FERMION] Waiting 2 seconds for engine initialization...
timeout /t 2 /nobreak >nul
echo [FERMION] Fast Edge engine ready on port 11435.
goto :EOF

REM ---------------------------------------------------------------------------
REM Option 10: Exit
REM ---------------------------------------------------------------------------
:END
echo.
echo =============================================
echo    Closing Project TALOS v5.9.7...
echo =============================================
exit /b
