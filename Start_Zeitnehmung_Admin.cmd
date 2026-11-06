@echo off
chcp 65001 >nul
setlocal

rem ============================================================
rem  Wasserski-Zeitnehmung – Start mit SYSTEMWEITEN HOTKEYS
rem
rem  Die keyboard-Library benötigt Windows-Administrator-Rechte
rem  (AGENTS.md §10). Diese CMD hebt sich selbst per UAC-Abfrage
rem  auf Admin-Rechte an und startet dann mit --hotkeys.
rem  Optional: Argument = Sekunden bis Auto-Close (Screenshots).
rem ============================================================

rem --- Selbst-Elevation (UAC-Prompt) ---------------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Benötigt Administrator-Rechte – UAC-Abfrage startet ...
    if "%~1"=="" (
        powershell -NoProfile -Command "Start-Process -Verb RunAs -FilePath '%~f0'"
    ) else (
        powershell -NoProfile -Command "Start-Process -Verb RunAs -FilePath '%~f0' -ArgumentList '%*'"
    )
    exit /b
)

rem --- Ab hier: laufen wir mit Admin-Rechten ---------------------------
cd /d "%~dp0"

echo.
echo ============================================
echo   Wasserski-Zeitnehmung
echo   Systemweite Hotkeys AKTIV (Admin)
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
".venv\Scripts\python.exe" scripts\preview_gui.py --hotkeys %*

if errorlevel 1 (
    echo.
    echo Das Programm wurde mit einem Fehler beendet.
    echo Details siehe gui_startup.log im Projektordner.
)

echo.
echo Anwendung beendet.
pause
