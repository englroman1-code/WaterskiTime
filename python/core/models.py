"""Domain models for the Waterski Racing Timing System.

Dieses Modul definiert die fachlichen Datenstrukturen (Domänenmodell) des
Zeitnehmungs-Systems. Das Modell ist bewusst UNABHÄNGIG vom Excel-Format –
die Excel-Datei des Kunden darf sich ändern, diese Klassen bleiben stabil.

Siehe Objektplan: _BOTBRAIN/object_model_plan.md (Abschnitt 4).

Konventionen:
    - Klassen-/Variablennamen: Englisch
    - Docstrings & Kommentare: Deutsch (Kundenwunsch, reichlich dokumentieren)
    - Datenklassen: @dataclass mit Typ-Hints
    - Zeitmessung: datetime (Zeitpunkt), timedelta (Dauer)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EventType(Enum):
    """Ereignistypen gemäß Pflichtenheft §5.1.

    Jedes erfasste Ereignis bekommt genau einen Typ zugeordnet.
    """
    START = "START"                      # Rennstart (Systemereignis, kein Hotkey)
    STARTLINE = "STARTLINE"              # Start einer Startreihe (zeitversetzter Start,
                                         # Variante A – Systemereignis)
    PASSAGE = "PASSAGE"                  # Rundenpassage (Hotkey-Eingabe)
    FINISH = "FINISH"                    # Zieleinlauf – wird MANUELL gesetzt, wenn
                                         # der Bediener eine Klasse beendet (2026-09-03)
    CORRECTION_PLUS = "CORRECTION_PLUS"  # Manuelle Korrektur +1 Runde
    CORRECTION_MINUS = "CORRECTION_MINUS"  # Manuelle Korrektur −1 Runde (optional, Q6)
    INVALID = "INVALID"                  # Verworfen (Sperrzeit verletzt / Fehlbedienung)


class RacePhase(Enum):
    """Rennphasen der Zustandsmaschine (ADR-005).

    Strikte Übergänge: PRESTART → ACTIVE → FINISHING → FINISHED → RESET
    """
    PRESTART = "PRESTART"    # Vorstart: Countdown läuft, noch keine Wertung
    ACTIVE = "ACTIVE"        # Rennen läuft, Eingaben werden verarbeitet
    FINISHING = "FINISHING"  # Renndauer abgelaufen, Klassen werden manuell beendet
    FINISHED = "FINISHED"    # alle Klassen manuell beendet, Ergebnisse stehen
    RESET = "RESET"          # zurückgesetzt, bereit für nächstes Rennen


# ---------------------------------------------------------------------------
# Stammdaten (kommen später aus der Excel-Datei)
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """Veranstaltungsdaten (Excel Named Range 'INFO', Pflichtenheft §3.1).

    Ein Event ist die gesamte Veranstaltung (z. B. ÖM Ybbs 2026),
    unter der mehrere Rennen gefahren werden.
    """
    title: str = ""             # Name der Veranstaltung
    date: str = ""              # Veranstaltungsdatum (Anzeigeformat)
    organizer: str = ""         # Ausrichtender Verein / Verband


@dataclass
class Starter:
    """Stammdaten eines Starters (Excel Named Range 'STARTER', Pflichtenheft §3.2).

    Ein Starter = ein Boot mit Fahrer. Eindeutig identifiziert über den Boot-Key.
    Enthält alle Felder aus der Excel-Startliste.
    """
    boot_key: str = ""          # eindeutige Tastenzuordnung A–Z (RundenTaste, UPPER)
    boat_number: str = ""       # Boot-Nummer (BoatNr, z.B. "173")
    skier: str = ""             # Fahrer-Name (Skier, z.B. "Pfenningbauer, Paul")
    team: str = ""              # Team-Name
    driver: str = ""            # Fahrer (Driver)
    observer: str = ""          # Observer
    club: str = ""              # Verein (Club)
    federation: str = ""        # Verband (Federation)
    klasse: str = ""            # Rennklasse, z.B. "JUN", "MEN", "F1"
    race_number: int = 0        # Rennnummer (welches Rennen)
    startreihe: int = 0         # Startreihe (1, 2, 3, ...)

    @property
    def display_name(self) -> str:
        """Anzeigename für GUI: 'BoatNr /Klasse Team' (wie im Copit-Sheet)."""
        parts = [self.boat_number]
        if self.klasse:
            parts.append(f"/{self.klasse}")
        if self.team:
            parts.append(self.team)
        return "".join(parts)


@dataclass
class StartLine:
    """Startreihe mit Zeitoffset (Pflichtenheft §3.3).

    Verschiedene Startreihen starten mit festem Offset (10 oder 15 Sekunden)
    nach der vorherigen Startreihe. Der Offset ist FIX pro Veranstaltung.
    """
    number: int = 0            # Startreihe-Nummer (1, 2, 3, ...)
    offset_seconds: int = 0    # Zeitoffset in Sekunden gegenüber Rennstart


@dataclass
class RaceConfig:
    """Konfiguration EINES Rennens (Excel Named Range 'RACES', §3.3).

    Die Excel-Datei enthält typischerweise mehrere RaceConfigs –
    der Bediener wählt das Rennen per Dropdown aus (Q5).
    Rundenlängen sind PRO RENNEN (nicht global).

    Begriffsklärung (Kunde, 2026-08-20, bestätigt 2026-09-02):
        - Startintervall: Vorlaufzeit bis zum wirklichen Start (Countdown),
          kommt aus der Excel/IMPORT.json, PFLICHTFELD (pro Rennen unterschiedlich)
        - Grid Time: Zeit zwischen den Startreihen, kommt aus der Excel/IMPORT.json,
          PFLICHTFELD (ersetzt den früheren festen startreihe_offset_s aus der Config)
        - Beide Werte sind in SEKUNDEN angegeben (keine Verwirrung durch Mischeinheiten)
    """
    race_number: int = 0                   # eindeutige Rennnummer
    race_duration_min: int = 0             # Gesamtdauer in Minuten
    start_interval_s: int = 0              # Startintervall = Vorlaufzeit bis zum Start (Sekunden, Pflicht)
    lap1_length_m: int = 0                 # Streckenlänge 1. Runde in Metern
    standard_lap_length_m: int = 0         # Streckenlänge Standardrunde in Metern
    grid_time_s: int = 0                   # Grid Time: Zeit zwischen den Startreihen (Sekunden, Pflicht)


# ---------------------------------------------------------------------------
# Laufzeit-Objekte (entstehen während des Rennens)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RaceEvent:
    """Ein erfasstes Ereignis – Basis aller Zeitnehmung und Protokollierung.

    Unveränderlich (frozen): Ereignisse sind die Rohdaten des Systems und
    dürfen nachträglich nicht verändert werden (Beweisfunktion, §7).
    Auch UNGÜLTIGE Eingaben werden als RaceEvent festgehalten (valid=False) –
    sie sind für die Wertung irrelevant, aber für die Rekonstruktion wichtig.
    """
    timestamp: datetime      # exakter Zeitstempel der Erfassung
    boot_key: str            # Boot-Key A–Z (siehe Starter)
    event_type: EventType    # START / PASSAGE / FINISH / KORREKTUR / INVALID
    valid: bool = True       # False = durch Sperrzeit verworfen
    source: str = "HOTKEY"   # HOTKEY | MANUAL | SYSTEM
    detail: str = ""         # optionaler Zusatz fürs Renn-Log
                             # (z. B. "Race=1;Line=2" bei STARTLINE)


@dataclass
class Lap:
    """Eine gefahrene Runde eines Boots.

    Erste Runde:    start_time = Rennstart, end_time = erste Passage
    Folge-Runden:   start_time = vorige Passage, end_time = aktuelle Passage
    """
    number: int            # Rundennummer (1 = erste Runde)
    start_time: datetime   # Rundenbeginn
    end_time: datetime     # Zielpassage dieser Runde
    duration: timedelta = field(init=False)  # wird in __post_init__ berechnet

    def __post_init__(self) -> None:
        """Konsistenzprüfung: Die Dauer wird aus Start/Ende berechnet."""
        self.duration = self.end_time - self.start_time


@dataclass
class BoatState:
    """Dynamischer Zustand eines Boots während des Rennens.

    Dieses Objekt treibt die Live-Tabelle der GUI:
    Runden, letzte Runde, Gesamtzeit, Sperrzeit-Anzeige, Platzierung.
    """
    starter: Starter                        # Stammdaten (Verweis auf Starter)
    laps: list[Lap] = field(default_factory=list)          # abgeschlossene Runden
    last_passage: datetime | None = None    # Zeitpunkt der letzten Passage
    last_real_passage: datetime | None = None  # letzte echte Zielpassage (nur
                                               # Hotkey; ohne +1-Korrektur) –
                                               # Basis für die Rennende-Ampel
    lockout_until: datetime | None = None   # Sperrzeit-Ende (für GUI-Anzeige)
    finished_at: datetime | None = None     # Zieleinlauf-Zeitpunkt (manuell, 2026-09-03)
    place: int | None = None                # Platzierung (nach Wertung, siehe ResultCalculator)
    start_time: datetime | None = None      # individueller Startzeitpunkt des Boots
                                             # (wenn seine Startreihe startet, Variante A).
                                             # Die erste Runde wird ab diesem Zeitpunkt
                                             # gemessen – nicht ab dem globalen Rennstart.

    # --- berechnete Eigenschaften (bequem für GUI & Export) -----------------
    @property
    def laps_count(self) -> int:
        """Anzahl der vollständig gefahrenen Runden."""
        return len(self.laps)

    @property
    def total_time(self) -> timedelta:
        """Gesamtzeit = Summe aller Rundenzeiten."""
        return sum((lap.duration for lap in self.laps), start=timedelta())

    @property
    def last_lap(self) -> timedelta | None:
        """Dauer der zuletzt abgeschlossenen Runde (oder None)."""
        if not self.laps:
            return None
        return self.laps[-1].duration

    @property
    def best_lap(self) -> timedelta | None:
        """Schnellste Runde (oder None, wenn noch keine Runde fertig)."""
        if not self.laps:
            return None
        return min(lap.duration for lap in self.laps)

    # --- Geschwindigkeit (km/h, Kundenanforderung 2026-09-03) --------------
    def speed_last_lap(self, lap1_length_m: int,
                       standard_lap_length_m: int) -> float | None:
        """Durchschnittsgeschwindigkeit der letzten Runde in km/h.

        Strecke der letzten Runde: die 1. Runde nutzt `lap1_length_m`,
        alle weiteren Runden `standard_lap_length_m` (Achtung: wenn die
        letzte Runde die erste Runde ist!).

        Args:
            lap1_length_m: Streckenlänge der 1. Runde in Metern.
            standard_lap_length_m: Streckenlänge der Standardrunde in Metern.

        Returns:
            km/h (float) oder None, wenn noch keine Runde abgeschlossen ist
            oder die Rundenzeit 0 ist.
        """
        if not self.laps:
            return None
        last = self.laps[-1]
        distance_m = (lap1_length_m if last.number == 1
                      else standard_lap_length_m)
        seconds = last.duration.total_seconds()
        if distance_m <= 0 or seconds <= 0:
            return None
        # km/h = (m / 1000) / (s / 3600) = m / s * 3.6
        return distance_m / seconds * 3.6

    def speed_total(self, lap1_length_m: int,
                    standard_lap_length_m: int) -> float | None:
        """Durchschnittsgeschwindigkeit über die Gesamtstrecke in km/h.

        Gesamtstrecke bisher = 1. Runde + (Runden-1) × Standardrunde.
        Zeit = vom individuellen Start (Startreihe) bis zum letzten
        Passieren der Startlinie (state.last_passage).

        Args:
            lap1_length_m: Streckenlänge der 1. Runde in Metern.
            standard_lap_length_m: Streckenlänge der Standardrunde in Metern.

        Returns:
            km/h (float) oder None, wenn noch keine Runde abgeschlossen ist
            oder die verstrichene Zeit 0 ist.
        """
        if not self.laps or self.last_passage is None:
            return None
        start = self.start_time or (self.laps[0].start_time
                                    if self.laps else None)
        if start is None:
            return None
        elapsed = self.last_passage - start
        seconds = elapsed.total_seconds()
        if seconds <= 0:
            return None
        distance_m = (lap1_length_m
                      + (self.laps_count - 1) * standard_lap_length_m)
        if distance_m <= 0:
            return None
        return distance_m / seconds * 3.6


@dataclass
class BoatResult:
    """Endergebnis eines Boots – Grundlage für Wertung und Excel-Export.

    Platzierung gemäß Pflichtenheft §5.3: primär Rundenzahl,
    sekundär (bei gleicher Rundenzahl) die geringere Gesamtzeit.
    """
    starter: Starter
    laps_count: int = 0            # Anzahl vollständiger Runden
    total_time: timedelta = timedelta()   # Gesamtzeit (Summe der Runden)
    best_lap: timedelta | None = None     # schnellste Runde
    place: int = 0                 # Platzierung (1 = Sieger)


@dataclass
class RaceClass:
    """Laufzeit-Klasse: eine Rennklasse mit ihrem Fortschritts-Zustand.

    Wird aus den Starter-Klassen abgeleitet. Der Zustand steuert das
    GUI-Panel 'Rennende-Status' (WARTEND / FERTIG) und die manuelle
    Beendigung einer Klasse (2026-09-03).

    Hinweis: Klassen sind NUR für die Auswertung relevant,
    nicht für die Zeitmessung. Die Startreihe bestimmt den Startzeitpunkt.
    """
    name: str                     # Klassenname, z. B. "JUN", "MEN"
    finish_state: str = "WAITING"  # WAITING (offen) → CLOSED (manuell beendet)
