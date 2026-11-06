"""AppLogger – zentrale Text-Protokollierung für das Zeitnehmungs-System.

Basiert auf loguru (AGENTS.md §8: ausschließlich loguru in Produktionscode).
Diese Klasse bietet einen einheitlichen Einstiegspunkt:
    - Konsolen-Ausgabe während der Entwicklung (farbig)
    - Datei-Log (TXT) für Diagnose/Support (rotation, überschreibbar)

Verwendung:
    from python.logger.app_logger import logger, setup_logging
    setup_logging("logs/app.log")
    logger.info("Anwendung gestartet")

WICHTIG: Keine Secrets/Blackbox-Rohdaten hier – die Blackbox (Beweisfunktion)
wird separat in python/logger/blackbox.py umgesetzt (append-only, unverändert).
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

# Einheitliches Log-Format: Zeit (ms) | Level | Meldung
LOG_FORMAT = (
    "[{time:YYYY-MM-DD HH:mm:ss.SSS}] [{level:<8}] "
    "{name}:{function}:{line} – {message}"
)


def setup_logging(log_file: str | Path | None = None,
                  console: bool = True,
                  level: str = "DEBUG") -> None:
    """Konfiguriert die loguru-Logger (einmalig pro App-Start).

    Args:
        log_file: Pfad zur TXT-Logdatei (None → nur Konsole).
        console: True → farbige Konsolenausgabe.
        level: Log-Level (z. B. "DEBUG", "INFO").
    """
    # Alte Handler entfernen, damit setup idempotent ist (Tests, Neustarts)
    logger.remove()

    if console:
        if sys.stderr is None:
            # Gebaute .exe mit --noconsole (PyInstaller): es gibt keine
            # Konsole – der Konsolen-Sink entfällt, das Datei-Log reicht
            # (sonst würde loguru.add(None) die App abstürzen lassen).
            pass
        else:
            logger.add(sys.stderr, format=LOG_FORMAT, level=level,
                       colorize=True, enqueue=False)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        # mode="w": überschreiben pro Sitzung (Diagnose-Log, keine Rotation nötig)
        logger.add(str(path), format=LOG_FORMAT, level=level,
                   encoding="utf-8", mode="w", enqueue=False)


def log_progress(message: str, step: int | None = None, total: int | None = None) -> None:
    """Loggt einen Fortschrittsschritt (Start-Sequenz-Diagnose).

    Args:
        message: Beschreibung des Schritts.
        step: aktuelle Schrittnummer (optional).
        total: Gesamtzahl der Schritte (optional).
    """
    prefix = f"[{step}/{total}] " if step is not None else ""
    logger.info(f"{prefix}{message}")


__all__ = ["logger", "setup_logging", "log_progress"]
