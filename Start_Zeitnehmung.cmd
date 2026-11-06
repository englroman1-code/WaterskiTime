@echo off
chcp 65001 >nul
setlocal

rem ============================================================
rem  Wasserski-Zeitnehmung – normaler Start
rem  Startet die GUI (echte Renndaten) mit der virtuellen Umgebung.
rem  Optional: Argument = Sekunden bis Auto-Close (Screenshots).
rem ============================================================
cd /d "%~dp0"

echo.
echo ============================================
echo   Wasserski-Zeitnehmung
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo FEHLER: Virtuelle Umgebung .venv wurde nicht gefunden.
    echo Bitte einmalig einrichten:
    echo    python -m venv .venv
    echo    .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starte Anwendung ... bitte warten.
echo.
".venv\Scripts\python.exe" scripts\preview_gui.py %*

if errorlevel 1 (
    echo.
    echo Das Programm wurde mit einem Fehler beendet.
    echo Details siehe gui_startup.log im Projektordner.
)

echo.
echo Anwendung beendet.
pause
