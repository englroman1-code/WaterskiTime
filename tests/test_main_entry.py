"""Tests für den Produktions-Einstieg python/main.py (PyInstaller-Entry).

Geprüft wird nur das Argument-Parsing (keine GUI-Initialisierung), damit
die Tests ohne Fenster und ohne Blockade durch mainloop laufen.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_main_entry():
    """Lädt python/main.py als Modul (ohne main() aufzurufen)."""
    spec = importlib.util.spec_from_file_location(
        "main_entry", PROJECT_ROOT / "python" / "main.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_args_default() -> None:
    """Ohne Argumente: kein Auto-Close, Hotkeys aus."""
    module = _load_main_entry()
    args = module.parse_args([])
    assert args.seconds == 0.0
    assert args.hotkeys is False


def test_parse_args_seconds_and_hotkeys() -> None:
    """Auto-Close-Sekunden und --hotkeys werden korrekt geparst."""
    module = _load_main_entry()
    args = module.parse_args(["8", "--hotkeys"])
    assert args.seconds == 8.0
    assert args.hotkeys is True


def test_parse_args_negative_seconds_rejected_by_main() -> None:
    """Negative Sekunden werden von parse_args durchgereicht (main() bricht ab)."""
    module = _load_main_entry()
    args = module.parse_args(["-3"])
    assert args.seconds == -3.0
