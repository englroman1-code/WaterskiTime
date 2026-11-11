"""JsonResultWriter – Schreibt Endergebnisse und Renn-Log als JSON.

Der Writer erzeugt eine JSON-Datei, die vom VBA-Makro
``MainJsonImport`` in die Excel zurückgeschrieben werden kann.
Das Schema folgt der IMPORT.json-Konvention (_IMP_ Ranges):

    {
        "event": { ... },
        "race_number": 1,
        "generated_at": "...",
        "results": [ { "place": 1, "boat_nr": "173", ... } ],
        "log": [ "[2026-08-25 14:30:00.123] START: Race=1 STATUS: VALID", ... ]
    }

Konventionen:
    - Klassen-/Methodennamen: Englisch
    - Docstrings & Kommentare: Deutsch
    - Typ-Hints für alle öffentlichen Funktionen
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from python.core.models import BoatResult, Event, RaceConfig, RaceEvent
from python.core.time_format import format_duration


class JsonWriteError(Exception):
    """Fehler beim Schreiben der Ergebnis-JSON."""
    pass


# ---------------------------------------------------------------------------
# Übergabe-Objekt
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RaceResultExport:
    """Alle Daten für den Ergebnis-Export EINES Rennens.

    Attributes:
        event: Veranstaltungsdaten.
        config: Konfiguration des Rennens.
        results: Endergebnisse, bereits sortiert.
        log_entries: Renn-Log (RaceEvent-Objekte).
        generated_at: Erzeugungszeitpunkt.
    """
    event: Event
    config: RaceConfig
    results: list[BoatResult]
    log_entries: list[RaceEvent] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

class JsonResultWriter:
    """Schreibt Endergebnisse + Renn-Log als JSON-Datei."""

    def write(self, path: str | Path, export: RaceResultExport) -> Path:
        """Schreibt den Export als JSON-Datei.

        Args:
            path: Zielpfad (z.B. "RESULT_20260904_153022.json").
            export: Export-Daten.

        Returns:
            Pfad der geschriebenen Datei.

        Raises:
            JsonWriteError: Bei Schreibfehlern.
        """
        target = Path(path)
        self._ensure_writable(target)

        data = {
            "event": self._serialize_event(export.event),
            "race_number": export.config.race_number,
            "race_duration_min": export.config.race_duration_min,
            "generated_at": export.generated_at.isoformat(),
            "results": self._serialize_results(export.results, export.config),
            "log": [
                self._serialize_log_entry(e) for e in export.log_entries
            ],
        }

        try:
            target.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise JsonWriteError(
                f"JSON konnte nicht geschrieben werden: {exc}"
            ) from exc

        logger.info("Ergebnis-JSON geschrieben: {}", target)
        return target

    def write_all_races(self, path: str | Path,
                        exports: list[RaceResultExport],
                        event: Event | None = None) -> Path:
        """Schreibt ALLE fertigen Rennen als EINE JSON-Datei.

        Option 1 (2026-09-03): Der Export enthält alle bereits beendeten
        Rennen, gruppiert nach Rennen und Klasse:

            {
                "event": {...},
                "generated_at": "...",
                "races": [
                    {
                        "race_number": 1,
                        "race_duration_min": ...,
                        "classes": [
                            {
                                "klasse": "Herren",
                                "results": [ { "place": 1, ... }, ... ]
                            },
                            ...
                        ],
                        "log": [ ... ]
                    },
                    ...
                ]
            }

        Ist `exports` leer (noch kein Rennen beendet), wird eine Datei mit
        nur den Stammdaten (Event) und leerer `races`-Liste erzeugt.

        Args:
            path: Zielpfad.
            exports: Export-Daten je fertigem Rennen (eines pro Rennen).
            event: Veranstaltungsdaten – wird verwendet, wenn `exports` leer
                ist (nur Stammdaten-Export). Sonst aus dem ersten Export.

        Returns:
            Pfad der geschriebenen Datei.

        Raises:
            JsonWriteError: Bei Schreibfehlern.
        """
        target = Path(path)
        self._ensure_writable(target)

        # Nach Rennnummer sortieren (stabile, aufsteigende Reihenfolge)
        sorted_exports = sorted(exports, key=lambda e: e.config.race_number)

        races = []
        for export in sorted_exports:
            # Ergebnisse nach Klasse gruppieren (Reihenfolge der Klassen
            # wie sie im Rennen vorkommen)
            by_class: dict[str, list[BoatResult]] = {}
            for result in export.results:
                by_class.setdefault(result.starter.klasse, []).append(result)
            classes = [
                {
                    "klasse": klasse,
                    "results": self._serialize_results(results, export.config),
                }
                for klasse, results in by_class.items()
            ]
            races.append({
                "race_number": export.config.race_number,
                "race_duration_min": export.config.race_duration_min,
                "classes": classes,
                "log": [
                    self._serialize_log_entry(e) for e in export.log_entries
                ],
            })

        # Event: aus dem ersten Export, sonst aus dem expliziten Parameter
        export_event = exports[0].event if exports else event
        data = {
            "event": self._serialize_event(export_event) if export_event else {},
            "generated_at": datetime.now().isoformat(),
            "races": races,
        }

        try:
            target.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise JsonWriteError(
                f"JSON konnte nicht geschrieben werden: {exc}"
            ) from exc

        logger.info("Ergebnis-JSON (alle Rennen) geschrieben: {}", target)
        return target

    def _ensure_writable(self, path: Path) -> None:
        """Prüft ob die Zieldatei beschreibbar ist."""
        if path.exists():
            try:
                # Versuchen zum Schreiben zu öffnen
                with open(path, "a", encoding="utf-8"):
                    pass
            except PermissionError:
                raise JsonWriteError(
                    f"Zieldatei gesperrt: {path}\n"
                    f"Bitte Excel schließen und erneut versuchen."
                )

    def _serialize_event(self, event: Event) -> dict:
        """Serialisiert ein Event-Objekt."""
        return {
            "title": event.title,
            "date": event.date,
            "organizer": event.organizer,
        }

    def _serialize_results(self, results: list[BoatResult],
                           config: RaceConfig) -> list[dict]:
        """Serialisiert alle Ergebnisse eines Rennens bzw. einer Klasse.

        Die Rennzeit (``race_time``) wird relativ zur besten Strecke der
        Gruppe berechnet. Gruppe = Klasse innerhalb des Rennens (die
        Ergebnisse werden bereits nach Klasse gruppiert übergeben). Die
        beste Strecke ist die weiteste gefahrene Distanz der Gruppe –
        in der Wertung entspricht das dem Sieger, weil primär nach
        Rundenzahl sortiert wird.

        Args:
            results: Ergebnisse einer Klasse (oder des ganzen Rennens).
            config: Rennkonfiguration (Rundenlängen für die Distanz).

        Returns:
            Liste serialisierter Ergebnis-Dicts.
        """
        best_by_class: dict[str, float] = {}
        for result in results:
            klasse = result.starter.klasse
            distance = self._distance_km(result, config)
            best_by_class[klasse] = max(best_by_class.get(klasse, 0.0), distance)
        return [
            self._serialize_result(
                r, config, best_by_class[r.starter.klasse])
            for r in results
        ]

    def _distance_km(self, result: BoatResult, config: RaceConfig) -> float:
        """Gesamtdistanz eines Boots in Kilometern.

        Formel (wie Excel-Spalte „Calc Strecke“):
        ``Länge 1. Runde + (Runden - 1) × Länge Standardrunde``.

        Args:
            result: Ergebnis mit Rundenzahl.
            config: Rennkonfiguration (Rundenlängen in Metern).

        Returns:
            Distanz in Kilometern (0.0 ohne gefahrene Runde).
        """
        if result.laps_count <= 0:
            return 0.0
        distance_m = (config.lap1_length_m
                      + (result.laps_count - 1) * config.standard_lap_length_m)
        return distance_m / 1000.0

    def _avg_speed_kmh(self, result: BoatResult, distance_km: float) -> float | None:
        """Durchschnittsgeschwindigkeit über die Gesamtdistanz in km/h.

        Args:
            result: Ergebnis mit Gesamtzeit.
            distance_km: gefahrene Distanz in Kilometern.

        Returns:
            km/h (auf 1 Nachkommastelle gerundet) oder None, wenn Distanz
            oder Zeit 0 sind.
        """
        seconds = result.total_time.total_seconds()
        if distance_km <= 0 or seconds <= 0:
            return None
        return round(distance_km / (seconds / 3600.0), 1)

    def _race_time(self, result: BoatResult, distance_km: float,
                   best_distance_km: float) -> timedelta | None:
        """Rennzeit bei gleicher Distanz wie die beste Strecke der Gruppe.

        Formel (wie Excel-Spalte „Rennzeit“):
        ``eigene Gesamtzeit ÷ eigene Distanz × beste Distanz``.

        Args:
            result: Ergebnis mit Gesamtzeit.
            distance_km: eigene Distanz in Kilometern.
            best_distance_km: weiteste Distanz der Klasse im Rennen.

        Returns:
            Hochgerechnete Rennzeit oder None, wenn keine Distanz vorliegt.
        """
        if distance_km <= 0 or best_distance_km <= 0:
            return None
        if result.total_time <= timedelta():
            return None
        return result.total_time * (best_distance_km / distance_km)

    def _serialize_result(self, result: BoatResult, config: RaceConfig,
                          best_distance_km: float = 0.0) -> dict:
        """Serialisiert ein BoatResult-Objekt.

        Neue Felder (Kundenwunsch 2026-11-09):
            - ``distance``: Strecke in km (1. Runde + weitere Runden)
            - ``avg_speed``: Durchschnittsgeschwindigkeit in km/h
            - ``race_time``: Zeit auf die beste Strecke der Klasse umgerechnet
            - ``penalties``: Platzhalter (Strafprozente, aktuell leer)
            - ``points``: Platzhalter (Punkte, aktuell leer)
        """
        distance_km = self._distance_km(result, config)
        race_time = self._race_time(result, distance_km, best_distance_km)
        return {
            "place": result.place,
            "boat_nr": result.starter.boat_number,
            "klasse": result.starter.klasse,
            "skier": result.starter.skier,
            "team": result.starter.team,
            "club": result.starter.club,
            "race_number": result.starter.race_number,
            "laps": result.laps_count,
            "total_time": format_duration(result.total_time),
            "best_lap": format_duration(result.best_lap),
            "distance": round(distance_km, 3),
            "avg_speed": self._avg_speed_kmh(result, distance_km),
            "race_time": format_duration(race_time),
            # Platzhalter: Strafen und Punkte werden weiterhin außerhalb der
            # App gepflegt (Kundenwunsch 2026-11-09: aktuell leere Spalten).
            "penalties": None,
            "points": None,
        }

    def _serialize_log_entry(self, event: RaceEvent) -> str:
        """Serialisiert ein RaceEvent als Log-Zeile.

        Format: [YYYY-MM-DD HH:MM:SS,mmm] EVENTTYPE: daten
        """
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S") + \
            f".{event.timestamp.microsecond // 1000:03d}"

        # Daten-String: bevorzugt der im Event hinterlegte Detail-Text
        # (START/STARTLINE), sonst aus Boot-Key ableiten.
        data = event.detail
        if not data:
            if event.event_type.value == "START":
                data = f"Boot={event.boot_key}"
            elif event.event_type.value == "PASSAGE":
                data = f"Boot={event.boot_key}"
            elif event.event_type.value == "FINISH":
                data = f"Boot={event.boot_key}"
            elif event.event_type.value == "CORRECTION_PLUS":
                data = f"Boot={event.boot_key};Delta=+1"
            elif event.event_type.value == "CORRECTION_MINUS":
                data = f"Boot={event.boot_key};Delta=-1"
            elif event.event_type.value == "INVALID":
                data = f"Boot={event.boot_key}"

        status = "VALID" if event.valid else "INVALID"
        return f"[{ts}] {event.event_type.value}: {data} STATUS: {status}"


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------

def write_race_json(
    path: str | Path,
    event: Event,
    config: RaceConfig,
    results: list[BoatResult],
    log_entries: list[RaceEvent] | None = None,
) -> Path:
    """Schreibt Endergebnisse als JSON-Datei.

    Args:
        path: Zielpfad.
        event: Veranstaltungsdaten.
        config: Rennkonfiguration.
        results: Endergebnisse (sortiert).
        log_entries: Optionaler Renn-Log.

    Returns:
        Pfad der geschriebenen Datei.
    """
    export = RaceResultExport(
        event=event,
        config=config,
        results=results,
        log_entries=log_entries or [],
    )
    return JsonResultWriter().write(path, export)
