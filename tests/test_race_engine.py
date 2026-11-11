"""Tests für die RaceEngine (Zustandsmaschine + Ereignisverarbeitung).

Die Zeitbasis wird über die injizierbaren now-Parameter kontrolliert –
keine echten Wartezeiten, deterministisch.

Szenario: Rennen mit 10 Minuten Dauer, 20 Sekunden Countdown (Startintervall).
Starter: A+B → Klasse MEN, C → Klasse DAMEN (Q7: mehrere Boote je Klasse).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from python.core.models import (
    Event,
    EventType,
    RaceConfig,
    RacePhase,
    Starter,
)
from python.core.race_engine import RaceEngine

BASE = datetime(2026, 8, 14, 8, 0, 0)
SEC = timedelta(seconds=1)


def _make_engine() -> RaceEngine:
    """Baut eine frisch geladene Engine (Countdown läuft ab BASE)."""
    engine = RaceEngine()
    engine.load_race(
        race=Event(title="ÖM Ybbs 2026", date="2026-08-14"),
        config=RaceConfig(
            race_number=1,
            race_duration_min=10,
            start_interval_s=20,
            grid_time_s=15,
        ),
        starters=[
            Starter(boot_key="A", skier="Boot A", klasse="MEN", race_number=1, startreihe=1),
            Starter(boot_key="B", skier="Boot B", klasse="MEN", race_number=1, startreihe=1),
            Starter(boot_key="C", skier="Boot C", klasse="DAMEN", race_number=1, startreihe=2),
        ],
        lockout_seconds=2.0,
    )
    engine.start_countdown(BASE)   # Countdown-Zeitbasis deterministisch setzen
    return engine


def _start_race(engine: RaceEngine, at: datetime) -> None:
    """Führt den Countdown bis zum Rennstart aus (Q8: automatisch)."""
    engine.tick(at + 19 * SEC)
    assert engine.phase == RacePhase.PRESTART
    engine.tick(at + 21 * SEC)
    assert engine.phase == RacePhase.ACTIVE


# ---------------------------------------------------------------------------
# Phasen / Countdown
# ---------------------------------------------------------------------------

def test_load_race_builds_boats_and_classes() -> None:
    """load_race baut Boots-Zustände und Klassen auf (Q7)."""
    engine = _make_engine()
    assert engine.phase == RacePhase.PRESTART
    assert set(engine.boats.keys()) == {"A", "B", "C"}
    assert set(engine.classes.keys()) == {"MEN", "DAMEN"}
    assert engine.boats["A"].starter.klasse == "MEN"
    assert engine.countdown_end == BASE + 20 * SEC


def test_countdown_auto_starts_race() -> None:
    """Q8: Der Countdown startet das Rennen automatisch (kein Startsignal)."""
    engine = _make_engine()
    engine.tick(BASE + 21 * SEC)
    assert engine.phase == RacePhase.ACTIVE
    assert engine.race_start == BASE + 21 * SEC
    assert engine.race_end == engine.race_start + 10 * 60 * SEC
    # START-Ereignis protokolliert (Systemereignis)
    assert engine.events[0].event_type == EventType.START
    assert engine.events[0].source == "SYSTEM"


def test_countdown_pause_blocks_auto_start() -> None:
    """Q8: Ein pausierter Countdown startet das Rennen nicht."""
    engine = _make_engine()
    engine.pause_countdown(BASE + 5 * SEC)
    assert engine.countdown_paused
    assert engine.countdown_remaining(BASE + 5 * SEC) == 15 * SEC
    # Lange Zeit vergeht – aber pausiert → kein Start
    engine.tick(BASE + 100 * SEC)
    assert engine.phase == RacePhase.PRESTART
    # Fortsetzen → Restzeit läuft exakt weiter (15s ab Fortsetzung)
    engine.resume_countdown(BASE + 100 * SEC)
    assert engine.countdown_end == BASE + 115 * SEC
    engine.tick(BASE + 114 * SEC)
    assert engine.phase == RacePhase.PRESTART
    engine.tick(BASE + 116 * SEC)
    assert engine.phase == RacePhase.ACTIVE


def test_race_ends_after_duration() -> None:
    """Nach Ablauf der Renndauer wechselt die Engine in die Endphase."""
    engine = _make_engine()
    _start_race(engine, BASE)
    engine.tick(BASE + 21 * SEC + 10 * 60 * SEC - SEC)
    assert engine.phase == RacePhase.ACTIVE
    engine.tick(BASE + 21 * SEC + 10 * 60 * SEC + SEC)
    assert engine.phase == RacePhase.FINISHING


# ---------------------------------------------------------------------------
# Hotkeys / Sperrzeit
# ---------------------------------------------------------------------------

def test_key_press_before_race_is_invalid() -> None:
    """Eingabe im Vorstart → INVALID (valid=False, aber protokolliert)."""
    engine = _make_engine()
    event = engine.handle_key_press("A", BASE + 10 * SEC)
    assert event.event_type == EventType.INVALID
    assert event.valid is False
    assert engine.events[-1] is event


def test_key_press_adds_lap() -> None:
    """Gültige Passage → PASSAGE-Event + Runde (1. Runde ab Rennstart)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    now = BASE + 21 * SEC + 60 * SEC
    event = engine.handle_key_press("A", now)
    assert event.event_type == EventType.PASSAGE
    assert event.valid is True
    state = engine.boats["A"]
    assert state.laps_count == 1
    assert state.laps[0].duration == 60 * SEC
    assert state.last_passage == now


def test_lockout_marks_second_input_invalid() -> None:
    """Zweite Eingabe innerhalb der Sperrzeit → INVALID (Pflichtenheft §5.2)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    base_passage = BASE + 21 * SEC + 60 * SEC
    engine.handle_key_press("A", base_passage)
    invalid = engine.handle_key_press("A", base_passage + 1 * SEC)
    assert invalid.event_type == EventType.INVALID
    assert invalid.valid is False
    assert engine.boats["A"].laps_count == 1   # keine zweite Runde

    # Nach Sperrzeit wieder erlaubt
    valid = engine.handle_key_press("A", base_passage + 3 * SEC)
    assert valid.valid is True
    assert engine.boats["A"].laps_count == 2


def test_unknown_key_raises() -> None:
    """Unbekannter Boot-Key → ValueError (Konfigurationsfehler)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    with pytest.raises(ValueError):
        engine.handle_key_press("Z", BASE + 60 * SEC)


# ---------------------------------------------------------------------------
# Rennende-Logik (manuelle Klassen-Beendigung, 2026-09-03)
# ---------------------------------------------------------------------------

def _go_finishing(engine: RaceEngine) -> None:
    """Bringt die Engine in die Endphase (Renndauer abgelaufen)."""
    _start_race(engine, BASE)
    engine.tick(BASE + 21 * SEC + 10 * 60 * SEC + SEC)
    assert engine.phase == RacePhase.FINISHING


def test_passage_after_duration_does_not_finish_automatically() -> None:
    """Nach Renndauer passiert bei einer Passage NICHTS automatisch (2026-09-03).

    Die frühere Letzte-Runde-Logik (finish_mode/TRIGGERED) wurde entfernt.
    Eine Passage in FINISHING ist weiterhin eine normale Runde – das Boot
    wird erst durch finish_class() beendet.
    """
    engine = _make_engine()
    _go_finishing(engine)
    now = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    event = engine.handle_key_press("A", now)
    assert event.event_type == EventType.PASSAGE
    assert event.valid is True
    state_a = engine.boats["A"]
    assert state_a.finished_at is None          # NICHT automatisch fertig
    assert engine.classes["MEN"].finish_state == "WAITING"
    assert engine.phase == RacePhase.FINISHING


def test_crossed_after_race_end_false_before_end() -> None:
    """Rennende-Ampel: vor Ablauf der Renndauer ist kein Boot 'im Ziel'."""
    engine = _make_engine()
    _start_race(engine, BASE)
    engine.handle_key_press("A", BASE + 21 * SEC + 30 * SEC)
    crossed = engine.get_crossed_after_race_end()
    assert crossed["A"] is False
    assert crossed["B"] is False
    assert crossed["C"] is False


def test_crossed_after_race_end_marks_only_crossing_boats() -> None:
    """Rennende-Ampel: nur Boote mit echter Passage nach race_end sind grün."""
    engine = _make_engine()
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.handle_key_press("A", t)

    crossed = engine.get_crossed_after_race_end()
    assert crossed["A"] is True
    assert crossed["B"] is False
    assert crossed["C"] is False


def test_crossed_after_race_end_ignores_manual_correction() -> None:
    """Eine +1-Korrektur darf kein falsches Grün erzeugen (Klickzeit!)."""
    engine = _make_engine()
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.handle_manual_correction("A", 1, t)

    assert engine.boats["A"].laps_count == 1
    assert engine.get_crossed_after_race_end()["A"] is False


def test_crossed_after_race_end_survives_serialization() -> None:
    """Die echte Zielpassage überlebt to_dict/restore_from_state."""
    engine = _make_engine()
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.handle_key_press("A", t)

    restored = _make_engine()
    restored.restore_from_state(engine.to_dict())

    crossed = restored.get_crossed_after_race_end()
    assert crossed["A"] is True
    assert crossed["B"] is False


def test_crossed_after_race_end_backfilled_from_events() -> None:
    """Alte Crash-States ohne last_real_passage werden aus Events ergänzt."""
    engine = _make_engine()
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.handle_key_press("A", t)

    saved = engine.to_dict()
    del saved["boats"]["A"]["last_real_passage"]   # altes Schema simulieren

    restored = _make_engine()
    restored.restore_from_state(saved)

    assert restored.get_crossed_after_race_end()["A"] is True


def test_finish_class_marks_boats_and_logs_finish_events() -> None:
    """finish_class() beendet alle Boote der Klasse + FINISH-Events."""
    engine = _make_engine()
    _go_finishing(engine)
    now = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    assert engine.finish_class("MEN", now) is True
    assert engine.boats["A"].finished_at == now
    assert engine.boats["B"].finished_at == now
    assert engine.classes["MEN"].finish_state == "CLOSED"
    # FINISH-Ereignis für jedes Boot der Klasse
    finish_events = [e for e in engine.events
                     if e.event_type == EventType.FINISH]
    assert {e.boot_key for e in finish_events} == {"A", "B"}
    # DAMEN (C) noch offen → kein FINISHED
    assert engine.phase == RacePhase.FINISHING


def test_finished_boat_rejects_further_passages() -> None:
    """Ein beendetes Boot nimmt keine weiteren Passagen mehr an (INVALID)."""
    engine = _make_engine()
    _go_finishing(engine)
    now = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.finish_class("MEN", now)
    event = engine.handle_key_press("A", now + 10 * SEC)
    assert event.event_type == EventType.INVALID
    assert event.valid is False
    assert engine.boats["A"].laps_count == 0   # keine weitere Runde


def test_all_classes_finished_ends_race() -> None:
    """Wenn alle Klassen manuell beendet sind, wird das Rennen FINISHED."""
    engine = _make_engine()
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.finish_class("MEN", t)
    assert engine.phase == RacePhase.FINISHING   # DAMEN (C) noch offen
    engine.finish_class("DAMEN", t + 90 * SEC)
    assert engine.phase == RacePhase.FINISHED
    assert engine.classes["MEN"].finish_state == "CLOSED"
    assert engine.classes["DAMEN"].finish_state == "CLOSED"


def test_finish_class_unknown_class_returns_false() -> None:
    """Unbekannte Klasse → False, keine Änderung."""
    engine = _make_engine()
    _go_finishing(engine)
    now = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    assert engine.finish_class("JUNIOREN", now) is False
    assert engine.phase == RacePhase.FINISHING


# ---------------------------------------------------------------------------
# Rennwechsel (Bugfix 2026-09-02)
# ---------------------------------------------------------------------------

def test_load_race_after_finished_race_resets_phase() -> None:
    """Bugfix: Nach beendetem Rennen (FINISHED) muss der Rennwechsel die
    Engine auf RESET setzen – sonst bleibt die Vorstartzeit 0 und der
    PLAY-Button ist wirkungslos (on_start_race prüft phase == RESET)."""
    engine = _make_engine()

    # --- Rennen 1 komplett durchspielen bis FINISHED ----------------------
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.finish_class("MEN", t)
    engine.finish_class("DAMEN", t + 90 * SEC)
    assert engine.phase == RacePhase.FINISHED

    # --- Rennen 2 laden (anderes Startintervall: 7 s) ---------------------
    engine.load_race(
        race=Event(title="ÖM Ybbs 2026", date="2026-08-14"),
        config=RaceConfig(
            race_number=2,
            race_duration_min=12,
            start_interval_s=7,
            grid_time_s=10,
        ),
        starters=[
            Starter(boot_key="A", skier="Boot A", klasse="MEN",
                    race_number=2, startreihe=1),
            Starter(boot_key="B", skier="Boot B", klasse="MEN",
                    race_number=2, startreihe=1),
        ],
        lockout_seconds=2.0,
    )

    # Phase + Zeitstempel müssen zurückgesetzt sein (RESET)
    assert engine.phase == RacePhase.RESET
    assert engine.countdown_end is None
    assert engine.race_start is None
    assert engine.race_end is None
    assert engine.events == []

    # PLAY-Button-Pfad: start_countdown() muss funktionieren
    engine.start_countdown(BASE)
    assert engine.phase == RacePhase.PRESTART
    # Neues Startintervall von Rennen 2 (7 s) – nicht das alte von Rennen 1
    assert engine.countdown_end == BASE + 7 * SEC

    # Countdown läuft ab → Rennen startet automatisch (Q8)
    engine.tick(BASE + 8 * SEC)
    assert engine.phase == RacePhase.ACTIVE
    assert engine.race_start == BASE + 8 * SEC


def test_finished_race_results_persist_across_race_switch() -> None:
    """Option 1 (2026-09-03): Ergebnisse eines beendeten Rennens bleiben
    beim Rennwechsel erhalten – beim Zurückwechseln sind sie wieder da."""
    engine = _make_engine()

    # --- Rennen 1 durchspielen: Runden + beenden ---------------------------
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    # Boot A fährt 3 Runden, Boot B 2 Runden
    engine.handle_key_press("A", t)
    engine.handle_key_press("B", t + 5 * SEC)
    engine.handle_key_press("A", t + 10 * SEC)
    engine.handle_key_press("B", t + 15 * SEC)
    engine.handle_key_press("A", t + 20 * SEC)
    engine.finish_class("MEN", t + 30 * SEC)
    engine.finish_class("DAMEN", t + 90 * SEC)
    assert engine.phase == RacePhase.FINISHED
    assert engine.boats["A"].laps_count == 3
    assert engine.boats["B"].laps_count == 2

    # --- Zu Rennen 2 wechseln ----------------------------------------------
    engine.load_race(
        race=Event(title="ÖM Ybbs 2026", date="2026-08-14"),
        config=RaceConfig(race_number=2, race_duration_min=12,
                          start_interval_s=7, grid_time_s=10),
        starters=[
            Starter(boot_key="A", skier="Boot A", klasse="MEN",
                    race_number=2, startreihe=1),
            Starter(boot_key="B", skier="Boot B", klasse="MEN",
                    race_number=2, startreihe=1),
        ],
        lockout_seconds=2.0,
    )
    assert engine.phase == RacePhase.RESET
    assert engine.boats["A"].laps_count == 0  # Rennen 2 frisch

    # --- Zurück zu Rennen 1 wechseln: Ergebnisse wiederherstellen ----------
    engine.load_race(
        race=Event(title="ÖM Ybbs 2026", date="2026-08-14"),
        config=RaceConfig(race_number=1, race_duration_min=10,
                          start_interval_s=20, grid_time_s=15),
        starters=[
            Starter(boot_key="A", skier="Boot A", klasse="MEN",
                    race_number=1, startreihe=1),
            Starter(boot_key="B", skier="Boot B", klasse="MEN",
                    race_number=1, startreihe=1),
            Starter(boot_key="C", skier="Boot C", klasse="DAMEN",
                    race_number=1, startreihe=2),
        ],
        lockout_seconds=2.0,
    )
    # Ergebnisse sind wieder da
    assert engine.boats["A"].laps_count == 3
    assert engine.boats["B"].laps_count == 2
    assert engine.boats["A"].finished_at is not None
    # Klassen-Status wiederhergestellt (CLOSED)
    assert engine.classes["MEN"].finish_state == "CLOSED"
    assert engine.classes["DAMEN"].finish_state == "CLOSED"
    # Events wiederhergestellt (Renn-Log)
    assert len(engine.events) > 0
    # Phase bleibt RESET (frisch geladen, bereit für erneuten Start)
    assert engine.phase == RacePhase.RESET


def test_export_collects_all_finished_races() -> None:
    """Option 1 (2026-09-03): finished_races enthält alle beendeten Rennen."""
    engine = _make_engine()

    # Rennen 1 beenden
    _go_finishing(engine)
    t = BASE + 21 * SEC + 10 * 60 * SEC + 30 * SEC
    engine.finish_class("MEN", t)
    engine.finish_class("DAMEN", t + 90 * SEC)
    assert engine.phase == RacePhase.FINISHED
    assert 1 in engine.finished_races

    # Rennen 2 beenden
    engine.load_race(
        race=Event(title="ÖM Ybbs 2026", date="2026-08-14"),
        config=RaceConfig(race_number=2, race_duration_min=12,
                          start_interval_s=7, grid_time_s=10),
        starters=[
            Starter(boot_key="A", skier="Boot A", klasse="MEN",
                    race_number=2, startreihe=1),
            Starter(boot_key="B", skier="Boot B", klasse="MEN",
                    race_number=2, startreihe=1),
        ],
        lockout_seconds=2.0,
    )
    engine.start_countdown(BASE)
    engine.tick(BASE + 8 * SEC)
    engine.finish_class("MEN", BASE + 8 * SEC + 60 * SEC)
    assert engine.phase == RacePhase.FINISHED
    assert 2 in engine.finished_races

    # Beide Rennen gespeichert
    assert set(engine.finished_races.keys()) == {1, 2}
    # Ergebnisse je Rennen vorhanden
    assert len(engine.finished_races[1]["results"]) == 3
    assert len(engine.finished_races[2]["results"]) == 2


# ---------------------------------------------------------------------------
# Manuelle Korrektur (Q6: nur +1)
# ---------------------------------------------------------------------------

def test_manual_correction_plus_one() -> None:
    """Manuell +1 → CORRECTION_PLUS-Event + zusätzliche Runde (Pflichtenheft §6)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    now = BASE + 21 * SEC + 60 * SEC
    event = engine.handle_manual_correction("A", 1, now)
    assert event.event_type == EventType.CORRECTION_PLUS
    assert event.source == "MANUAL"
    assert engine.boats["A"].laps_count == 1


def test_manual_correction_minus_rejected() -> None:
    """Q6: −1 ist im MVP nicht erlaubt → ValueError."""
    engine = _make_engine()
    _start_race(engine, BASE)
    with pytest.raises(ValueError):
        engine.handle_manual_correction("A", -1, BASE + 60 * SEC)


def test_manual_correction_before_race_rejected() -> None:
    """Korrektur im Vorstart ist nicht möglich → ValueError."""
    engine = _make_engine()
    with pytest.raises(ValueError):
        engine.handle_manual_correction("A", 1, BASE + 10 * SEC)


# ---------------------------------------------------------------------------
# Reset / Wertung
# ---------------------------------------------------------------------------

def test_reset_clears_state_and_enters_reset_phase() -> None:
    """reset() leert Zustände und bringt Engine in RESET-Phase (Play-Button)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    engine.handle_key_press("A", BASE + 21 * SEC + 60 * SEC)
    engine.reset()
    assert engine.phase == RacePhase.RESET
    assert engine.events == []
    assert all(b.laps_count == 0 for b in engine.boats.values())
    assert all(b.lockout_until is None for b in engine.boats.values())
    assert all(cls.finish_state == "WAITING" for cls in engine.classes.values())
    assert engine.countdown_end is None
    # Nach start_countdown() → PRESTART
    engine.start_countdown()
    assert engine.phase == RacePhase.PRESTART
    assert engine.countdown_end is not None


def test_get_placements_ranks_correctly() -> None:
    """get_placements() liefert die Wertung (Runden primär, Zeit sekundär)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    # A: 2 Runden (120s gesamt) | B: 2 Runden (100s) | C: 1 Runde
    engine.handle_key_press("A", t0 + 60 * SEC)
    engine.handle_key_press("A", t0 + 120 * SEC)
    engine.handle_key_press("B", t0 + 50 * SEC)
    engine.handle_key_press("B", t0 + 100 * SEC)
    engine.handle_key_press("C", t0 + 70 * SEC)

    placements = engine.get_placements()
    assert [p.starter.boot_key for p in placements] == ["B", "A", "C"]
    # Platzierung PRO KLASSE (2026-09-04): B und A sind in "MEN" (1./2.),
    # C ist in "DAMEN" und damit Erster seiner Klasse.
    assert placements[0].place == 1    # B: MEN, 2 Runden, 100s → Erster
    assert placements[1].place == 2    # A: MEN, 2 Runden, 120s → Zweiter
    assert placements[2].place == 1    # C: DAMEN, 1 Runde → Erster seiner Klasse
    # Plätze wurden in die BoatStates zurückgeschrieben (GUI-Tabelle)
    assert engine.boats["B"].place == 1


# ------------------------------------------------------------------
# Serialisierung (Crash-Recovery)
# ------------------------------------------------------------------

def test_to_dict_contains_race_number() -> None:
    """to_dict() enthält die Rennnummer."""
    engine = _make_engine()
    state = engine.to_dict()
    assert state["race_number"] == 1


def test_to_dict_contains_phase() -> None:
    """to_dict() enthält die aktuelle Phase."""
    engine = _make_engine()
    state = engine.to_dict()
    assert state["phase"] == "PRESTART"


def test_to_dict_contains_boats() -> None:
    """to_dict() enthält alle Boote mit ihren Daten."""
    engine = _make_engine()
    state = engine.to_dict()
    assert "A" in state["boats"]
    assert state["boats"]["A"]["skier"] == "Boot A"
    assert state["boats"]["A"]["klasse"] == "MEN"
    assert state["boats"]["A"]["laps_count"] == 0


def test_to_dict_contains_events_after_passage() -> None:
    """to_dict() enthält Events nach einer Passage."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.handle_key_press("A", t0 + 30 * SEC)

    state = engine.to_dict()
    assert len(state["events"]) >= 2  # START + PASSAGE
    event_types = [e["event_type"] for e in state["events"]]
    assert "START" in event_types
    assert "PASSAGE" in event_types


def test_to_dict_serializes_datetime() -> None:
    """to_dict() serialisiert datetime als ISO-String."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.handle_key_press("A", t0 + 30 * SEC)

    state = engine.to_dict()
    assert isinstance(state["race_start"], str)
    # Kann zurück-konvertiert werden
    from datetime import datetime
    datetime.fromisoformat(state["race_start"])


# ---------------------------------------------------------------------------
# Zeitversetzte Starts (Variante A) – Startreihen
# ---------------------------------------------------------------------------

def test_start_race_sets_individual_start_times() -> None:
    """Variante A: start_race setzt je Boot einen individuellen Startzeitpunkt.

    Reihe 1 startet bei T=0, Reihe 2 bei +Grid Time (15s), Reihe 3 bei
    +2×Grid Time.
    """
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    assert engine.boats["A"].start_time == t0            # Reihe 1
    assert engine.boats["B"].start_time == t0            # Reihe 1
    assert engine.boats["C"].start_time == t0 + 15 * SEC  # Reihe 2


def test_passage_before_start_is_invalid() -> None:
    """Variante A: Passage vor dem individuellen Start ist UNGÜLTIG."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    # Boot C (Reihe 2) drückt vor seinem Start (t0 + 15s)
    event = engine.handle_key_press("C", t0 + 5 * SEC)
    assert event.event_type == EventType.INVALID
    assert engine.boats["C"].laps_count == 0


def test_passage_after_start_is_valid() -> None:
    """Variante A: Passage nach dem individuellen Start ist gültig."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    # Boot C (Reihe 2) drückt nach seinem Start (t0 + 15s)
    event = engine.handle_key_press("C", t0 + 20 * SEC)
    assert event.event_type == EventType.PASSAGE
    assert engine.boats["C"].laps_count == 1


def test_startline_events_emitted() -> None:
    """Variante A: STARTLINE-Ereignisse für jede gestartete Startreihe."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    # tick() bis nach dem Start von Reihe 2 (t0 + 15s)
    engine.tick(t0 + 16 * SEC)
    startline_events = [e for e in engine.events
                        if e.event_type == EventType.STARTLINE]
    # Reihe 1 (t0) und Reihe 2 (t0+15s) gestartet
    assert len(startline_events) == 2
    assert startline_events[0].timestamp == t0
    assert startline_events[1].timestamp == t0 + 15 * SEC


def test_start_line_remaining_and_next() -> None:
    """Variante A: Countdown bis zur nächsten Startreihe."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    # Kurz nach Rennstart: nächste Startreihe ist 2, Restzeit ~15s
    assert engine.next_start_line(t0 + 1 * SEC) == 2
    remaining = engine.start_line_remaining(t0 + 1 * SEC)
    assert remaining == 14 * SEC
    # Nach Start von Reihe 2: keine weitere Startreihe
    engine.tick(t0 + 16 * SEC)
    assert engine.next_start_line(t0 + 16 * SEC) is None
    assert engine.start_line_remaining(t0 + 16 * SEC) == timedelta()


def test_race_elapsed_counts_until_finished() -> None:
    """Renndauer (2026-11-09): zählt ab erstem Start und friert bei FINISHED ein."""
    engine = _make_engine()
    assert engine.race_elapsed(BASE) == timedelta()   # noch nicht gestartet
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    # Kurz nach dem Start: Renndauer läuft mit
    assert engine.race_elapsed(t0 + 5 * SEC) == 5 * SEC
    # Alle Startreihen gestartet (Reihe 2 bei t0 + 15 s)
    engine.tick(t0 + 16 * SEC)
    assert engine.next_start_line(t0 + 16 * SEC) is None
    assert engine.race_elapsed(t0 + 30 * SEC) == 30 * SEC

    # Rennen beenden: FINISHED friert die Anzeige auf den letzten Zieleinlauf ein
    engine.finish_class("MEN", t0 + 100 * SEC)
    engine.finish_class("DAMEN", t0 + 120 * SEC)
    assert engine.phase == RacePhase.FINISHED
    assert engine.race_elapsed(t0 + 999 * SEC) == 120 * SEC


def test_start_time_serialized_and_restored() -> None:
    """Variante A: start_time und started_lines überleben Crash-Recovery."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.tick(t0 + 16 * SEC)  # Reihe 2 gestartet

    state = engine.to_dict()
    assert state["boats"]["C"]["start_time"] is not None
    assert state["started_lines"] == [1, 2]

    restored = RaceEngine()
    restored.load_race(
        race=Event(title="ÖM Ybbs 2026", date="2026-08-14"),
        config=RaceConfig(
            race_number=1,
            race_duration_min=10,
            start_interval_s=20,
            grid_time_s=15,
        ),
        starters=[
            Starter(boot_key="A", skier="Boot A", klasse="MEN", race_number=1, startreihe=1),
            Starter(boot_key="B", skier="Boot B", klasse="MEN", race_number=1, startreihe=1),
            Starter(boot_key="C", skier="Boot C", klasse="DAMEN", race_number=1, startreihe=2),
        ],
        lockout_seconds=2.0,
    )
    restored.restore_from_state(state)
    assert restored.boats["C"].start_time == t0 + 15 * SEC
    assert restored._started_lines == {1, 2}


def test_startline_event_has_race_and_line_detail() -> None:
    """STARTLINE-Events tragen Race/Line für das Renn-Log."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.tick(t0 + 16 * SEC)

    startlines = [e for e in engine.events
                  if e.event_type == EventType.STARTLINE]
    assert startlines
    assert startlines[0].detail == "Race=1;Line=1"
    assert startlines[-1].detail == "Race=1;Line=2"


def test_to_dict_contains_lap_details() -> None:
    """to_dict() speichert vollständige Runden (Start/Ende), nicht nur Counts."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.handle_key_press("A", t0 + 30 * SEC)

    state = engine.to_dict()
    laps = state["boats"]["A"]["laps"]
    assert len(laps) == 1
    assert laps[0]["number"] == 1
    assert laps[0]["start_time"] == t0.isoformat()
    assert laps[0]["end_time"] == (t0 + 30 * SEC).isoformat()


def test_restore_laps_exactly() -> None:
    """Crash-Recovery stellt Rundenzeiten exakt wieder her (keine Mittelung)."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.handle_key_press("A", t0 + 30 * SEC)
    engine.handle_key_press("A", t0 + 70 * SEC)

    state = engine.to_dict()
    restored = _make_engine()
    restored.restore_from_state(state)

    original_durations = [lap.duration for lap in engine.boats["A"].laps]
    restored_durations = [lap.duration for lap in restored.boats["A"].laps]
    assert restored_durations == original_durations
    assert restored.boats["A"].best_lap == engine.boats["A"].best_lap


def test_restore_without_lap_details_does_not_synthesize() -> None:
    """Alter State ohne Lap-Details erzeugt keine falschen Rundenzeiten."""
    engine = _make_engine()
    _start_race(engine, BASE)
    t0 = BASE + 21 * SEC
    engine.handle_key_press("A", t0 + 30 * SEC)

    state = engine.to_dict()
    del state["boats"]["A"]["laps"]
    state["boats"]["A"]["laps_count"] = 2
    state["boats"]["A"]["total_time_s"] = 120.0

    restored = _make_engine()
    restored.restore_from_state(state)
    assert restored.boats["A"].laps == []
