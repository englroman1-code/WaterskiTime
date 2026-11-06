"""Tests für den ClassFinishTracker (manuelle Klassen-Beendigung, 2026-09-03).

Kundenentscheidung (2026-09-03): Nach Ablauf der Renndauer passiert NICHTS
automatisch. Der Bediener beendet jede Klasse manuell über finish_class().
Dabei werden alle Boote der Klasse als fertig markiert (finished_at = now)
und die Klasse wird CLOSED.
"""

from __future__ import annotations

from datetime import datetime

from python.core.class_finish_tracker import (
    STATE_CLOSED,
    STATE_WAITING,
    ClassFinishTracker,
)
from python.core.models import BoatState, RaceClass, Starter

BASE = datetime(2026, 8, 14, 8, 0, 0)


def _make_tracker() -> tuple[ClassFinishTracker, dict]:
    """Aufbau: MEN mit Booten A+B, DAMEN mit Boot C."""
    classes = {
        "MEN": RaceClass(name="MEN"),
        "DAMEN": RaceClass(name="DAMEN"),
    }
    boats = {
        "A": BoatState(starter=Starter(boot_key="A", skier="A", klasse="MEN")),
        "B": BoatState(starter=Starter(boot_key="B", skier="B", klasse="MEN")),
        "C": BoatState(starter=Starter(boot_key="C", skier="C", klasse="DAMEN")),
    }
    return ClassFinishTracker(classes, boats), boats


def test_finish_class_marks_all_boats_finished() -> None:
    """finish_class() setzt finished_at für ALLE Boote der Klasse."""
    tracker, boats = _make_tracker()
    assert tracker.finish_class("MEN", BASE) is True
    assert boats["A"].finished_at == BASE
    assert boats["B"].finished_at == BASE
    # Andere Klasse unberührt
    assert boats["C"].finished_at is None
    assert tracker.status()["MEN"] == STATE_CLOSED
    assert tracker.status()["DAMEN"] == STATE_WAITING


def test_finish_class_does_not_overwrite_existing_finished() -> None:
    """Bereits fertige Boote behalten ihren früheren finished_at."""
    tracker, boats = _make_tracker()
    earlier = datetime(2026, 8, 14, 7, 59, 0)
    boats["A"].finished_at = earlier
    tracker.finish_class("MEN", BASE)
    assert boats["A"].finished_at == earlier   # unverändert
    assert boats["B"].finished_at == BASE


def test_finish_class_unknown_class_returns_false() -> None:
    """Unbekannte Klasse → False, keine Änderung."""
    tracker, boats = _make_tracker()
    assert tracker.finish_class("JUNIOREN", BASE) is False
    assert boats["A"].finished_at is None


def test_all_closed_requires_every_class() -> None:
    """all_closed() erst wahr, wenn JEDE Klasse CLOSED ist."""
    tracker, _ = _make_tracker()
    tracker.finish_class("MEN", BASE)
    assert tracker.all_closed() is False   # DAMEN (C) noch offen
    tracker.finish_class("DAMEN", BASE)
    assert tracker.all_closed() is True


def test_status_and_reset() -> None:
    """status() liefert die Zustände, reset() setzt alles auf WAITING."""
    tracker, _ = _make_tracker()
    tracker.finish_class("MEN", BASE)
    assert tracker.status() == {"MEN": STATE_CLOSED, "DAMEN": STATE_WAITING}
    tracker.reset()
    assert tracker.status() == {"MEN": STATE_WAITING, "DAMEN": STATE_WAITING}
