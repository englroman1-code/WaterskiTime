"""Test-Fixture: fiktive, realistische Renndaten für Tests.

WICHTIG: Dieses Modul gehört NUR zu den Tests (tests/). Die App selbst
enthält KEINE Demo-Daten (Entscheidung 2026-08-25) – sie lädt ausschließlich
echte Daten über die Lade-Kette (race_state.json → IMPORT.json → Excel → Fehler).

Warum existiert dieses Modul?
    Für GUI- und Logik-Tests werden realistische Beispiel-Daten benötigt:
        - Veranstaltung: "Österreichische Meisterschaften Ybbs 2026"
        - 3 Rennen (MEN+DAMEN, U18 Open, JUN)
        - Starter A–I mit Klassen
        - Laufzeit-Zustände (BoatState mit Runden) für Rennen 2 (U18 Open)
        - Ereignisliste inkl. eines INVALID-Events (Sperrzeit-Demo)

Alle Zeitstempel basieren auf einem FESTEN Rennstart (17.06.2026 14:30:00),
damit die Tests reproduzierbar und stabil sind (keine Zufallswerte).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from python.core.models import (
    BoatState,
    Event,
    EventType,
    Lap,
    RaceConfig,
    RaceEvent,
    Starter,
)
from python.core.race_data import RaceData
from python.config.app_config import get_settings

# ---------------------------------------------------------------------------
# Fester Demo-Zeitpunkt (reproduzierbar, keine echte "Jetzt"-Zeit)
# ---------------------------------------------------------------------------

DEMO_RACE_START = datetime(2026, 6, 17, 14, 30, 0)  # Rennstart Rennen 2 (U18 Open)


# ---------------------------------------------------------------------------
# Stammdaten
# ---------------------------------------------------------------------------

def build_event() -> Event:
    """Veranstaltungsdaten (entspricht Excel Named Range 'INFO')."""
    return Event(
        title="Österreichische Meisterschaften Ybbs 2026",
        date="17.06.2026",
        organizer="WSV Ybbs",
    )


def build_starters() -> list[Starter]:
    """Fiktive Starterliste (Fahrer + Boot-Keys A–I, mehrere Klassen)."""
    return [
        Starter(boot_key="A", boat_number="101", skier="S. Huber", klasse="U18", race_number=2, startreihe=1),
        Starter(boot_key="B", boat_number="102", skier="M. Berger", klasse="U18", race_number=2, startreihe=1),
        Starter(boot_key="C", boat_number="103", skier="A. Sterner", klasse="DAMEN", race_number=1, startreihe=2),
        Starter(boot_key="D", boat_number="104", skier="G. Hocker", klasse="U18", race_number=2, startreihe=1),
        Starter(boot_key="E", boat_number="105", skier="M. Herger", klasse="MEN", race_number=1, startreihe=1),
        Starter(boot_key="F", boat_number="106", skier="L. Wagner", klasse="DAMEN", race_number=1, startreihe=2),
        Starter(boot_key="G", boat_number="107", skier="T. Leitner", klasse="MEN", race_number=1, startreihe=1),
        Starter(boot_key="H", boat_number="108", skier="J. Pichler", klasse="JUN", race_number=3, startreihe=1),
        Starter(boot_key="I", boat_number="109", skier="K. Eder", klasse="JUN", race_number=3, startreihe=1),
    ]


def build_race_configs() -> list[RaceConfig]:
    """Drei Rennen der Veranstaltung (entspricht Excel Named Range 'RACES')."""
    return [
        RaceConfig(
            race_number=1,
            race_duration_min=45,
            lap1_length_m=1800,          # erste Runde ist länger
            standard_lap_length_m=1600,  # alle weiteren Runden
            grid_time_s=30,              # Grid Time: Zeit zwischen Startreihen
            start_interval_s=15,         # Startintervall = Vorlaufzeit bis zum Start
        ),
        RaceConfig(
            race_number=2,
            race_duration_min=30,
            lap1_length_m=1600,
            standard_lap_length_m=1600,
            grid_time_s=30,
            start_interval_s=20,
        ),
        RaceConfig(
            race_number=3,
            race_duration_min=40,
            lap1_length_m=2000,
            standard_lap_length_m=1800,
            grid_time_s=30,
            start_interval_s=15,
        ),
    ]


# ---------------------------------------------------------------------------
# Laufzeit-Zustände (simulierte Runden für Rennen 2 – U18 Open)
# ---------------------------------------------------------------------------

def _simulate_laps(boot_key: str, laps_count: int, start: datetime,
                   base_seconds: float, variance: float) -> list[Lap]:
    """Erzeugt eine realistische Rundenfolge mit leicht variierenden Zeiten.

    Rundenzeiten bei 1600 m liegen typischerweise zwischen ~2:05 und 2:30.
    Die Werte sind deterministisch (Formel, kein Zufall), damit Tests stabil sind.

    Args:
        boot_key: Boot-Key (nur für Log-/Doc-Zwecke).
        laps_count: Anzahl zu erzeugender Runden.
        start: Zeitpunkt des Rennstarts (Beginn Runde 1).
        base_seconds: mittlere Rundenzeit in Sekunden.
        variance: maximale Abweichung je Runde in Sekunden.

    Returns:
        Liste der simulierten Runden.
    """
    laps: list[Lap] = []
    lap_start = start
    for number in range(1, laps_count + 1):
        # Abwechselnde Abweichung (deterministisch: +/− variance je Nummer)
        sign = 1.0 if number % 2 == 0 else -1.0
        duration_s = base_seconds + sign * variance * (0.5 + (number % 3) * 0.25)
        lap_end = lap_start + timedelta(seconds=duration_s)
        laps.append(Lap(number=number, start_time=lap_start, end_time=lap_end))
        lap_start = lap_end  # nächste Runde beginnt an der Zielpassage der vorigen
    return laps


def build_boat_states_for_race2() -> dict[str, BoatState]:
    """Laufzeit-Zustände der U18-Boote für Rennen 2 (Live-Tabelle Demo).

    Boot A führt mit 8 Runden (wie im GUI-Design), B folgt mit 7, D mit 6.
    """
    starters = {s.boot_key: s for s in build_starters()}

    # Führender: S. Huber – 8 Runden, schnellste Runde 02:11,4
    a_laps = _simulate_laps("A", 8, DEMO_RACE_START, base_seconds=134.0, variance=3.0)
    boat_a = BoatState(starter=starters["A"], laps=a_laps)
    # Demo der roten "SPERRZEIT"-Zelle: Sperrzeit läuft noch (bewusst übertrieben)
    boat_a.lockout_until = a_laps[-1].end_time + timedelta(seconds=35)

    # Zweiter: M. Berger – 7 Runden
    b_laps = _simulate_laps("B", 7, DEMO_RACE_START, base_seconds=136.5, variance=2.5)
    boat_b = BoatState(starter=starters["B"], laps=b_laps)

    # Dritter: G. Hocker – 6 Runden
    d_laps = _simulate_laps("D", 6, DEMO_RACE_START, base_seconds=138.0, variance=2.0)
    boat_d = BoatState(starter=starters["D"], laps=d_laps)

    # Die übrigen Starter sind im Rennen 2 (U18) nicht am Start:
    # sie bekommen einen leeren Laufzeit-Zustand (0 Runden) für die Anzeige.
    boats = {key: BoatState(starter=starter) for key, starter in starters.items()}
    boats["A"], boats["B"], boats["D"] = boat_a, boat_b, boat_d
    return boats


def build_boat_states(config: RaceConfig, starters: list[Starter]) -> dict[str, BoatState]:
    """Laufzeit-Zustände für ein beliebiges Rennen.

    Für Rennen 2 (U18 Open) werden die simulierten Runden geladen (Demo),
    für alle anderen Rennen erhalten alle Starter einen leeren Zustand
    (0 Runden – die Live-Tabelle zeigt dann nur die Startliste).

    Args:
        config: Das aktive Rennen (bestimmt, ob simulierte Runden geladen werden).
        starters: Starterliste der Veranstaltung.

    Returns:
        Dict boot_key → BoatState.
    """
    boats = {s.boot_key: BoatState(starter=s) for s in starters}
    if config.race_number == 2:
        boats.update(build_boat_states_for_race2())
    return boats


def build_demo_events(boats: dict[str, BoatState]) -> list[RaceEvent]:
    """Ereignisliste passend zu den simulierten Runden (chronologisch).

    Enthält ein bewusst ungültiges Ereignis (Sperrzeit-Demo, Q1/Pflichtenheft §5.2):
    Eingaben innerhalb der Sperrzeit werden verworfen, aber trotzdem protokolliert.
    """
    events: list[RaceEvent] = [
        RaceEvent(timestamp=DEMO_RACE_START, boot_key="SYSTEM",
                  event_type=EventType.START, valid=True, source="SYSTEM"),
    ]

    for boat_key in ("A", "B", "D"):
        for lap in boats[boat_key].laps:
            events.append(
                RaceEvent(timestamp=lap.end_time, boot_key=boat_key,
                          event_type=EventType.PASSAGE, valid=True, source="HOTKEY")
            )

    # Ungültige Doppel-Eingabe direkt nach der letzten Passage von Boot A
    # (innerhalb der Sperrzeit → INVALID, aber vollständig protokolliert)
    last_a = boats["A"].laps[-1].end_time
    events.append(
        RaceEvent(timestamp=last_a + timedelta(seconds=1), boot_key="A",
                  event_type=EventType.PASSAGE, valid=False, source="HOTKEY")
    )

    # Chronologisch sortieren (Ereignisse werden immer in Zeitreihenfolge gehalten)
    events.sort(key=lambda e: e.timestamp)
    return events


# ---------------------------------------------------------------------------
# Gesamt-Szenario (Test-Fixture)
# ---------------------------------------------------------------------------

def create_demo_scenario() -> RaceData:
    """Baut das vollständige Test-Szenario (reproduzierbar, ohne Zufall).

    Returns:
        RaceData mit allen befüllten Objekten (event, race_configs, starters).
    """
    event = build_event()
    configs = build_race_configs()
    starters = build_starters()

    # Aktives Rennen für die Tests: Rennen 2 (U18 Open) – wie im GUI-Design
    selected_config = configs[1]

    return RaceData(
        event=event,
        race_configs=configs,
        starters=starters,
        selected_config=selected_config,
    )


def demo_lockout_seconds() -> float:
    """Sperrzeit aus der App-Konfiguration (JSON) – Live-Demo des App-Parameters (Q1).

    Returns:
        Konfigurierte Sperrzeit in Sekunden (Default 2.0).
    """
    return get_settings().lockout_seconds