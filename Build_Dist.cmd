@echo off
chcp 65001 >nul
setlocal

rem ============================================================
rem  Wasserski-Zeitnehmung – DIST (.exe) erzeugen
rem
rem  Baut die Single-.exe via PyInstaller (scripts/build_exe.py).
rem  Ergebnis: dist\Wasserski-Zeitnehmung.exe
rem
rem  Voraussetzungen:
rem    - .venv im Projekt-Root (python -m venv .venv)
rem    - Abhängigkeiten installiert (.venv\Scripts\pip install -r requirements.txt)
rem
rem  Hinweis: Vor dem Build wird der alte build\-Ordner und die
rem  .spec-Datei gelöscht (verhindert "Zugriff verweigert"-Fehler).
rem ============================================================

cd /d "%~dp0"

echo.
echo ============================================
echo   Wasserski-Zeitnehmung – Build der .exe
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

rem --- Alte Build-Artefakte bereinigen (verhindert Zugriff-verweigert) ---
if exist "build\Wasserski-Zeitnehmung" (
    echo Bereinige alten build-Ordner ...
    rmdir /s /q "build\Wasserski-Zeitnehmung"
)
if exist "Wasserski-Zeitnehmung.spec" (
    echo Lösche alte .spec-Datei ...
    del /q "Wasserski-Zeitnehmung.spec"
)

echo.
echo Starte PyInstaller-Build ... bitte warten.
echo.

".venv\Scripts\python.exe" scripts\build_exe.py

if errorlevel 1 (
    echo.
    echo FEHLER: Build fehlgeschlagen. Details siehe Ausgabe oben.
    echo.
    pause
    exit /b 1
)

echo.
echo Build abgeschlossen.
echo Ergebnis: dist\Wasserski-Zeitnehmung.exe
echo.
pause
