"""Tests für den LockoutManager (Sperrzeit, Pflichtenheft §5.2)."""

from __future__ import annotations

from datetime import datetime, timedelta

from python.core.lockout_manager import LockoutManager

BASE = datetime(2026, 8, 14, 8, 0, 0)


def test_first_input_always_allowed() -> None:
    """Erste Eingabe eines Boots ist immer erlaubt."""
    lockout = LockoutManager(lockout_seconds=2.0)
    assert lockout.is_allowed("A", BASE)


def test_second_input_within_lockout_rejected() -> None:
    """Eingabe innerhalb der Sperrzeit wird verworfen."""
    lockout = LockoutManager(lockout_seconds=2.0)
    lockout.register("A", BASE)
    assert not lockout.is_allowed("A", BASE + timedelta(seconds=1.0))


def test_input_after_lockout_allowed() -> None:
    """Eingabe nach Ablauf der Sperrzeit ist wieder erlaubt."""
    lockout = LockoutManager(lockout_seconds=2.0)
    lockout.register("A", BASE)
    assert lockout.is_allowed("A", BASE + timedelta(seconds=2.0))


def test_key_normalized_upper() -> None:
    """Boot-Keys werden unabhängig von Groß-/Kleinschreibung behandelt."""
    lockout = LockoutManager(lockout_seconds=2.0)
    lockout.register("a", BASE)          # klein registriert
    assert not lockout.is_allowed("A", BASE + timedelta(seconds=1.0))  # groß geprüft


def test_remaining_seconds() -> None:
    """remaining() liefert die Restzeit der Sperrzeit (GUI-Anzeige)."""
    lockout = LockoutManager(lockout_seconds=2.0)
    assert lockout.remaining("A", BASE) == timedelta()
    lockout.register("A", BASE)
    remaining = lockout.remaining("A", BASE + timedelta(seconds=0.5))
    assert remaining == timedelta(seconds=1.5)
    # Abgelaufen → 0, nie negativ
    assert lockout.remaining("A", BASE + timedelta(seconds=5)) == timedelta()


def test_reset_clears_all() -> None:
    """reset() löscht alle Sperrzeit-Zustände (neues Rennen)."""
    lockout = LockoutManager(lockout_seconds=2.0)
    lockout.register("A", BASE)
    lockout.register("B", BASE)
    lockout.reset()
    assert lockout.is_allowed("A", BASE)
    assert lockout.is_allowed("B", BASE)
