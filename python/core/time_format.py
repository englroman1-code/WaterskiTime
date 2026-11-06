"""Zentrale Zeitformatierung für Anzeige und Export.

Enthält die formatierte Darstellung von Runden-/Gesamtzeiten. Dieses Modul
ist der EINZIGE Ort für die Zeit-Formatierung – GUI (panels.py) und
JSON-Export (json_result_writer.py) nutzen dieselbe Funktion, damit
Anzeige und Ergebnisliste immer konsistent sind.

Konventionen:
    - Funktionsnamen: Englisch
    - Docstrings & Kommentare: Deutsch
"""

from __future__ import annotations

from datetime import timedelta

# Platzhalter für eine nicht vorhandene Zeit (z. B. noch keine Runde)
NO_TIME_PLACEHOLDER = "–"


def format_duration(duration: timedelta | None) -> str:
    """Formatiert eine Rundenzeit als MM:SS.t (z. B. 02:14.2).

    Die Auflösung ist eine Zehntelsekunde – die Anzeige-Auflösung der
    Live-Tabelle (die Rohdaten in der Blackbox bleiben millisekundengenau).

    Args:
        duration: Rundenzeit (None → Platzhalter "–").

    Returns:
        Zeitstring im Format MM:SS.t oder den Platzhalter.
    """
    if duration is None:
        return NO_TIME_PLACEHOLDER
    total_tenths = int(duration.total_seconds() * 10)
    minutes, remainder = divmod(total_tenths, 600)   # 10tel-Sekunden → Minuten
    seconds, tenth = divmod(remainder, 10)
    return f"{minutes:02}:{seconds:02}.{tenth}"


__all__ = ["format_duration", "NO_TIME_PLACEHOLDER"]
