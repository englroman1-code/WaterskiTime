"""Tests für den ResultCalculator (Runden, Zeiten, Platzierung, §5.3)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from python.core.models import BoatState, Starter
from python.core.result_calculator import ResultCalculator

BASE = datetime(2026, 8, 14, 8, 0, 0)


def _boat(key: str, klasse: str = "MEN") -> BoatState:
    """Hilfsfunktion: neuer Boots-Zustand."""
    return BoatState(starter=Starter(boot_key=key, skier=f"Boot {key}",
                                     klasse=klasse))


def test_first_lap_starts_at_race_start() -> None:
    """Erste Runde: start = Rennstart, end = erste Passage."""
    state = _boat("A")
    lap = ResultCalculator.add_lap(state, BASE + timedelta(seconds=60), BASE)
    assert lap.number == 1
    assert lap.start_time == BASE
    assert lap.end_time == BASE + timedelta(seconds=60)
    assert lap.duration == timedelta(seconds=60)
    assert state.last_passage == lap.end_time


def test_followup_lap_starts_at_previous_passage() -> None:
    """Folge-Runde: start = vorige Passage."""
    state = _boat("A")
    ResultCalculator.add_lap(state, BASE + timedelta(seconds=60), BASE)
    lap2 = ResultCalculator.add_lap(state, BASE + timedelta(seconds=150), BASE)
    assert lap2.number == 2
    assert lap2.start_time == BASE + timedelta(seconds=60)
    assert lap2.duration == timedelta(seconds=90)


def test_add_lap_rejects_past_passage() -> None:
    """Passage vor Rundenbeginn ist ein Fehler (ValueError)."""
    state = _boat("A")
    with pytest.raises(ValueError):
        ResultCalculator.add_lap(state, BASE + timedelta(seconds=-5), BASE)


def test_state_properties() -> None:
    """laps_count, total_time und best_lap werden korrekt berechnet."""
    state = _boat("A")
    ResultCalculator.add_lap(state, BASE + timedelta(seconds=60), BASE)
    ResultCalculator.add_lap(state, BASE + timedelta(seconds=100), BASE)
    ResultCalculator.add_lap(state, BASE + timedelta(seconds=150), BASE)
    assert state.laps_count == 3
    assert state.total_time == timedelta(seconds=150)
    assert state.best_lap == timedelta(seconds=40)   # 60, 40, 50


def test_compute_results_ranks_by_laps_then_time() -> None:
    """Wertung: erst Rundenzahl, dann Gesamtzeit (Pflichtenheft §5.3)."""
    a, b, c = _boat("A"), _boat("B"), _boat("C")
    # A: 2 Runden, 200s | B: 2 Runden, 150s | C: 3 Runden
    ResultCalculator.add_lap(a, BASE + timedelta(seconds=90), BASE)
    ResultCalculator.add_lap(a, BASE + timedelta(seconds=200), BASE)
    ResultCalculator.add_lap(b, BASE + timedelta(seconds=70), BASE)
    ResultCalculator.add_lap(b, BASE + timedelta(seconds=150), BASE)
    ResultCalculator.add_lap(c, BASE + timedelta(seconds=60), BASE)
    ResultCalculator.add_lap(c, BASE + timedelta(seconds=120), BASE)
    ResultCalculator.add_lap(c, BASE + timedelta(seconds=180), BASE)

    results = ResultCalculator.compute_results({"A": a, "B": b, "C": c})
    assert [r.starter.boot_key for r in results] == ["C", "B", "A"]
    assert results[0].place == 1          # C: 3 Runden
    assert results[1].place == 2          # B: 2 Runden, 150s
    assert results[2].place == 3          # A: 2 Runden, 200s


def test_compute_results_unranked_boats_last() -> None:
    """Boote ohne Runde bekommen Platz 0 und stehen am Ende."""
    a, b = _boat("A"), _boat("B")
    ResultCalculator.add_lap(a, BASE + timedelta(seconds=60), BASE)
    results = ResultCalculator.compute_results({"A": a, "B": b})
    assert results[0].starter.boot_key == "A"
    assert results[0].place == 1
    assert results[1].starter.boot_key == "B"
    assert results[1].place == 0


def test_compute_results_places_per_class() -> None:
    """Platzierung wird PRO KLASSE vergeben (2026-09-04).

    In jeder Klasse gibt es einen Ersten, Zweiten, … – nicht global über
    alle Boote. Boot 172 (Klasse Herren) ist Erster seiner Klasse, auch
    wenn ein Boot einer anderen Klasse mehr Runden hat.
    """
    # Klasse "Promo Herren": Boot 70 mit 4 Runden
    promo = _boat("70", klasse="Promo Herren")
    ResultCalculator.add_lap(promo, BASE + timedelta(seconds=60), BASE)
    ResultCalculator.add_lap(promo, BASE + timedelta(seconds=120), BASE)
    ResultCalculator.add_lap(promo, BASE + timedelta(seconds=180), BASE)
    ResultCalculator.add_lap(promo, BASE + timedelta(seconds=240), BASE)

    # Klasse "Herren": Boot 172 mit 3 Runden
    herren = _boat("172", klasse="Herren")
    ResultCalculator.add_lap(herren, BASE + timedelta(seconds=60), BASE)
    ResultCalculator.add_lap(herren, BASE + timedelta(seconds=120), BASE)
    ResultCalculator.add_lap(herren, BASE + timedelta(seconds=180), BASE)

    results = ResultCalculator.compute_results({"70": promo, "172": herren})

    # Jedes Boot ist Erster seiner eigenen Klasse
    by_key = {r.starter.boot_key: r for r in results}
    assert by_key["70"].place == 1     # Promo Herren: Erster
    assert by_key["172"].place == 1    # Herren: Erster (nicht 2ter!)

    # Zwei Boote derselben Klasse: 1. und 2. Platz
    a = _boat("A", klasse="MEN")
    b = _boat("B", klasse="MEN")
    ResultCalculator.add_lap(a, BASE + timedelta(seconds=90), BASE)
    ResultCalculator.add_lap(a, BASE + timedelta(seconds=200), BASE)
    ResultCalculator.add_lap(b, BASE + timedelta(seconds=70), BASE)
    ResultCalculator.add_lap(b, BASE + timedelta(seconds=150), BASE)
    results2 = ResultCalculator.compute_results({"A": a, "B": b})
    by_key2 = {r.starter.boot_key: r for r in results2}
    assert by_key2["B"].place == 1     # 2 Runden, 150s → Erster
    assert by_key2["A"].place == 2     # 2 Runden, 200s → Zweiter
