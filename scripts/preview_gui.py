"""Startet die GUI mit echten Renndaten zur Vorschau.

Verwendung:
    python scripts/preview_gui.py                 # Fenster offen lassen
    python scripts/preview_gui.py 8               # nach 8 Sekunden automatisch
                                                  # schließen (Screenshots/CI)
    python scripts/preview_gui.py --hotkeys       # systemweite Hotkeys aktivieren
                                                  # (benötigt Windows-Admin!)
    python scripts/preview_gui.py --excel race.xlsx  # Excel laden (Named Ranges)
    python scripts/preview_gui.py --json IMPORT.json # JSON (vom VBA-Makro) laden

Hinweis: Ohne --excel/--json sucht die App automatisch nach IMPORT.json bzw.
einer Excel-Datei im Programmordner (Lade-Kette, Manual.md). Es gibt KEINE
Demo-Daten – ohne Datenquelle erscheint eine Fehlermeldung.

Systemweite Hotkeys (--hotkeys): Die keyboard-Library benötigt Windows-
Administrator-Rechte (AGENTS.md §10). Ohne Admin-Rechte registriert sie
keine globalen Hooks. Der bequeme Start als Admin: `Start_Zeitnehmung_Admin.cmd`.

Logging: Die Start-Sequenz wird über python/logger/app_logger.py protokolliert
(Diagnose-Log "gui_startup.log" im Projekt-Root + Konsole). So lässt sich
feststellen, wie weit die GUI-Initialisierung kommt.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Projekt-Root in den Import-Pfad aufnehmen, damit die Skripte auch direkt
# aufgerufen werden können (nicht nur via `python -m ...`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.config.app_config import get_settings
from python.logger.app_logger import log_progress, logger, setup_logging


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parst die Kommandozeilen-Argumente (testbar, ohne GUI-Start).

    Args:
        argv: Argumentliste (None → sys.argv[1:]).

    Returns:
        Namespace mit `seconds` (Auto-Close) und `hotkeys` (Flag).
    """
    parser = argparse.ArgumentParser(
        description="Vorschau-Start der Wasserski-Zeitnehmung (echte Renndaten).")
    parser.add_argument(
        "seconds", nargs="?", type=float, default=0.0,
        help="Nach N Sekunden automatisch schließen (Screenshots/CI).")
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


def main() -> None:
    """Öffnet das Hauptfenster (optional mit Auto-Close), mit Schritt-Logging."""
    args = parse_args()
    seconds: float = args.seconds
    if seconds < 0:
        logger.error(f"Ungültige Sekundenangabe: {seconds}")
        sys.exit(1)

    # --- Logging initialisieren (Diagnose) -----------------------------------
    setup_logging("gui_startup.log", console=True, level="DEBUG")
    logger.info("=== Vorschau gestartet (Grundgerüst) ===")
    t0 = time.perf_counter()

    # --- Schritt 1: CustomTkinter importieren ---------------------------------
    log_progress("Importiere customtkinter ...", step=1, total=5)
    import customtkinter as ctk
    logger.info(f"customtkinter {getattr(ctk, '__version__', '?')} importiert")
    ctk.set_appearance_mode("dark")

    # --- Schritt 2: GUI-Module importieren --------------------------------------
    log_progress("Importiere GUI-Module (main_window, panels) ...", step=2, total=5)
    from python.config.app_config import AppConfig as Cfg
    from python.gui.main_window import AppController, MainWindow

    # --- Schritt 3: MainWindow erstellen -----------------------------------------
    log_progress("Erstelle MainWindow (4-Bereichs-Layout) ...", step=3, total=5)
    window = MainWindow()
    logger.info(f"MainWindow erstellt in {time.perf_counter() - t0:.2f}s")

    # --- Schritt 4: AppController (lädt Renndaten) -----------------------------------
    log_progress("Erstelle AppController (lädt Renndaten) ...", step=4, total=5)
    # Systemweite Hotkeys: Flag gewinnt, sonst Wert aus app_settings.json,
    # oder automatisch wenn Admin-Rechte vorhanden (Entscheidung 2026-09-02).
    # Blackbox ist immer aktiv (Beweis-Log) – Hotkeys brauchen sie zwingend.
    def _is_admin() -> bool:
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    settings = get_settings()
    is_admin = _is_admin()
    enable_keyboard = args.hotkeys or settings.enable_keyboard or is_admin
    if enable_keyboard:
        logger.warning("Systemweite Hotkeys AKTIVIERT – Administrator-Rechte "
                       "erforderlich (Start_Zeitnehmung_Admin.cmd)")
    else:
        logger.info("Systemweite Hotkeys deaktiviert (GUI-Tastatur aktiv; "
                    "Admin-Start für Hotkeys: Start_Zeitnehmung_Admin.cmd)")
    try:
        AppController(window, blackbox_path="blackbox.log",
                      enable_keyboard=enable_keyboard,
                      excel_path=args.excel,
                      json_path=args.json,
                      is_admin=is_admin)
    except (FileNotFoundError, Exception) as exc:
        logger.error(f"Start fehlgeschlagen: {exc}")
        import tkinter.messagebox as messagebox
        messagebox.showerror("Start fehlgeschlagen", str(exc))
        window.destroy()
        return
    logger.info(f"AppController erstellt in {time.perf_counter() - t0:.2f}s")

    # --- Schritt 5: mainloop ------------------------------------------------------
    log_progress("Starte mainloop ...", step=5, total=5)
    if seconds > 0:
        # Auto-Close-Modus (Screenshots/CI): Fenster nach oben holen und
        # an eine feste Position setzen, damit der Screenshot deterministisch ist
        window.geometry(f"{Cfg.WINDOW_WIDTH}x{Cfg.WINDOW_HEIGHT}+50+50")
        window.lift()
        window.attributes("-topmost", True)
        window.after(int(seconds * 1000), window.destroy)
        logger.info(f"Auto-Close nach {seconds:.0f}s aktiviert")

    window.mainloop()
    logger.info(f"mainloop beendet nach {time.perf_counter() - t0:.2f}s "
                f"(Fenster geschlossen)")


if __name__ == "__main__":
    main()
