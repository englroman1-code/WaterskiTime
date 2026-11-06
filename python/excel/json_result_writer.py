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
from datetime import datetime
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
            "results": [
                self._serialize_result(r) for r in export.results
            ],
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
                    "results": [self._serialize_result(r) for r in results],
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

    def _serialize_result(self, result: BoatResult) -> dict:
        """Serialisiert ein BoatResult-Objekt."""
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
