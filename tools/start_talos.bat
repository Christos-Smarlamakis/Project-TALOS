@echo off
title Project TALOS v5.4.0 Launcher

REM Activate the conda environment
call C:\ProgramData\miniconda3\Scripts\activate.bat talosenv
IF ERRORLEVEL 1 (
    echo [ERROR] Could not activate talosenv conda environment.
    echo Please ensure Miniconda/Anaconda is installed at C:\ProgramData\miniconda3
    echo or edit this batch file to point to the correct path.
    pause
    exit /b 1
)

:MENU
cls
echo =============================================
echo    Project TALOS v5.4.0
echo    Research Intelligence Platform
echo =============================================
echo.
echo    [1] CLI Menu (Terminal)
echo    [2] Web GUI (Streamlit - Recommended)
echo    [3] Legacy Dashboard (Flask)
echo    [4] Generate Baseline Report
echo    [5] Autonomous Research Service (24/7)
echo    [6] Live DRL Agent (Real APIs)
echo    [7] Exit
echo.
set /p choice="    Select mode [1-7]: "

if "%choice%"=="1" goto CLI
if "%choice%"=="2" goto GUI
if "%choice%"=="3" goto DASHBOARD
if "%choice%"=="4" goto REPORT
if "%choice%"=="5" goto SERVICE
if "%choice%"=="6" goto LIVEAGENT
if "%choice%"=="7" goto END
goto MENU

:CLI
cls
python ..\talos.py
goto MENU

:GUI
cls
echo =============================================
echo    Starting TALOS Web GUI...
echo    Open: http://localhost:8501
echo    Press Ctrl+C to stop
echo =============================================
echo.
python -m streamlit run ..\app.py --server.port 8501
goto MENU

:DASHBOARD
cls
echo =============================================
echo    Starting Legacy Dashboard...
echo    Open: http://localhost:5000
echo =============================================
python ..\src\utils\interactive_dashboard.py
goto MENU

:REPORT
cls
echo =============================================
echo    Generating Baseline Report...
echo =============================================
python ..\src\analysis\generate_baseline_report.py --academic
echo.
echo    Report saved to reports\general_status_report\
echo.
pause
goto MENU

:SERVICE
cls
echo =============================================
echo    Starting Autonomous Research Service...
echo    Press Ctrl+C to stop
echo =============================================
python ..\src\ai\drl\talos_service.py
goto MENU

:LIVEAGENT
cls
echo =============================================
echo    Starting Live DRL Agent (Real APIs)...
echo    ⚠️  This makes REAL API calls.
echo    Press Ctrl+C to stop
echo =============================================
python ..\src\ai\drl\talos_live_agent.py --verbose
goto MENU

:END
echo.
echo =============================================
echo    Closing Project TALOS...
echo =============================================
REM Deactivate the conda environment gracefully
call conda deactivate 2>nul
exit /b