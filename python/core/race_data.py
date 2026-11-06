"""RaceData – neutraler Container für geladene Renndaten.

Dieses Modul definiert den Datencontainer, der die aus IMPORT.json (oder
Excel via VBA-Makro) geladenen Renndaten bündelt und an GUI & RaceEngine
weitergibt.

Hinweis: Es gibt KEINE Demo-Daten mehr in der App (Entscheidung 2026-08-25).
Die App lädt ausschließlich echte Daten über die Lade-Kette
(race_state.json → IMPORT.json → Excel → Fehler). Testdaten liegen nur in
`tests/` als Fixture.

Konventionen:
    - Klassen-/Variablennamen: Englisch
    - Docstrings & Kommentare: Deutsch (Kundenwunsch)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from python.core.models import Event, RaceConfig, Starter


@dataclass
class RaceData:
    """Gebündelte Renndaten einer Veranstaltung.

    Enthält alle Daten, die GUI und RaceEngine zum Betrieb benötigen.
    Die Laufzeit-Zustände (BoatState) entstehen erst beim Laden in die
    RaceEngine – sie sind hier bewusst NICHT enthalten.

    Attributes:
        event: Veranstaltungsdaten (Event).
        race_configs: Alle Rennkonfigurationen der Veranstaltung.
        starters: Alle Starter der Veranstaltung (über alle Rennen).
        selected_config: Das aktuell ausgewählte Rennen (RaceConfig).
    """
    event: Event
    race_configs: list[RaceConfig]
    starters: list[Starter]
    selected_config: RaceConfig = field(default_factory=RaceConfig)


__all__ = ["RaceData"]
