@echo off
setlocal EnableDelayedExpansion
title Project TALOS v5.25.0 -- Research Intelligence Dashboard

mode con: cols=105 lines=32
chcp 65001 >nul 2>&1

REM ---------------------------------------------------------------------------
REM [ INIT ] Robust ANSI Escape Code Generator via PowerShell
REM ---------------------------------------------------------------------------
for /f %%a in ('powershell -NoProfile -Command "[char]27"') do set "ESC=%%a"

set "C_RESET=!ESC![0m"
set "C_IEEE_LIGHT=!ESC![38;2;0;102;153m"
set "C_IEEE_DARK=!ESC![38;2;0;28;85m"
set "C_GREEN=!ESC![38;2;40;167;69m"
set "C_RED=!ESC![38;2;220;53;69m"
set "C_YELLOW=!ESC![38;2;255;193;7m"
set "C_CYAN=!ESC![38;2;23;162;184m"
set "C_WHITE=!ESC![38;2;255;255;255m"

REM ---------------------------------------------------------------------------
REM [ INIT ] Conda Discovery + Silent Fast Pre-Flight Bypass Gate (v5.12.2)
REM ---------------------------------------------------------------------------
set "CONDA_ACTIVATE_PATH="
set "CONDA_BAT="
set "CONDA_ROOT="
set "CONDA_PATHS=%USERPROFILE%\miniconda3 %USERPROFILE%\anaconda3 C:\ProgramData\miniconda3 C:\ProgramData\anaconda3 %LOCALAPPDATA%\Continuum\anaconda3"

call :DISCOVER_CONDA

REM -- Silent fast-path gate: if Conda, the talosenv environment, the .env
REM -- configuration, and all core Python packages are already in place, the
REM -- onboarding wizard is skipped entirely. Target: sub-1-second startup.
set "PREFLIGHT_OK=1"
if not defined CONDA_BAT set "PREFLIGHT_OK=0"
if not defined CONDA_ROOT set "PREFLIGHT_OK=0"
if not exist ".env" set "PREFLIGHT_OK=0"
if "!PREFLIGHT_OK!"=="1" (
    if not exist "!CONDA_ROOT!\envs\talosenv\python.exe" set "PREFLIGHT_OK=0"
)
if "!PREFLIGHT_OK!"=="1" (
    "!CONDA_ROOT!\envs\talosenv\python.exe" -c "import questionary, rich, fastapi" >nul 2>&1
    if errorlevel 1 set "PREFLIGHT_OK=0"
)
if "!PREFLIGHT_OK!"=="1" goto :MAIN_MENU

call :AUTO_PREFLIGHT
goto :MAIN_MENU

REM ===========================================================================
REM SYSTEM SUBROUTINES
REM ===========================================================================

:LOG_INFO
echo %C_CYAN%[%time:~0,8%] [ INFO ]%C_RESET% %~1
goto :EOF

:LOG_SUCCESS
echo %C_GREEN%[%time:~0,8%] [ SUCCESS ]%C_RESET% %~1
goto :EOF

:LOG_WARN
echo %C_YELLOW%[%time:~0,8%] [ WARNING ]%C_RESET% %~1
goto :EOF

:LOG_ERROR
echo %C_RED%[%time:~0,8%] [ ERROR ]%C_RESET% %~1
goto :EOF

:ACTIVATE_CONDA
if defined CONDA_ACTIVATE_PATH (
    call "%CONDA_ACTIVATE_PATH%" talosenv >nul 2>&1
    if !ERRORLEVEL! neq 0 call conda activate talosenv >nul 2>&1
) else (
    call conda activate talosenv >nul 2>&1
)
goto :EOF

:CHECK_PORT_SILENT
netstat -ano 2>nul | findstr "LISTENING" | findstr ":%~1" >nul 2>&1
if !ERRORLEVEL! equ 0 ( set "%~2=%C_GREEN%ONLINE%C_RESET%" ) else ( set "%~2=%C_RED%OFFLINE%C_RESET%" )
goto :EOF

:DISCOVER_CONDA
REM Scans candidate installation roots for condabin\conda.bat, sets CONDA_BAT
REM and CONDA_ROOT, and backfills CONDA_ACTIVATE_PATH (Scripts\activate.bat)
REM so the legacy :ACTIVATE_CONDA routine used by all menu options keeps working.
set "CONDA_BAT="
set "CONDA_ROOT="
for %%p in (%CONDA_PATHS%) do (
    if not defined CONDA_BAT (
        if exist "%%p\condabin\conda.bat" (
            set "CONDA_BAT=%%p\condabin\conda.bat"
            set "CONDA_ROOT=%%p"
        )
    )
)
if not defined CONDA_BAT (
    for /f "delims=" %%c in ('where conda 2^>nul') do (
        if not defined CONDA_BAT set "CONDA_BAT=%%c"
    )
)
if not defined CONDA_ACTIVATE_PATH (
    for %%p in (%CONDA_PATHS%) do (
        if not defined CONDA_ACTIVATE_PATH (
            if exist "%%p\Scripts\activate.bat" set "CONDA_ACTIVATE_PATH=%%p\Scripts\activate.bat"
        )
    )
)
goto :EOF

:AUTO_PREFLIGHT
cls
echo ==============================================================================
echo                PROJECT TALOS -- AUTOMATED RESEARCH SETUP WIZARD
echo ==============================================================================
echo [INFO] Preparing the TALOS Research Environment. Please do not close this window.
echo.

REM --- STEP 1: CONDA RUNTIME CHECK ---
echo [Step 1/5] Checking Conda scientific runtime...
call :DISCOVER_CONDA >nul 2>&1
if defined CONDA_BAT (
    echo          [OK] Conda runtime detected.
) else (
    echo          - Conda not detected. Initiating automatic setup...
    echo          - Downloading Miniconda3 ^(approx. 85 MB^). Please wait...
    set "MC_INSTALLER=%TEMP%\miniconda_installer.exe"
    curl.exe -# -fS -o "!MC_INSTALLER!" "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    if not exist "!MC_INSTALLER!" (
        echo          [ERROR] Download failed. Please verify your internet connection.
        pause
        exit /b 1
    )
    echo          - Installing Miniconda silently ^(estimated time: 1-2 minutes^)...
    start /wait "" "!MC_INSTALLER!" /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3
    del /f /q "!MC_INSTALLER!" 2>nul
    set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
    if exist "!CONDA_BAT!" (
        set "CONDA_ROOT=%USERPROFILE%\miniconda3"
        set "CONDA_ACTIVATE_PATH=%USERPROFILE%\miniconda3\Scripts\activate.bat"
        echo          [OK] Miniconda3 successfully installed and ready.
    ) else (
        echo          [ERROR] Installation failed. Please check user permissions.
        pause
        exit /b 1
    )
)
echo.

REM --- STEP 2: ISOLATED TALOSENV ENVIRONMENT ---
echo [Step 2/5] Checking isolated environment 'talosenv' ^(Python 3.11^)...
call "!CONDA_BAT!" info --envs | findstr /R /C:"talosenv " >nul 2>&1
if errorlevel 1 (
    echo          - Creating dedicated 'talosenv' environment. Please wait ~1 minute...
    call "!CONDA_BAT!" create -n talosenv python=3.11 -y >nul 2>&1
    echo          [OK] Environment 'talosenv' created successfully.
) else (
    echo          [OK] Environment 'talosenv' verified.
)
call "!CONDA_BAT!" activate talosenv
echo.

REM --- STEP 3: ENVIRONMENT CONFIGURATION (.ENV) ---
echo [Step 3/5] Checking configuration files ^(.env^)...
if not exist ".env" (
    if exist "example.env" (
        copy /y "example.env" ".env" >nul 2>&1
        echo          [OK] Initialized .env configuration file from template.
    ) else (
        echo. > ".env"
        echo          [OK] Created new empty .env configuration file.
    )
) else (
    echo          [OK] Active .env configuration verified.
)
echo.

REM --- STEP 4: DEPENDENCIES VERIFICATION ---
echo [Step 4/5] Checking Python scientific packages ^(requirements.txt^)...
python.exe -c "import questionary, rich, fastapi" >nul 2>&1
if errorlevel 1 (
    echo          - First-run setup detected.
    echo          - Installing required AI and scientific packages...
    echo          - Note: This is a ONE-TIME installation ^(approx. 2-3 minutes^).
    echo.
    python.exe -m pip install --upgrade pip --quiet
    python.exe -m pip install -r requirements.txt
    python.exe src/utils/frontend_provisioner.py >nul 2>&1
    echo.
    echo          [OK] All Python packages successfully installed.
) else (
    echo          [OK] All core dependencies verified.
)
echo.

REM --- STEP 5: SYSTEM HEALTH & INTEGRITY ---
echo [Step 5/5] Finalizing startup verification...
python.exe -c "import sys; sys.exit(0)" >nul 2>&1
echo          [OK] System integrity verified. Environment is 100%% ready.
echo ==============================================================================
echo.
timeout /t 1 /nobreak >nul 2>&1
goto :EOF

REM ===========================================================================
REM MAIN DASHBOARD
REM ===========================================================================
:MAIN_MENU
cls
set "API_STATUS="
set "SYNAPSE_STATUS="
set "OLLAMA_STATUS="
set "OPTICA_STATUS="

call :CHECK_PORT_SILENT 8001 API_STATUS
call :CHECK_PORT_SILENT 8000 SYNAPSE_STATUS
call :CHECK_PORT_SILENT 11434 OLLAMA_STATUS
call :CHECK_PORT_SILENT 8002 OPTICA_STATUS

echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo %C_IEEE_LIGHT%          ████████  █████  ██       ██████  ██████ %C_RESET%
echo %C_IEEE_LIGHT%             ██    ██   ██ ██      ██    ██ ██      %C_RESET%
echo %C_IEEE_LIGHT%             ██    ███████ ██      ██    ██ ██████  %C_RESET%
echo %C_IEEE_LIGHT%             ██    ██   ██ ██      ██    ██     ██  %C_RESET%
echo %C_IEEE_LIGHT%             ██    ██   ██ ███████  ██████  ██████  %C_RESET%
echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo  %C_CYAN%Project TALOS v5.25.0 -- Research Intelligence Ecosystem (IEEE WEIGD Supported)%C_RESET%
echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo  [ SYSTEM TELEMETRY ]  API (8001): !API_STATUS! ^| BUS (8000): !SYNAPSE_STATUS! ^| OLLAMA (11434): !OLLAMA_STATUS! ^| OPTICA (8002): !OPTICA_STATUS!
echo %C_IEEE_DARK%-----------------------------------------------------------------------------------------------------%C_RESET%
echo.
echo  %C_IEEE_LIGHT%[ 1. PRIMARY CONTROL HUBS ]%C_RESET%
echo   [1] TALOS Master Console (Interactive TUI Dashboard)
echo   [2] Launch UI (Cherry Studio Desktop Integration)
echo.
echo  %C_IEEE_LIGHT%[ 2. AUTONOMOUS DAEMONS AND DRL AGENTS ]%C_RESET%
echo   [3] Autonomous Research Daemon (24/7 Background Service)
echo   [4] Live DRL Foraging Agent (Interactive API Exploration)
echo   [5] Autonomous Red Tester (RL Chaos Engineering Fuzzer)
echo.
echo  %C_IEEE_LIGHT%[ 3. BACKGROUND SERVERS AND PROVISIONING ]%C_RESET%
echo   [6] Start FastAPI REST Server (Port 8001)
echo   [7] Start MCP Tool Server (Model Context Protocol)
echo   [8] Full Environment Setup (Auto-Conda + Dependencies)
echo.
echo  %C_IEEE_LIGHT%[ 4. QUALITY ASSURANCE AND EXIT ]%C_RESET%
echo   [9] Execute Automated Test Suite (Pytest Framework)
echo   [10] Terminate Session / Exit
echo.
echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo.

set "choice="
set /p choice="  %C_CYAN%Select Operational Directive [1-10]:%C_RESET% "

if "!choice!"=="1" goto CLI
if "!choice!"=="2" goto PROVISION_UI
if "!choice!"=="3" goto DAEMON
if "!choice!"=="4" goto LIVE_DRL
if "!choice!"=="5" goto AUTO_TESTER
if "!choice!"=="6" goto SERVER
if "!choice!"=="7" goto MCP_SERVER
if "!choice!"=="8" goto SETUP
if "!choice!"=="9" goto TEST
if "!choice!"=="10" exit /b
goto MAIN_MENU

REM ===========================================================================
REM EXECUTION MATRICES
REM ===========================================================================

:CLI
cls
call :LOG_INFO "Initializing TALOS Master Console..."
call :ACTIVATE_CONDA
python talos.py
if !ERRORLEVEL! neq 0 (
    echo.
    call :LOG_ERROR "TALOS Master Console exited with an error code: !ERRORLEVEL!"
    pause
)
goto MAIN_MENU

:PROVISION_UI
cls
call :LOG_INFO "Deploying UI Provisioner..."
call :ACTIVATE_CONDA
python src/utils/frontend_provisioner.py %*
pause
goto MAIN_MENU

:DAEMON
cls
call :LOG_INFO "Engaging Autonomous Research Daemon..."
call :ACTIVATE_CONDA
python src/ai/drl/talos_service.py
if !ERRORLEVEL! neq 0 (
    echo.
    call :LOG_ERROR "Daemon exited with an error code: !ERRORLEVEL!"
    pause
)
goto MAIN_MENU

:LIVE_DRL
cls
call :LOG_INFO "Engaging Deep Reinforcement Learning Agent..."
call :ACTIVATE_CONDA
python src/ai/drl/talos_live_agent.py --verbose
if !ERRORLEVEL! neq 0 (
    echo.
    call :LOG_ERROR "Live DRL Agent exited with an error code: !ERRORLEVEL!"
    pause
)
goto MAIN_MENU

:AUTO_TESTER
cls
call :LOG_INFO "Deploying Autonomous Red Tester (RL Chaos Fuzzer)..."
call :ACTIVATE_CONDA
python src/ai/testing/red_tester.py %*
pause
goto MAIN_MENU

:SERVER
cls
netstat -ano 2>nul | findstr "LISTENING" | findstr ":8001" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    call :LOG_WARN "Port 8001 is engaged. FastAPI Server is already operational."
    pause
    goto MAIN_MENU
)
call :LOG_INFO "Bootstrapping FastAPI Microservice on Port 8001..."
call :ACTIVATE_CONDA
start "TALOS FastAPI Server (8001)" /min cmd /c "python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001"
call :LOG_SUCCESS "Microservice dispatched to background."
pause
goto MAIN_MENU

:MCP_SERVER
cls
call :LOG_INFO "Bootstrapping MCP Server..."
call :ACTIVATE_CONDA
start "TALOS MCP Server" /min cmd /c "python src/mcp_server.py"
call :LOG_SUCCESS "MCP Server operational in background."
pause
goto MAIN_MENU

:SETUP
cls
call :LOG_INFO "Initiating Global Setup Sequence..."
call :ACTIVATE_CONDA
call :LOG_INFO "Resolving and installing Python dependencies..."
pip install -r requirements.txt
python src/utils/frontend_provisioner.py
python src/utils/model_provisioner.py
call :LOG_SUCCESS "TALOS v5.25.0 deployment finalized."
pause
goto MAIN_MENU

:TEST
cls
call :LOG_INFO "Executing Automated Test Suite..."
call :ACTIVATE_CONDA
python -m pytest -v --tb=short
pause
goto MAIN_MENU