"""Tests für die Aktivierung der systemweiten Hotkeys (Konfiguration + Verdrahtung).

Abgedeckt:
    - AppSettings/ConfigManager: `enable_keyboard` wird geladen/gespeichert
    - AppController-Verdrahtung: enable_keyboard=True → InputHandler + Queue
      werden gestartet; False → keine Hotkeys (GUI-Tastatur reicht)
    - Absicherung: Hotkeys ohne Blackbox → ValueError (Beweis-Log fehlt)
    - preview_gui.py: `--hotkeys`-Flag + Auto-Close-Sekunden (CLI-Parsing)

Hinweis: Die echte keyboard-Library wird NICHT benutzt – für die
Verdrahtungs-Tests wird das Modul `keyboard` durch ein Fake ersetzt
(monkeypatch sys.modules), da `keyboard.on_press` ohne Admin-Rechte keine
globalen Hooks registrieren kann (AGENTS.md §10).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

customtkinter = pytest.importorskip("customtkinter")

from python.config.app_config import AppConfig, AppSettings, ConfigManager
from python.gui.main_window import AppController, MainWindow
from python.logger.blackbox import BlackboxWriter
from tests.demo_data import create_demo_scenario

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Config (AppSettings / ConfigManager)
# ---------------------------------------------------------------------------

def test_enable_keyboard_default_off() -> None:
    """Standard: systemweite Hotkeys sind AUS (bewusst, Admin-Pflicht)."""
    assert AppSettings().enable_keyboard is False


def test_config_manager_roundtrip_enable_keyboard(tmp_path) -> None:
    """enable_keyboard wird in der JSON-Konfiguration gespeichert und geladen."""
    path = tmp_path / "settings.json"
    manager = ConfigManager(path)
    manager.save(AppSettings(lockout_seconds=2.5, enable_keyboard=True))

    loaded = manager.load()
    assert loaded.enable_keyboard is True
    assert loaded.lockout_seconds == 2.5          # bestehende Felder bleiben
    assert AppConfig.DEFAULT_LOCKOUT_SECONDS == 2.0  # Default unverändert


# ---------------------------------------------------------------------------
# AppController-Verdrahtung (Fake-keyboard, kein echter Hook)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def window(tk_window):
    """Session-Fenster aus conftest.py (kein eigenes Tk-Fenster erzeugen)."""
    yield tk_window
    tk_window.update_idletasks()


@pytest.fixture
def fake_keyboard(monkeypatch):
    """Ersetzt die keyboard-Library durch einen Fake (kein Admin nötig)."""
    fake = types.ModuleType("keyboard")
    fake.on_press = lambda callback: object()     # registriert einen Fake-Hook
    fake.unhook = lambda hook: None
    monkeypatch.setitem(sys.modules, "keyboard", fake)
    return fake


def test_controller_without_keyboard_no_handler(window) -> None:
    """enable_keyboard=False → kein InputHandler, keine Queue (Standard)."""
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, enable_keyboard=False)
    assert controller._input_handler is None
    assert controller._input_queue is None
    assert controller.blackbox is None


def test_controller_with_keyboard_starts_handler(window, fake_keyboard,
                                                 tmp_path) -> None:
    """enable_keyboard=True → InputHandler gestartet, Queue vorhanden.

    Der Fake-keyboard-Hook wird registriert (start() erfolgreich).
    """
    blackbox_path = tmp_path / "blackbox.log"
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario,
                               blackbox_path=str(blackbox_path),
                               enable_keyboard=True)

    assert controller._input_handler is not None
    assert controller._input_queue is not None
    assert controller._input_handler._hook is not None   # Hook registriert
    assert controller.blackbox is not None

    controller._input_handler.stop()                     # Fake-unhook
    controller.blackbox.close()
    controller.blackbox = None


def test_controller_keyboard_requires_blackbox(window) -> None:
    """Hotkeys ohne Blackbox → ValueError (Beweis-Log ist zwingend)."""
    scenario = create_demo_scenario()
    with pytest.raises(ValueError):
        AppController(window, data=scenario, enable_keyboard=True)


# ---------------------------------------------------------------------------
# CLI-Flag in preview_gui.py
# ---------------------------------------------------------------------------

def _load_preview_gui():
    """Lädt scripts/preview_gui.py als Modul (ohne main() aufzurufen)."""
    spec = importlib.util.spec_from_file_location(
        "preview_gui", PROJECT_ROOT / "scripts" / "preview_gui.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_preview_gui_parse_args_default() -> None:
    """Ohne Argumente: kein Auto-Close, Hotkeys aus."""
    module = _load_preview_gui()
    args = module.parse_args([])
    assert args.seconds == 0.0
    assert args.hotkeys is False


def test_preview_gui_parse_args_hotkeys_and_seconds() -> None:
    """--hotkeys aktiviert das Flag, Sekunden werden als Float geparst."""
    module = _load_preview_gui()
    args = module.parse_args(["8", "--hotkeys"])
    assert args.seconds == 8.0
    assert args.hotkeys is True


def test_blackbox_writer_usable_with_settings(tmp_path) -> None:
    """Blackbox ist mit den Settings kombinierbar (bewahrt Beweisfunktion)."""
    path = tmp_path / "blackbox.log"
    box = BlackboxWriter(path)
    box.close()
    assert path.exists()
