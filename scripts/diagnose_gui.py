"""Mini-Isolationstest: Wo stirbt die GUI?

Testet in einem einzigen Prozess nacheinander (mit Auto-Close, damit der
Test automatisiert laufen kann):
  T1: nacktes tkinter  – tk.Tk() + Label + mainloop
  T2: nacktes CustomTkinter – ctk.CTk() + CTkLabel + mainloop
  T3: unser MainWindow (vollständiges Layout)

Jede Stufe loggt ihren Start/Ende-Zustand über die AppLogger-Klasse.
Bricht eine Stufe mit TclError ab, ist sie als Ursache identifiziert.

Verwendung:
    python scripts/diagnose_gui.py           # jede Stufe 2s sichtbar
    python scripts/diagnose_gui.py 5         # jede Stufe 5s sichtbar
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

# Projekt-Root in den Import-Pfad aufnehmen
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.logger.app_logger import log_progress, logger, setup_logging


def run_stage(name: str, seconds: float, build: callable) -> None:
    """Führt eine Teststufe aus und fängt Tcl-Fehler sauber ab.

    Args:
        name: Name der Stufe (T1/T2/T3).
        seconds: Sichtzeit in Sekunden (0 = manuell schließen).
        build: Funktion, die das Fenster baut und zurückgibt.
    """
    log_progress(f"{name}: starte ...", step=0, total=0)
    t0 = time.perf_counter()
    try:
        window = build()
        logger.info(f"{name}: Fenster gebaut in {time.perf_counter() - t0:.2f}s, "
                    f"winfo_id={window.winfo_id()}, "
                    f"state={window.state()}")
        if seconds > 0:
            window.after(int(seconds * 1000), window.destroy)
            logger.info(f"{name}: Auto-Close nach {seconds:.0f}s")
        window.mainloop()
        logger.info(f"{name}: mainloop sauber beendet "
                    f"({time.perf_counter() - t0:.2f}s)")
    except Exception as exc:  # noqa: BLE001 – Diagnose: alles erfassen
        logger.error(f"{name}: FEHLER -> {type(exc).__name__}: {exc}")
        logger.error(f"{name}: Traceback:\n{traceback.format_exc()}")


def main() -> None:
    """Führt die drei Isolationstufen aus."""
    setup_logging("gui_diagnose.log", console=True, level="DEBUG")
    logger.info("=== GUI-Isolationstest gestartet ===")
    seconds: float = 2.0
    if len(sys.argv) > 1:
        try:
            seconds = float(sys.argv[1])
        except ValueError:
            logger.error(f"Ungültige Sekundenangabe: {sys.argv[1]}")
            sys.exit(1)

    # --- T1: nacktes tkinter ------------------------------------------------
    def build_t1():
        import tkinter as tk
        root = tk.Tk()
        root.title("T1 nacktes tkinter")
        tk.Label(root, text="T1: HALLOWELT", font=("Arial", 24)).pack(padx=50, pady=50)
        return root

    run_stage("T1 (tkinter)", seconds, build_t1)

    # --- T2: nacktes CustomTkinter --------------------------------------------
    def build_t2():
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        root = ctk.CTk()
        root.title("T2 nacktes CustomTkinter")
        ctk.CTkLabel(root, text="T2: HALLOWELT", font=("Arial", 24)).pack(padx=50, pady=50)
        return root

    run_stage("T2 (CustomTkinter)", seconds, build_t2)

    # --- T3: unser MainWindow ---------------------------------------------------
    def build_t3():
        from python.gui.main_window import AppController, MainWindow
        window = MainWindow()
        AppController(window)
        return window

    run_stage("T3 (MainWindow)", seconds, build_t3)

    logger.info("=== Isolationstest beendet ===")


if __name__ == "__main__":
    main()
