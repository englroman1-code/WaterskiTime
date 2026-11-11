"""Tests für den JSON-Ergebnis-Export (JsonResultWriter).

Prüft die 2026-11-09 ergänzten Ergebnis-Spalten:
    - distance: Strecke in km (1. Runde + weitere Runden)
    - avg_speed: Durchschnittsgeschwindigkeit in km/h
    - race_time: Zeit auf die beste Strecke der Klasse umgerechnet
    - penalties/points: Platzhalter (aktuell leer)
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from python.core.models import BoatResult, Event, RaceConfig, Starter
from python.excel.json_result_writer import JsonResultWriter, RaceResultExport


def _starter(boot_key: str, klasse: str, race_number: int = 1) -> Starter:
    """Baut einen minimalen Starter für den Export."""
    return Starter(boot_key=boot_key, boat_number=boot_key,
                   skier=f"Boot {boot_key}", klasse=klasse,
                   race_number=race_number, startreihe=1)


def _result(boot_key: str, klasse: str, laps: int, seconds: float,
            place: int) -> BoatResult:
    """Baut ein Ergebnis mit Gesamtzeit und Rundenzahl."""
    return BoatResult(
        starter=_starter(boot_key, klasse),
        laps_count=laps,
        total_time=timedelta(seconds=seconds),
        best_lap=timedelta(seconds=5),
        place=place,
    )


def _config() -> RaceConfig:
    """Rennen mit 2 km erster Runde und 3,5 km Standardrunde."""
    return RaceConfig(race_number=1, race_duration_min=45,
                      start_interval_s=15, grid_time_s=30,
                      lap1_length_m=2000, standard_lap_length_m=3500)


def test_new_result_columns(tmp_path) -> None:
    """Distance, avg_speed, Race_time und Platzhalter werden geschrieben."""
    export = RaceResultExport(
        event=Event(title="Test", date="2026-11-09", organizer="WSC"),
        config=_config(),
        results=[
            _result("A", "Herren", laps=8, seconds=144, place=1),  # 2:24
            _result("B", "Herren", laps=7, seconds=170, place=2),  # 2:50
        ],
    )
    out = tmp_path / "RESULT_test.json"
    JsonResultWriter().write_all_races(out, [export])

    data = json.loads(out.read_text(encoding="utf-8"))
    results = data["races"][0]["classes"][0]["results"]
    winner, second = results

    # Distanz in km: 2 + (Runden - 1) * 3,5
    assert winner["distance"] == pytest.approx(26.5)
    assert second["distance"] == pytest.approx(23.0)

    # Durchschnittsgeschwindigkeit in km/h
    assert winner["avg_speed"] == pytest.approx(662.5)
    assert second["avg_speed"] == pytest.approx(487.1)

    # Rennzeit: eigene Zeit / eigene Distanz * beste Distanz der Klasse
    assert winner["race_time"] == "02:24.0"
    assert second["race_time"] == "03:15.8"

    # Platzhalter bleiben vorerst leer
    assert winner["penalties"] is None
    assert winner["points"] is None


def test_race_time_uses_best_distance_per_class(tmp_path) -> None:
    """Die Rennzeit bezieht sich auf die beste Distanz derselben Klasse."""
    export = RaceResultExport(
        event=Event(title="Test", date="2026-11-09", organizer="WSC"),
        config=_config(),
        results=[
            _result("A", "Herren", laps=8, seconds=144, place=1),   # 26,5 km
            _result("B", "Herren", laps=7, seconds=170, place=2),   # 23,0 km
            _result("C", "Damen", laps=6, seconds=200, place=1),    # 19,5 km
            _result("D", "Damen", laps=5, seconds=90, place=2),     # 16,0 km
        ],
    )
    out = tmp_path / "RESULT_test.json"
    JsonResultWriter().write_all_races(out, [export])

    data = json.loads(out.read_text(encoding="utf-8"))
    classes = {c["klasse"]: c["results"] for c in data["races"][0]["classes"]}

    # Damen: Siegerin 19,5 km; D fährt 16 km -> 90 s * 19,5/16 = 109,7 s
    assert classes["Damen"][1]["race_time"] == "01:49.6"
    # Herren unabhängig davon: 170 s * 26,5/23 = 195,9 s
    assert classes["Herren"][1]["race_time"] == "03:15.8"


def test_result_without_laps_has_zero_distance(tmp_path) -> None:
    """Boote ohne Runde: Distanz 0, keine Geschwindigkeit, keine Rennzeit."""
    export = RaceResultExport(
        event=Event(title="Test", date="2026-11-09", organizer="WSC"),
        config=_config(),
        results=[_result("A", "Herren", laps=0, seconds=0, place=0)],
    )
    out = tmp_path / "RESULT_test.json"
    JsonResultWriter().write_all_races(out, [export])

    data = json.loads(out.read_text(encoding="utf-8"))
    result = data["races"][0]["classes"][0]["results"][0]
    assert result["distance"] == 0.0
    assert result["avg_speed"] is None
    assert result["race_time"] == "–"
