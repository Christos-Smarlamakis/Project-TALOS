@echo off
setlocal EnableDelayedExpansion
title Project TALOS v5.10.6 -- Research Intelligence Dashboard

REM ---------------------------------------------------------------------------
REM [ INIT ] Enforce Terminal Viewport Dimensions
REM Width: 105, Height: 32. Ensures NO SCROLLBAR appears and logo stays at top.
REM ---------------------------------------------------------------------------
mode con: cols=105 lines=32

chcp 65001 >nul 2>&1

REM ===========================================================================
REM script         : run_talos.bat
REM version        : v5.10.6 (Universal Dynamic Model Provisioner & Self-Healing Redundancy Engine)
REM description    : Advanced System Dashboard and Execution Matrix for Project TALOS.
REM                  Implements Two-Column UI, IEEE WEIGD standard telemetry,
REM                  defensive error handling, solid-block Unicode rendering,
REM                  and Automated Zero-Click Miniconda Provisioning.
REM ===========================================================================

REM ---------------------------------------------------------------------------
REM [ INIT ] ANSI Escape Character Generator for True Color Support
REM ---------------------------------------------------------------------------
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

REM ---------------------------------------------------------------------------
REM [ INIT ] Color Palette Definition (IEEE WEIGD Compliance)
REM ---------------------------------------------------------------------------
set "C_RESET=%ESC%[0m"
set "C_IEEE_LIGHT=%ESC%[38;2;0;102;153m"
set "C_IEEE_DARK=%ESC%[38;2;0;28;85m"
set "C_GREEN=%ESC%[38;2;40;167;69m"
set "C_RED=%ESC%[38;2;220;53;69m"
set "C_YELLOW=%ESC%[38;2;255;193;7m"
set "C_CYAN=%ESC%[38;2;23;162;184m"

REM ---------------------------------------------------------------------------
REM [ INIT ] Dynamic Conda Environment Discovery
REM ---------------------------------------------------------------------------
set "CONDA_ACTIVATE_PATH="
set "CONDA_PATHS=%USERPROFILE%\miniconda3 %USERPROFILE%\anaconda3 C:\ProgramData\miniconda3 C:\ProgramData\anaconda3 %LOCALAPPDATA%\Continuum\anaconda3"

for %%p in (%CONDA_PATHS%) do (
    if exist "%%p\Scripts\activate.bat" (
        set "CONDA_ACTIVATE_PATH=%%p\Scripts\activate.bat"
        goto :CONDA_FOUND
    )
)
:CONDA_FOUND

REM Jump to main loop to bypass subroutines during initialization
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
    if %ERRORLEVEL% neq 0 call conda activate talosenv >nul 2>&1
) else (
    call conda activate talosenv >nul 2>&1
)
goto :EOF

:CHECK_PORT_SILENT
netstat -ano | findstr "LISTENING" | findstr ":%~1" >nul
if %ERRORLEVEL% equ 0 ( set "%~2=%C_GREEN%ONLINE%C_RESET%" ) else ( set "%~2=%C_RED%OFFLINE%C_RESET%" )
goto :EOF

REM ===========================================================================
REM MAIN DASHBOARD (Two-Column User Interface)
REM ===========================================================================
:MAIN_MENU
cls
REM -- Live Port Status Telemetry --
call :CHECK_PORT_SILENT 8001 API_STATUS
call :CHECK_PORT_SILENT 8000 SYNAPSE_STATUS
call :CHECK_PORT_SILENT 11435 EDGE_STATUS

echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo %C_IEEE_LIGHT%          ████████  █████  ██       ██████  ██████ %C_RESET%
echo %C_IEEE_LIGHT%             ██    ██   ██ ██      ██    ██ ██      %C_RESET%
echo %C_IEEE_LIGHT%             ██    ███████ ██      ██    ██ ██████  %C_RESET%
echo %C_IEEE_LIGHT%             ██    ██   ██ ██      ██    ██     ██  %C_RESET%
echo %C_IEEE_LIGHT%             ██    ██   ██ ███████  ██████  ██████  %C_RESET%
echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo  %C_CYAN%Project TALOS v5.10.6 -- Research Intelligence Ecosystem (IEEE WEIGD Supported)%C_RESET%
echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo  [ SYSTEM TELEMETRY ]    API (8001): %API_STATUS%   ^|   BUS (8000): %SYNAPSE_STATUS%   ^|   EDGE (11435): %EDGE_STATUS%
echo %C_IEEE_DARK%-----------------------------------------------------------------------------------------------------%C_RESET%
echo  %C_IEEE_LIGHT%[ INFRASTRUCTURE ^& UI ]%C_RESET%                       %C_IEEE_LIGHT%[ REASONING AGENTS ]%C_RESET%
echo  [1] Full Setup (Auto-Conda + Pip + UI)       [5] TALOS Console (Interactive CLI)
echo  [2] Start FastAPI Server (Background)        [6] Autonomous Research Daemon (24/7)
echo  [3] Start MCP Server (Background)            [7] Live DRL Agent (Verbose Output)
echo  [4] Launch UI (Cherry Studio Provisioner)
echo.
echo  %C_IEEE_LIGHT%[ TESTING ^& MAINTENANCE ]%C_RESET%
echo  [8] Autonomous Red Tester (RL Chaos Fuzzer)   [10] Terminate Session
echo  [9] Execute Test Framework (Pytest Suite)
echo %C_IEEE_DARK%=====================================================================================================%C_RESET%
echo.

set /p choice="  %C_CYAN%Select Operational Directive [1-10]:%C_RESET% "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto SERVER
if "%choice%"=="3" goto MCP_SERVER
if "%choice%"=="4" goto PROVISION_UI
if "%choice%"=="5" goto CLI
if "%choice%"=="6" goto DAEMON
if "%choice%"=="7" goto LIVE_DRL
if "%choice%"=="8" goto AUTO_TESTER
if "%choice%"=="9" goto TEST
if "%choice%"=="10" exit /b
goto MAIN_MENU

REM ===========================================================================
REM EXECUTION MATRICES
REM ===========================================================================

:SETUP
cls
call :LOG_INFO "Initiating Global Setup Sequence..."
call :LOG_INFO "Validating Conda environment paths..."
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 if not defined CONDA_ACTIVATE_PATH (
    call :LOG_WARN "Conda distribution not found on system PATH."
    call :LOG_INFO "Initiating Automated Zero-Click Miniconda3 Deployment..."
    
    REM Auto-Download Miniconda
    call :LOG_INFO "Downloading Miniconda3 installer. Please wait..."
    curl -# -k -o miniconda_installer.exe https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    if %ERRORLEVEL% neq 0 (
        call :LOG_ERROR "Network failure during download. Please check internet connection."
        pause
        goto MAIN_MENU
    )
    
    REM Silent Installation
    call :LOG_INFO "Executing silent background installation to %USERPROFILE%\miniconda3..."
    start /wait "" miniconda_installer.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3
    
    REM Environment Assignment & Cleanup
    set "CONDA_ACTIVATE_PATH=%USERPROFILE%\miniconda3\Scripts\activate.bat"
    del miniconda_installer.exe >nul 2>&1
    call :LOG_SUCCESS "Miniconda3 subsystem successfully installed."
)

call :LOG_INFO "Provisioning 'talosenv' runtime (Python 3.11)..."
if defined CONDA_ACTIVATE_PATH (
    call "%CONDA_ACTIVATE_PATH%" && conda create -n talosenv python=3.11 -y >nul 2>&1
) else (
    call conda create -n talosenv python=3.11 -y >nul 2>&1
)
call :ACTIVATE_CONDA

call :LOG_INFO "Resolving and installing Python dependencies..."
pip install -r requirements.txt >nul
if %ERRORLEVEL% neq 0 (
    call :LOG_ERROR "Dependency resolution failed. Halting setup."
    pause
    goto MAIN_MENU
)
call :LOG_SUCCESS "All dependencies successfully integrated."

call :LOG_INFO "Triggering Frontend Provisioner..."
python src/utils/frontend_provisioner.py

echo [5/5] Provisioning Local AI Models (Universal Model Provisioner)...
call :LOG_INFO "Executing Universal Dynamic Model Provisioner (fast edge + heavy models)..."
python src/utils/model_provisioner.py

call :LOG_SUCCESS "TALOS v5.10.6 deployment finalized."
pause
goto MAIN_MENU

:SERVER
cls
netstat -ano | findstr "LISTENING" | findstr ":8001" >nul
if %ERRORLEVEL% equ 0 (
    call :LOG_WARN "Port 8001 is engaged. FastAPI Server is already operational."
    pause
    goto MAIN_MENU
)
call :LOG_INFO "Bootstrapping FastAPI Microservice..."
call :ACTIVATE_CONDA
start "TALOS FastAPI Server (8001)" /min cmd /c "python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001"
call :LOG_SUCCESS "Microservice dispatched to background (Port: 8001)."
call :CHECK_EDGE_SERVER
pause >nul
goto MAIN_MENU

:MCP_SERVER
cls
call :LOG_INFO "Bootstrapping MCP Server..."
call :ACTIVATE_CONDA
start "TALOS MCP Server" /min cmd /c "python src/mcp_server.py"
call :LOG_SUCCESS "MCP Server operational in background."
pause >nul
goto MAIN_MENU

:PROVISION_UI
cls
call :LOG_INFO "Validating Backend Data Stream..."
netstat -ano | findstr "LISTENING" | findstr ":8001" >nul
if %ERRORLEVEL% equ 0 (
    call :LOG_SUCCESS "FastAPI Server detected."
) else (
    call :LOG_INFO "FastAPI offline. Auto-starting backend..."
    call :ACTIVATE_CONDA
    start "TALOS FastAPI Server (8001)" /min cmd /c "python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001"
    timeout /t 2 /nobreak >nul
)
call :LOG_INFO "Deploying React User Interface..."
call :ACTIVATE_CONDA
python src/utils/frontend_provisioner.py %*
pause
goto MAIN_MENU

:CLI
cls
call :LOG_INFO "Initializing Terminal Interactive Mode..."
call :ACTIVATE_CONDA
python talos.py
goto MAIN_MENU

:DAEMON
cls
call :LOG_INFO "Engaging Autonomous Research Daemon..."
call :ACTIVATE_CONDA
python src/ai/drl/talos_service.py
goto MAIN_MENU

:LIVE_DRL
cls
call :LOG_INFO "Engaging Deep Reinforcement Learning Agent..."
call :ACTIVATE_CONDA
python src/ai/drl/talos_live_agent.py --verbose
goto MAIN_MENU

:AUTO_TESTER
cls
call :LOG_INFO "Deploying Autonomous Red Tester (RL Chaos Fuzzer)..."
call :ACTIVATE_CONDA
python src/ai/testing/red_tester.py %*
pause
goto MAIN_MENU

:TEST
cls
call :LOG_INFO "Executing Comprehensive Pytest Suite..."
call :ACTIVATE_CONDA
python -m pytest --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :LOG_WARN "Pytest framework absent. Initializing installation..."
    pip install pytest >nul 2>&1
)
python -m pytest -v --tb=short 2>&1
if %ERRORLEVEL% equ 0 (
    call :LOG_SUCCESS "System validation passed. Zero errors detected."
) else (
    call :LOG_ERROR "System validation failed. Refer to stack trace above."
)
pause
goto MAIN_MENU

:CHECK_EDGE_SERVER
if not exist ".env" goto :EOF
for /f "tokens=1,2 delims==" %%a in ('type .env 2^>nul') do (
    if "%%a"=="FAST_EDGE_MODEL" set "FAST_EDGE=%%b"
)
if not defined FAST_EDGE goto :EOF
echo %FAST_EDGE% | findstr /i "Neutrino local" >nul
if %ERRORLEVEL% neq 0 goto :EOF

netstat -ano | findstr "LISTENING" | findstr ":11435" >nul
if %ERRORLEVEL% neq 0 (
    call :LOG_INFO "Bootstrapping Fast Edge CPU server..."
    start "TALOS Fast Edge Server" /min cmd /c "python -m llama_cpp.server --port 11435"
    timeout /t 2 /nobreak >nul
)
goto :EOF