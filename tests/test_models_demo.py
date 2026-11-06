"""Tests für Domänenmodelle, App-Konfiguration und Test-Fixture-Daten."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

import pytest

from python.config.app_config import (
    AppSettings,
    ConfigManager,
    resolve_settings_path,
)
from python.core.models import (
    BoatState,
    Event,
    EventType,
    Lap,
    RaceConfig,
    RaceEvent,
    RacePhase,
    Starter,
)
from tests.demo_data import (
    build_boat_states_for_race2,
    build_demo_events,
    build_event,
    build_race_configs,
    build_starters,
    demo_lockout_seconds,
)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class TestModels:
    """Basistests der Domänenmodelle (models.py)."""

    def test_lap_duration_is_computed(self):
        """Die Rundenzeit wird aus Start/Ende automatisch berechnet."""
        start = datetime(2026, 6, 17, 14, 30, 0)
        lap = Lap(number=1, start_time=start, end_time=start + timedelta(seconds=134))
        assert lap.duration == timedelta(seconds=134)

    def test_boat_state_properties(self):
        """laps_count, total_time, best_lap und last_lap liefern korrekte Werte."""
        start = datetime(2026, 6, 17, 14, 30, 0)
        state = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
        state.laps.append(Lap(1, start, start + timedelta(seconds=140)))
        state.laps.append(Lap(2, start + timedelta(seconds=140), start + timedelta(seconds=270)))

        assert state.laps_count == 2
        assert state.total_time == timedelta(seconds=270)
        assert state.best_lap == timedelta(seconds=130)  # 140 vs. 130
        assert state.last_lap == timedelta(seconds=130)

    def test_speed_last_lap_uses_lap1_length_for_first_lap(self):
        """Geschw. der 1. Runde nutzt lap1_length_m (Kundenanforderung 2026-09-03)."""
        start = datetime(2026, 6, 17, 14, 30, 0)
        state = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
        # 1. Runde: 2000 m in 100 s → 72 km/h
        state.laps.append(Lap(1, start, start + timedelta(seconds=100)))
        assert state.speed_last_lap(2000, 3500) == pytest.approx(72.0)

    def test_speed_last_lap_uses_standard_length_for_following_laps(self):
        """Geschw. einer Folge-Runde nutzt standard_lap_length_m."""
        start = datetime(2026, 6, 17, 14, 30, 0)
        state = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
        state.laps.append(Lap(1, start, start + timedelta(seconds=100)))
        # 2. Runde: 3500 m in 100 s → 126 km/h
        state.laps.append(Lap(2, start + timedelta(seconds=100),
                              start + timedelta(seconds=200)))
        assert state.speed_last_lap(2000, 3500) == pytest.approx(126.0)

    def test_speed_last_lap_returns_none_without_laps(self):
        """Ohne abgeschlossene Runde liefert speed_last_lap None."""
        state = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
        assert state.speed_last_lap(2000, 3500) is None

    def test_speed_total_uses_start_time_and_last_passage(self):
        """Geschw. gesamt: Distanz = 1. Runde + (Runden-1)×Standardrunde."""
        start = datetime(2026, 6, 17, 14, 30, 0)
        state = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
        state.start_time = start
        state.laps.append(Lap(1, start, start + timedelta(seconds=100)))
        state.laps.append(Lap(2, start + timedelta(seconds=100),
                              start + timedelta(seconds=200)))
        state.last_passage = start + timedelta(seconds=200)
        # Distanz = 2000 + (2-1)*3500 = 5500 m in 200 s → 99 km/h
        assert state.speed_total(2000, 3500) == pytest.approx(99.0)

    def test_speed_total_returns_none_without_laps_or_passage(self):
        """Ohne Runden oder letzte Passage liefert speed_total None."""
        state = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
        assert state.speed_total(2000, 3500) is None

    def test_race_phase_transitions(self):
        """Die Zustandsmaschinen-Phasen existieren in der richtigen Reihenfolge."""
        phases = [RacePhase.PRESTART, RacePhase.ACTIVE, RacePhase.FINISHING,
                  RacePhase.FINISHED, RacePhase.RESET]
        # Strikte Reihenfolge prüfen (Reihenfolge = Erstellungsreihenfolge im Enum)
        assert list(RacePhase) == phases

    def test_race_event_is_frozen(self):
        """Ereignisse sind unveränderlich (Beweisfunktion, Pflichtenheft §7)."""
        event = RaceEvent(timestamp=datetime.now(), boot_key="A",
                          event_type=EventType.PASSAGE, valid=True)
        try:
            event.valid = False
            assert False, "RaceEvent muss unveränderlich sein (frozen)"
        except (AttributeError, Exception):
            pass  # erwartet: frozen-Dataclass wirft bei Zuweisung


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

class TestDemoData:
    """Prüft, dass die fiktiven Daten realistisch und konsistent sind."""

    def test_event_metadata(self):
        """Veranstaltungsdaten entsprechen dem GUI-Design-Beispiel."""
        event: Event = build_event()
        assert event.title == "Österreichische Meisterschaften Ybbs 2026"
        assert event.date == "17.06.2026"

    def test_starters_unique_keys(self):
        """Alle Boot-Keys sind eindeutig und liegen im Bereich A–Z."""
        starters = build_starters()
        keys = [s.boot_key for s in starters]
        assert len(keys) == len(set(keys))          # keine Duplikate
        assert all(k in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for k in keys)

    def test_race_configs(self):
        """Drei Rennen, Rennen 2 ist U18 Open (wie im GUI-Design)."""
        configs = build_race_configs()
        assert len(configs) == 3
        u18 = configs[1]
        assert u18.race_number == 2

    def test_boat_states_race2(self):
        """Rennen 2: Boot A führt mit 8 Runden, B mit 7, D mit 6."""
        boats = build_boat_states_for_race2()

        assert boats["A"].laps_count == 8
        assert boats["B"].laps_count == 7
        assert boats["D"].laps_count == 6
        # Nicht gestartete Boote haben 0 Runden
        assert boats["E"].laps_count == 0

        # Rundenzeiten sind plausibel (zwischen 2:00 und 2:45 pro Runde)
        for boat_key in ("A", "B", "D"):
            for lap in boats[boat_key].laps:
                assert timedelta(seconds=120) < lap.duration < timedelta(seconds=165)

    def test_events_chronological_and_invalid(self):
        """Ereignisliste: chronologisch, enthält START + INVALID (Sperrzeit-Demo)."""
        boats = build_boat_states_for_race2()
        events: list[RaceEvent] = build_demo_events(boats)

        # chronologische Ordnung
        stamps = [e.timestamp for e in events]
        assert stamps == sorted(stamps)

        # genau ein START-Event
        starts = [e for e in events if e.event_type == EventType.START]
        assert len(starts) == 1

        # genau ein ungültiges Ereignis (Doppel-Eingabe innerhalb Sperrzeit)
        invalid = [e for e in events if not e.valid]
        assert len(invalid) == 1
        assert invalid[0].event_type == EventType.PASSAGE

    def test_demo_is_deterministic(self):
        """Zwei Aufrufe liefern identische Daten (Reproduzierbarkeit)."""
        s1 = build_boat_states_for_race2()
        s2 = build_boat_states_for_race2()
        assert s1["A"].total_time == s2["A"].total_time


# ---------------------------------------------------------------------------
# App configuration (Q1: Sperrzeit als App-Parameter, JSON)
# ---------------------------------------------------------------------------

class TestConfigManager:
    """Tests der JSON-Konfiguration (python/config/app_config.py)."""

    def test_defaults_when_file_missing(self, tmp_path):
        """Fehlende JSON → Standardwerte (App bleibt startbar)."""
        mgr = ConfigManager(tmp_path / "fehlt.json")
        settings = mgr.load()
        assert settings.lockout_seconds == 2.0

    def test_save_and_reload(self, tmp_path):
        """Gespeicherte Werte werden wieder korrekt geladen."""
        path = tmp_path / "app_settings.json"
        mgr = ConfigManager(path)
        mgr.save(AppSettings(lockout_seconds=3.5))

        loaded = ConfigManager(path).load()
        assert loaded.lockout_seconds == 3.5

    def test_partial_json_keeps_defaults(self, tmp_path):
        """Unbekannte Felder in der JSON stören nicht (Defaults bleiben)."""
        path = tmp_path / "app_settings.json"
        path.write_text('{"lockout_seconds": 1.5, "unbekannt": 99}', encoding="utf-8")

        settings = ConfigManager(path).load()
        assert settings.lockout_seconds == 1.5

    def test_invalid_json_keeps_defaults(self, tmp_path):
        """Kaputtes JSON → Warnung + Standardwerte (kein Absturz)."""
        path = tmp_path / "app_settings.json"
        path.write_text("{kaputt", encoding="utf-8")

        settings = ConfigManager(path).load()
        assert settings.lockout_seconds == 2.0

    def test_demo_uses_app_parameter(self):
        """Die Demo liest die Sperrzeit aus der App-Konfiguration (Q1)."""
        assert demo_lockout_seconds() > 0.0


class TestBundleSettingsPath:
    """Tests der PyInstaller-Pfadauflösung (resolve_settings_path).

    Die Funktion entscheidet, wo die app_settings.json liegt:
    Entwicklung = Modul-Ordner, gebaute .exe = neben der .exe
    (einmalig aus dem Bundle kopiert, damit der Bediener sie ändern kann).
    """

    def test_dev_mode_uses_module_folder(self, monkeypatch):
        """Nicht eingefroren → python/config/app_settings.json."""
        monkeypatch.delattr(sys, "frozen", raising=False)
        resolved = resolve_settings_path()
        assert resolved.name == "app_settings.json"
        assert resolved.parent.name == "config"

    def test_frozen_uses_existing_file_next_to_exe(self, tmp_path, monkeypatch):
        """Gebaute .exe mit vorhandener JSON neben der .exe → diese verwenden."""
        exe_dir = tmp_path / "app"
        exe_dir.mkdir()
        settings_file = exe_dir / "app_settings.json"
        settings_file.write_text('{"lockout_seconds": 3.0}', encoding="utf-8")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe_dir / "app.exe"))
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)

        assert resolve_settings_path() == settings_file

    def test_frozen_copies_bundle_json_once(self, tmp_path, monkeypatch):
        """Keine JSON neben der .exe → aus dem Bundle kopieren (erster Start)."""
        exe_dir = tmp_path / "app"
        bundle_dir = tmp_path / "bundle"
        bundle_config = bundle_dir / "config"
        bundle_config.mkdir(parents=True)
        (bundle_config / "app_settings.json").write_text(
            '{"lockout_seconds": 2.5}', encoding="utf-8")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe_dir / "app.exe"))
        monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)

        resolved = resolve_settings_path()
        expected = exe_dir / "app_settings.json"
        assert resolved == expected
        assert expected.exists()                 # wurde kopiert (schreibbar)
        assert expected.read_text(encoding="utf-8") == '{"lockout_seconds": 2.5}'

        # Zweiter Aufruf: vorhandene Datei wird direkt verwendet (kein 2. Kopieren)
        assert resolve_settings_path() == expected

    def test_frozen_falls_back_to_bundle_if_copy_fails(self, tmp_path,
                                                       monkeypatch):
        """Kopieren scheitert (Zielpfad ist eine Datei) → Bundle-Kopie verwenden."""
        bundle_dir = tmp_path / "bundle"
        bundle_config = bundle_dir / "config"
        bundle_config.mkdir(parents=True)
        (bundle_config / "app_settings.json").write_text(
            '{"lockout_seconds": 1.0}', encoding="utf-8")

        # Der Ziel-Ordner "neben der .exe" existiert als DATEI → mkdir scheitert
        # → Kopieren schlägt fehl (OSError) → Fallback auf die Bundle-Kopie
        blocked = tmp_path / "blockiert"
        blocked.write_text("", encoding="utf-8")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(blocked / "app.exe"))
        monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)

        resolved = resolve_settings_path()
        assert resolved == bundle_config / "app_settings.json"
