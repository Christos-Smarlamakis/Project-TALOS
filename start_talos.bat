@echo off
title Project TALOS v4.10.0 Launcher

:CHECK_VENV
IF NOT EXIST "venv\" IF NOT EXIST ".venv\" (
    echo [INFO] First run: Creating Python Virtual Environment...
    python -m venv venv
    echo [INFO] Installing dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install streamlit
) ELSE (
    IF EXIST "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
    IF EXIST ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
)

:MENU
cls
echo =============================================
echo    Project TALOS v4.10.0
echo    Research Intelligence Platform
echo =============================================
echo.
echo    [1] CLI Menu (Terminal)
echo    [2] Web GUI (Streamlit - Recommended)
echo    [3] Legacy Dashboard (Flask)
echo    [4] Exit
echo.
set /p choice="    Select mode [1-4]: "

if "%choice%"=="1" goto CLI
if "%choice%"=="2" goto GUI
if "%choice%"=="3" goto DASHBOARD
if "%choice%"=="4" goto END
goto MENU

:CLI
cls
python talos.py
goto MENU

:GUI
cls
echo =============================================
echo    Starting TALOS Web GUI...
echo    Open: http://localhost:8501
echo    Press Ctrl+C to stop
echo =============================================
streamlit run app.py --server.port 8501
goto MENU

:DASHBOARD
cls
echo =============================================
echo    Starting Legacy Dashboard...
echo    Open: http://localhost:5000
echo =============================================
python scripts\interactive_dashboard.py
goto MENU

:END
deactivate
exit
