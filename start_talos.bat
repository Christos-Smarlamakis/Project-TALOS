@echo off
title Project TALOS Launcher
echo ==========================================
echo    Εκκίνηση Project TALOS...
echo ==========================================

IF NOT EXIST "venv" (
    echo [INFO] Πρωτη εκτελεση: Δημιουργια Python Virtual Environment...
    python -m venv venv
    echo [INFO] Εγκατασταση βιβλιοθηκων...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate.bat
)

IF NOT EXIST ".env" (
    echo [WARNING] Το αρχειο .env δεν βρεθηκε!
    copy env.example .env >nul
    echo Παρακαλω ανοιξτε το αρχειο .env και προσθεστε τα API Keys σας!
    pause
    exit
)

cls
python talos.py

deactivate
pause