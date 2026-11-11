"""PyInstaller-Build: erzeugt die Single-.exe des Zeitnehmungs-Systems.

Verwendung:
    python scripts/build_exe.py

Ergebnis:
    dist/Wasserski-Zeitnehmung.exe   (eine Datei, kein Python beim Kunden)

Build-Parameter (AGENTS.md §11):
    --onefile --noconsole            → eine .exe ohne Konsolenfenster
    --add-data "app_settings.json;config"
                                     → App-Konfiguration liegt im Bundle;
                                       beim ersten Start kopiert die App sie
                                       neben die .exe (editierbar, siehe
                                       python/config/app_config.py)
    --hidden-import keyboard         → wird in input_handler.py erst zur
                                       Laufzeit importiert (lazy) – ohne
                                       diesen Hinweis fehlt die Library
                                       in der .exe!
    --collect-all customtkinter      → CustomTkinter-Assets (Bilder,
                                       Titelbar-Themes) vollständig bündeln

Hinweis zum Testen: Die .exe startet ohne Administrator-Rechte ohne
systemweite Hotkeys. Als Admin (Start_Zeitnehmung_Admin.cmd nutzt den
Quellcode) startet sie mit Hotkeys. Ohne Datenquelle (IMPORT.json oder
Excel-Datei im Programmordner) erscheint eine Fehlermeldung – es gibt
keine Demo-Daten. Smoke-Test der .exe:
    dist/Wasserski-Zeitnehmung.exe 5    (Auto-Close nach 5 s)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "Wasserski-Zeitnehmung"
ENTRY = PROJECT_ROOT / "python" / "main.py"
SETTINGS_JSON = PROJECT_ROOT / "python" / "config" / "app_settings.json"


def _assert_dist_not_locked(exe: Path) -> None:
    """Prüft, ob die vorhandene .exe noch von der laufenden App gesperrt ist.

    PyInstaller entfernt die alte Datei im EXE-Schritt. Läuft die Anwendung
    noch, schlägt das mit ``PermissionError: [WinError 5] Zugriff verweigert``
    fehl (beobachtet 2026-11-09). Diese Prüfung liefert stattdessen eine
    verständliche Meldung, bevor der teure Build startet.

    Args:
        exe: Pfad zur bestehenden ``dist/Wasserski-Zeitnehmung.exe``.

    Raises:
        RuntimeError: wenn die Datei nicht zum Schreiben geöffnet werden kann.
    """
    if not exe.exists():
        return
    try:
        # "ab" prüft den Schreib-Lock, ohne Daten zu verändern.
        with open(exe, "ab"):
            pass
    except PermissionError as exc:
        raise RuntimeError(
            f"{exe.name} ist gesperrt – die Anwendung läuft noch. "
            "Bitte alle Fenster von 'Wasserski-Zeitnehmung' schließen "
            "und den Build erneut starten."
        ) from exc


def build() -> None:
    """Führt den PyInstaller-Build aus (blockierend, mit Live-Ausgabe)."""
    if not SETTINGS_JSON.exists():
        raise FileNotFoundError(
            f"app_settings.json nicht gefunden: {SETTINGS_JSON}")
    if not ENTRY.exists():
        raise FileNotFoundError(f"Einstiegspunkt nicht gefunden: {ENTRY}")

    exe = PROJECT_ROOT / "dist" / f"{APP_NAME}.exe"
    _assert_dist_not_locked(exe)

    # Windows-Trennzeichen für --add-data: "Quelle;Ziel" (im Bundle: /config)
    add_data = f"{SETTINGS_JSON};config"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--noconsole",
        "--name", APP_NAME,
        "--add-data", add_data,
        "--hidden-import", "keyboard",
        "--collect-all", "customtkinter",
        str(ENTRY),
    ]
    print(f"Starte PyInstaller-Build ...\n  {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"PyInstaller fehlgeschlagen (Code {result.returncode})")

    exe = PROJECT_ROOT / "dist" / f"{APP_NAME}.exe"
    if not exe.exists():
        raise RuntimeError(f".exe wurde nicht erzeugt: {exe}")
    size_mb = exe.stat().st_size / (1024 * 1024)
    print(f"\nBuild erfolgreich: {exe} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    try:
        build()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        sys.exit(1)
