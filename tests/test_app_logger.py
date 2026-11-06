"""Tests für den zentralen App-Logger (python/logger/app_logger.py).

Abgedeckt:
    - setup_logging ohne Konsolen-Sink bei sys.stderr=None
      (PyInstaller --noconsole: loguru.add(None) würde crashen → Regressions-
      test für den .exe-Build-Fix 2026-08-15)
    - Log-Datei wird angelegt und Meldungen landen darin
"""

from __future__ import annotations

import sys

from loguru import logger

from python.logger.app_logger import setup_logging


def test_setup_logging_without_console_does_not_crash(tmp_path,
                                                      monkeypatch) -> None:
    """sys.stderr=None (--noconsole) → setup_logging darf nicht abstürzen.

    Vor dem Fix versuchte setup_logging mit console=True einen
    Konsolen-Sink auf sys.stderr (= None bei --noconsole) zu legen,
    was die gebaute .exe mit "Unhandled exception in script" beendete.
    """
    monkeypatch.setattr(sys, "stderr", None)

    log_file = tmp_path / "app.log"
    setup_logging(str(log_file), console=True, level="INFO")

    logger.info("Testmeldung ohne Konsole")
    logger.remove()                       # Aufräumen (globale Handler)

    assert log_file.exists()
    assert "Testmeldung ohne Konsole" in log_file.read_text(encoding="utf-8")


def test_setup_logging_with_console_and_file(tmp_path) -> None:
    """Normale Entwicklung: Konsole + Datei, Meldung landet im Log."""
    log_file = tmp_path / "app.log"
    setup_logging(str(log_file), console=True, level="INFO")

    logger.info("Meldung mit Konsole")
    logger.remove()

    assert "Meldung mit Konsole" in log_file.read_text(encoding="utf-8")
