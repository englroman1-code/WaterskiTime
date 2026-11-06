"""Produktions-Einstiegspunkt für die gebaute .exe (PyInstaller).

Verwendung:
    python python/main.py                    # GUI starten (Auto-Suche)
    python python/main.py 5                  # Auto-Close nach 5 s (Smoke-Test)
    python python/main.py --hotkeys          # systemweite Hotkeys (Admin!)
    python python/main.py --excel race.xlsx  # Excel mit Renndaten laden
    python python/main.py --json IMPORT.json # JSON (vom VBA-Makro) laden

Hinweise:
    - Entwicklungs-Start: scripts/preview_gui.py (identische Logik).
      Diese Datei ist der schlanke Einstieg für den PyInstaller-Build
      (scripts/build_exe.py, AGENTS.md §11: --onefile --noconsole).
    - Systemweite Hotkeys benötigen Windows-Admin (AGENTS.md §10):
      bequemer Start als Admin über Start_Zeitnehmung_Admin.cmd.
    - Logging läuft in gui_startup.log (loguru) – bei --noconsole gibt es
      keine Konsole, das Log ist die einzige Diagnosequelle.
    - Ohne --excel/--json sucht die App automatisch nach IMPORT.json bzw.
      einer Excel-Datei im Programmordner (Lade-Kette, Manual.md).
      Keine Demo-Daten! Ohne Datenquelle erscheint eine Fehlermeldung.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Projekt-Root in den Import-Pfad aufnehmen (Entwicklung; im Bundle
# übernimmt PyInstaller das Auflösen der Pakete).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.logger.app_logger import setup_logging  # noqa: E402


def _is_admin() -> bool:
    """Prüft, ob die App mit Administrator-Rechten läuft (Windows).

    Returns:
        True wenn Admin-Rechte vorhanden, sonst False.
    """
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parst die Kommandozeilen-Argumente (testbar, ohne GUI-Start).

    Args:
        argv: Argumentliste (None → sys.argv[1:]).

    Returns:
        Namespace mit `seconds` (Auto-Close) und `hotkeys` (Flag).
    """
    parser = argparse.ArgumentParser(
        description="Wasserski-Racing Zeitnehmung (Desktop-Anwendung).")
    parser.add_argument(
        "seconds", nargs="?", type=float, default=0.0,
        help="Nach N Sekunden automatisch schließen (Smoke-Test).")
    parser.add_argument(
        "--hotkeys", action="store_true",
        help="Systemweite Hotkeys aktivieren (Windows-Admin nötig).")
    parser.add_argument(
        "--excel", type=str, default=None,
        help="Pfad zur Excel-Datei mit Renndaten (Named Ranges: INFO, RACES, STARTER).")
    parser.add_argument(
        "--json", type=str, default=None,
        help="Pfad zur IMPORT.json (vom VBA-Makro erzeugt).")
    return parser.parse_args(argv)


def _write_fatal(exception: BaseException) -> None:
    """Schreibt einen unbehandelten Fehler in gui_startup.log (letzte Rettung).

    Bei einer gebauten .exe (--noconsole) gibt es keine Konsole und oft
    nicht einmal ein funktionierendes Log-Setup – dieser Handler sichert
    die Fehlermeldung, damit der Absturz diagnostizierbar bleibt.

    Args:
        exception: die unbehandelte Exception.
    """
    try:
        from python.config.app_config import get_runtime_dir
        log_path = get_runtime_dir() / "gui_startup.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"FATAL: {type(exception).__name__}: {exception}\n")
    except OSError:
        pass


def main() -> None:
    """Startet die GUI mit der Standard-Konfiguration (run_app)."""
    try:
        _main()
    except BaseException as exc:          # noqa: BLE001 – Diagnose-Zweck
        _write_fatal(exc)
        raise


def _main() -> None:
    """Interne Startlogik (getrennt für die FATAL-Diagnose)."""
    args = parse_args()
    if args.seconds < 0:
        print(f"Ungültige Sekundenangabe: {args.seconds}")
        sys.exit(1)

    from python.config.app_config import get_runtime_dir, get_settings
    setup_logging(get_runtime_dir() / "gui_startup.log",
                  console=True, level="DEBUG")

    from python.gui.main_window import run_app

    # Hotkeys automatisch aktivieren wenn Admin-Rechte vorhanden
    # (kein --hotkeys Flag nötig wenn die .exe als Admin läuft)
    settings = get_settings()
    is_admin = _is_admin()
    enable_keyboard = args.hotkeys or settings.enable_keyboard or is_admin

    run_app(enable_keyboard=enable_keyboard,
            auto_close_seconds=args.seconds,
            excel_path=args.excel,
            json_path=args.json,
            is_admin=is_admin)


if __name__ == "__main__":
    main()
