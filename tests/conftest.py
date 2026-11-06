"""Gemeinsame pytest-Fixtures für die GUI-Tests.

Tk-Stabilität (Windows, Tk 8.6/Python 3.14): Mehrfaches Erzeugen und
Zerstören von Tk-Fenstern im selben Prozess crasht mit
„Can't find a usable tk.tcl" bzw. wirft sporadisch TclError. Deshalb wird
EXAKT EIN Fenster für die gesamte Test-Session erzeugt (scope="session")
und von allen GUI-Testmodulen wiederverwendet.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

customtkinter = pytest.importorskip("customtkinter")


def _remove_race_state(state_file: Path) -> None:
    """Löscht race_state.json mit Retry (Datei-Lock durch after()-Tick).

    Ein weiterlaufender after()-Tick eines Controllers kann race_state.json
    noch offen halten (save() schreibt asynchron). Beim Löschen kann dann ein
    PermissionError auftreten – deshalb mit kurzem Retry versuchen.
    """
    for _ in range(5):
        try:
            if state_file.exists():
                state_file.unlink()
            return
        except PermissionError:
            time.sleep(0.05)


@pytest.fixture(autouse=True)
def _clean_race_state():
    """Löscht race_state.json vor und nach JEDEM Test.

    Die Tests erzeugen race_state.json während des Laufs (Crash-Recovery-
    State im Tick). Ohne das Löschen nach jedem Test überlebt ein
    race_state.json von einem früheren Test und wird vom nächsten Test
    über die Crash-Recovery-Logik geladen – statt der übergebenen
    Testdaten (Demo-Daten). Das verfälscht die Test-Isolation.
    """
    from python.config.app_config import get_runtime_dir
    state_file = get_runtime_dir() / "race_state.json"
    _remove_race_state(state_file)
    yield
    _remove_race_state(state_file)


@pytest.fixture(scope="session")
def tk_window():
    """Das EINE Tk-Fenster für die gesamte Session (Tk-Stabilität).

    Module erzeugen darauf ihre eigenen AppController – zerstört wird das
    Fenster erst am Session-Ende (Fixture-TearDown).
    """
    customtkinter.set_appearance_mode("dark")
    from python.gui.main_window import MainWindow

    window = MainWindow()
    window.update_idletasks()
    yield window
    window.destroy()
