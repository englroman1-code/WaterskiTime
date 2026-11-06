"""Tests für RaceStateManager (Crash-Recovery)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from python.core.race_state_manager import RaceStateManager


class TestRaceStateManager:
    """Tests für den RaceStateManager."""

    def test_exists_returns_false_when_no_file(self, tmp_path: Path) -> None:
        """Keine race_state.json → exists() gibt False zurück."""
        mgr = RaceStateManager(tmp_path)
        assert mgr.exists() is False

    def test_exists_returns_true_when_file_present(self, tmp_path: Path) -> None:
        """Vorhandene race_state.json → exists() gibt True zurück."""
        (tmp_path / "race_state.json").write_text("{}")
        mgr = RaceStateManager(tmp_path)
        assert mgr.exists() is True

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """save() erzeugt race_state.json mit korrektem Inhalt."""
        mgr = RaceStateManager(tmp_path)
        state = {"race_number": 1, "phase": "ACTIVE", "boats": {}}
        assert mgr.save(state) is True

        assert mgr.exists()
        raw = json.loads((tmp_path / "race_state.json").read_text(encoding="utf-8"))
        assert raw["race_number"] == 1
        assert raw["phase"] == "ACTIVE"
        assert "_saved_at" in raw
        assert raw["_version"] == RaceStateManager.SCHEMA_VERSION

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        """save() überschreibt vorhandene Datei (nur aktuellster Stand)."""
        mgr = RaceStateManager(tmp_path)
        mgr.save({"race_number": 1})
        mgr.save({"race_number": 2}, force=True)

        raw = json.loads((tmp_path / "race_state.json").read_text(encoding="utf-8"))
        assert raw["race_number"] == 2

    def test_save_skips_unchanged_state(self, tmp_path: Path) -> None:
        """Unveränderter State wird innerhalb des Heartbeats nicht geschrieben."""
        mgr = RaceStateManager(tmp_path)
        state = {"race_number": 1, "phase": "ACTIVE"}
        assert mgr.save(state) is True
        assert mgr.save(state) is False

    def test_save_force_writes_unchanged_state(self, tmp_path: Path) -> None:
        """force=True schreibt auch einen unveränderten State."""
        mgr = RaceStateManager(tmp_path)
        state = {"race_number": 1, "phase": "ACTIVE"}
        mgr.save(state)
        assert mgr.save(state, force=True) is True

    def test_save_stores_source_fingerprint(self, tmp_path: Path) -> None:
        """Der Fingerprint der Datenquelle wird im State gespeichert."""
        mgr = RaceStateManager(tmp_path)
        mgr.save({"race_number": 1}, source_fingerprint="abc123")

        raw = json.loads((tmp_path / "race_state.json").read_text(encoding="utf-8"))
        assert raw["_source_fingerprint"] == "abc123"

    def test_load_returns_none_when_no_file(self, tmp_path: Path) -> None:
        """Keine Datei → load() gibt None zurück."""
        mgr = RaceStateManager(tmp_path)
        assert mgr.load() is None

    def test_load_returns_none_when_empty(self, tmp_path: Path) -> None:
        """Leere Datei → load() gibt None zurück."""
        (tmp_path / "race_state.json").write_text("")
        mgr = RaceStateManager(tmp_path)
        assert mgr.load() is None

    def test_load_returns_none_when_invalid_json(self, tmp_path: Path) -> None:
        """Ungültiges JSON → load() gibt None zurück."""
        (tmp_path / "race_state.json").write_text("not json {{{")
        mgr = RaceStateManager(tmp_path)
        assert mgr.load() is None

    def test_load_returns_state_dict(self, tmp_path: Path) -> None:
        """Gültige Datei → load() gibt State-Dict zurück."""
        mgr = RaceStateManager(tmp_path)
        original = {"race_number": 1, "phase": "ACTIVE"}
        mgr.save(original)

        loaded = mgr.load()
        assert loaded is not None
        assert loaded["race_number"] == 1
        assert loaded["phase"] == "ACTIVE"

    def test_load_rejects_old_schema(self, tmp_path: Path) -> None:
        """State mit altem Schema (Version 1) wird verworfen."""
        state = {
            "_version": 1,
            "_saved_at": datetime.now().astimezone().isoformat(),
            "race_number": 1,
            "phase": "ACTIVE",
        }
        (tmp_path / "race_state.json").write_text(
            json.dumps(state), encoding="utf-8")
        mgr = RaceStateManager(tmp_path)
        assert mgr.load() is None

    def test_load_rejects_stale_state(self, tmp_path: Path) -> None:
        """State älter als max_age_hours wird verworfen."""
        old = datetime.now().astimezone() - timedelta(hours=13)
        state = {
            "_version": RaceStateManager.SCHEMA_VERSION,
            "_saved_at": old.isoformat(),
            "race_number": 1,
            "phase": "ACTIVE",
        }
        (tmp_path / "race_state.json").write_text(
            json.dumps(state), encoding="utf-8")
        mgr = RaceStateManager(tmp_path, max_age_hours=12)
        assert mgr.load() is None

    def test_load_accepts_fresh_state(self, tmp_path: Path) -> None:
        """Frischer State wird geladen."""
        mgr = RaceStateManager(tmp_path)
        mgr.save({"race_number": 1, "phase": "ACTIVE"})
        assert mgr.load() is not None

    def test_is_compatible_checks_race_number(self, tmp_path: Path) -> None:
        """State mit falscher Rennnummer ist nicht kompatibel."""
        mgr = RaceStateManager(tmp_path)
        state = {"_version": RaceStateManager.SCHEMA_VERSION,
                 "race_number": 1}
        assert mgr.is_compatible(state, race_number=1) is True
        assert mgr.is_compatible(state, race_number=2) is False

    def test_is_compatible_checks_fingerprint(self, tmp_path: Path) -> None:
        """State mit falschem Quell-Fingerprint ist nicht kompatibel."""
        mgr = RaceStateManager(tmp_path)
        state = {"_version": RaceStateManager.SCHEMA_VERSION,
                 "race_number": 1,
                 "_source_fingerprint": "abc"}
        assert mgr.is_compatible(
            state, race_number=1, source_fingerprint="abc") is True
        assert mgr.is_compatible(
            state, race_number=1, source_fingerprint="def") is False

    def test_clear_removes_file(self, tmp_path: Path) -> None:
        """clear() löscht race_state.json."""
        mgr = RaceStateManager(tmp_path)
        mgr.save({"test": True})
        assert mgr.exists()

        mgr.clear()
        assert mgr.exists() is False

    def test_clear_is_safe_when_no_file(self, tmp_path: Path) -> None:
        """clear() ist sicher wenn keine Datei vorhanden ist."""
        mgr = RaceStateManager(tmp_path)
        mgr.clear()  # Sollte keinen Fehler werfen
        assert mgr.exists() is False

    def test_load_returns_dict_with_timestamp(self, tmp_path: Path) -> None:
        """Geladener State enthält _saved_at Zeitstempel."""
        mgr = RaceStateManager(tmp_path)
        mgr.save({"race_number": 1})

        loaded = mgr.load()
        assert loaded is not None
        assert "_saved_at" in loaded

    def test_default_dir_is_runtime_dir(self) -> None:
        """Standard-Verzeichnis ist der Laufzeitordner (Projekt-Root in Dev)."""
        mgr = RaceStateManager()
        assert mgr.path.parent == Path(__file__).resolve().parents[1]
