"""Tests für JsonRaceStore (IMPORT.json lesen)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.excel.json_race_store import JsonRaceStore, JsonReadError, read_race_json


# ---------------------------------------------------------------------------
# Test fixtures – neue FLD_/CODE-Feldnamen
# ---------------------------------------------------------------------------

SAMPLE_EXPORT = {
    "info": [
        {"CODE": "PAR_EVENT", "Parameter ": "Veranstaltung : ", "Wert": "Testrennen"},
        {"CODE": "PAR_DATE", "Parameter ": "Datum : ", "Wert": "2026-05-20"},
        {"CODE": "PAR_ORG", "Parameter ": "Organisator : ", "Wert": "Verein A"},
    ],
    "races": [
        {
            "FLD_RACE": 1,
            "FLD_STARTINT": 3,
            "FLD_RACEDUR": 10,
            "FLD_STARTTIME": None,
            "FLD_ROUND": 3.5,
            "FLD_ROUND1": 2,
            "FLD_GRIDTIME": 30,
        },
        {
            "FLD_RACE": 2,
            "FLD_STARTINT": 5,
            "FLD_RACEDUR": 12,
            "FLD_STARTTIME": None,
            "FLD_ROUND": 3.5,
            "FLD_ROUND1": 2,
            "FLD_GRIDTIME": 30,
        },
    ],
    "starter": [
        {
            "FLD_BOATNR": 173,
            "FLD_CLASS": "JUN",
            "FLD_TEAM": "Untouchable",
            "FLD_SKIER": "Pfenningbauer, Paul",
            "FLD_DRIVER": "Schmutz Günter",
            "FLD_OBSERVER": "Was i Net",
            "FLC_CLUB": "WSC Red Shark",
            "FLD_FED": None,
            "FLD_HOTKEY": "q",
            "FLD_RACE": 1,
            "FLD_LINE": 1,
        },
        {
            "FLD_BOATNR": 65,
            "FLD_CLASS": "MEN",
            "FLD_TEAM": None,
            "FLD_SKIER": "Conti, Devid",
            "FLD_DRIVER": None,
            "FLD_OBSERVER": None,
            "FLC_CLUB": "Italien",
            "FLD_FED": None,
            "FLD_HOTKEY": "a",
            "FLD_RACE": 1,
            "FLD_LINE": 2,
        },
        {
            "FLD_BOATNR": 173,
            "FLD_CLASS": "F1",
            "FLD_TEAM": None,
            "FLD_SKIER": "Pfenningbauer, Paul",
            "FLD_DRIVER": None,
            "FLD_OBSERVER": None,
            "FLC_CLUB": "WSC Tulln",
            "FLD_FED": None,
            "FLD_HOTKEY": "q",
            "FLD_RACE": 2,
            "FLD_LINE": 1,
        },
    ],
}


@pytest.fixture
def export_json(tmp_path: Path) -> Path:
    """Erzeugt eine Test-IMPORT.json."""
    path = tmp_path / "IMPORT.json"
    path.write_text(json.dumps(SAMPLE_EXPORT, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestJsonRaceStore:
    """Tests für den JsonRaceStore."""

    def test_read_success(self, export_json: Path) -> None:
        """IMPORT.json wird erfolgreich gelesen."""
        store = JsonRaceStore(export_json)
        event, configs, starters = store.read()
        assert event.title == "Testrennen"
        assert len(configs) == 2
        assert len(starters) == 3

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Fehlende Datei → FileNotFoundError."""
        store = JsonRaceStore(tmp_path / "missing.json")
        with pytest.raises(FileNotFoundError):
            store.read()

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Ungültiges JSON → JsonReadError."""
        path = tmp_path / "bad.json"
        path.write_text("not json {{{", encoding="utf-8")
        store = JsonRaceStore(path)
        with pytest.raises(JsonReadError):
            store.read()

    def test_event_metadata(self, export_json: Path) -> None:
        """Event-Metadata werden korrekt geparsed (via CODE-Spalte)."""
        event = JsonRaceStore(export_json).read()[0]
        assert event.title == "Testrennen"
        assert event.date == "2026-05-20"
        assert event.organizer == "Verein A"

    def test_race_configs(self, export_json: Path) -> None:
        """RaceConfigs werden korrekt geparsed."""
        _, configs, _ = JsonRaceStore(export_json).read()
        assert configs[0].race_number == 1
        assert configs[0].race_duration_min == 10
        assert configs[0].lap1_length_m == 2000  # 2 km → 2000 m
        assert configs[0].standard_lap_length_m == 3500  # 3.5 km → 3500 m
        assert configs[0].start_interval_s == 3
        assert configs[0].grid_time_s == 30
        assert configs[1].race_number == 2
        assert configs[1].race_duration_min == 12

    def test_starter_fields(self, export_json: Path) -> None:
        """Starter-Felder werden korrekt geparsed."""
        _, _, starters = JsonRaceStore(export_json).read()
        paul = starters[0]
        assert paul.boot_key == "Q"
        assert paul.boat_number == "173"
        assert paul.skier == "Pfenningbauer, Paul"
        assert paul.klasse == "JUN"
        assert paul.race_number == 1
        assert paul.startreihe == 1

    def test_starter_with_team(self, export_json: Path) -> None:
        """Starter mit Team-Name."""
        _, _, starters = JsonRaceStore(export_json).read()
        paul = starters[0]
        assert paul.team == "Untouchable"

    def test_starter_without_team(self, export_json: Path) -> None:
        """Starter ohne Team-Name."""
        _, _, starters = JsonRaceStore(export_json).read()
        devid = starters[1]
        assert devid.team == ""
        assert devid.klasse == "MEN"
        assert devid.startreihe == 2

    def test_starter_race_distribution(self, export_json: Path) -> None:
        """Starter auf Rennen verteilt."""
        _, _, starters = JsonRaceStore(export_json).read()
        race1 = [s for s in starters if s.race_number == 1]
        race2 = [s for s in starters if s.race_number == 2]
        assert len(race1) == 2
        assert len(race2) == 1

    def test_direct_key_matching(self, export_json: Path) -> None:
        """Direkte Key-Matching funktioniert."""
        _, configs, _ = JsonRaceStore(export_json).read()
        # FLD_RACEDUR → race_duration_min
        assert configs[0].race_duration_min == 10
        # FLD_ROUND → standard_lap_length_m
        assert configs[0].standard_lap_length_m == 3500
        # FLD_STARTINT → start_interval_s
        assert configs[0].start_interval_s == 3
        # FLD_GRIDTIME → grid_time_s
        assert configs[0].grid_time_s == 30

    def test_empty_starter_filtered(self, tmp_path: Path) -> None:
        """Leere Starter (ohne Boot/Fahrer) werden gefiltert."""
        data = {
            "info": [],
            "races": [{"FLD_RACE": 1, "FLD_RACEDUR": 10}],
            "starter": [
                {"FLD_HOTKEY": "a", "FLD_BOATNR": 1, "FLD_RACE": 1, "FLD_LINE": 1},
                {"FLD_HOTKEY": None, "FLD_BOATNR": None, "FLD_RACE": None, "FLD_LINE": None},  # leer
                {"FLD_HOTKEY": "b", "FLD_BOATNR": 2, "FLD_RACE": 1, "FLD_LINE": 1},
            ],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        _, _, starters = JsonRaceStore(path).read()
        assert len(starters) == 2

    def test_convenience_function(self, export_json: Path) -> None:
        """read_race_json() Funktion funktioniert."""
        event, configs, starters = read_race_json(export_json)
        assert event.title == "Testrennen"
        assert len(configs) == 2
        assert len(starters) == 3

    def test_info_skips_empty_code(self, tmp_path: Path) -> None:
        """Zeilen mit leerem CODE werden übersprungen."""
        data = {
            "info": [
                {"CODE": "PAR_EVENT", "Parameter ": "Veranstaltung", "Wert": "Test"},
                {"CODE": None, "Parameter ": None, "Wert": None},
                {"CODE": "PAR_DATE", "Parameter ": "Datum", "Wert": "2026-01-01"},
            ],
            "races": [],
            "starter": [],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        event, configs, starters = JsonRaceStore(path).read()
        assert event.title == "Test"
        assert event.date == "2026-01-01"
        assert len(configs) == 0
        assert len(starters) == 0


# ---------------------------------------------------------------------------
# Tests für doppelte Boot-Keys
# ---------------------------------------------------------------------------

class TestDuplicateKeyResolution:
    """Tests für die Auflösung doppelter Boot-Keys pro Rennen."""

    DUPLICATE_KEY_DATA = {
        "info": [{"CODE": "PAR_EVENT", "Parameter ": "Veranstaltung", "Wert": "Test"}],
        "races": [{"FLD_RACE": 1, "FLD_RACEDUR": 10}],
        "starter": [
            # Beide haben Key "A" im selben Rennen → zweiter wird umgesetzt
            {"FLD_BOATNR": 100, "FLD_CLASS": "MEN", "FLD_SKIER": "Erster",
             "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
            {"FLD_BOATNR": 200, "FLD_CLASS": "MEN", "FLD_SKIER": "Zweiter",
             "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
        ],
    }

    def test_duplicate_key_resolved(self, tmp_path: Path) -> None:
        """Zweiter Starter mit gleichem Key bekommt nächsten freien Buchstaben."""
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(self.DUPLICATE_KEY_DATA), encoding="utf-8")
        _, _, starters = JsonRaceStore(path).read()
        assert len(starters) == 2
        assert starters[0].boot_key == "A"  # erster behält Key
        assert starters[1].boot_key == "B"  # zweiter bekommt nächsten freien

    def test_same_key_different_races_ok(self, tmp_path: Path) -> None:
        """Gleicher Key in verschiedenen Rennen ist erlaubt."""
        data = {
            "info": [],
            "races": [
                {"FLD_RACE": 1, "FLD_RACEDUR": 10},
                {"FLD_RACE": 2, "FLD_RACEDUR": 10},
            ],
            "starter": [
                {"FLD_BOATNR": 100, "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
                {"FLD_BOATNR": 200, "FLD_HOTKEY": "a", "FLD_RACE": 2, "FLD_LINE": 1},
            ],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        _, _, starters = JsonRaceStore(path).read()
        assert starters[0].boot_key == "A"
        assert starters[1].boot_key == "A"  # gleicher Key, anderes Rennen → ok

    def test_multiple_duplicates_resolved(self, tmp_path: Path) -> None:
        """Drei Starter mit gleichem Key → A, B, C."""
        data = {
            "info": [],
            "races": [{"FLD_RACE": 1, "FLD_RACEDUR": 10}],
            "starter": [
                {"FLD_BOATNR": 100, "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
                {"FLD_BOATNR": 200, "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
                {"FLD_BOATNR": 300, "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
            ],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        _, _, starters = JsonRaceStore(path).read()
        assert starters[0].boot_key == "A"
        assert starters[1].boot_key == "B"
        assert starters[2].boot_key == "C"

    def test_no_duplicates_unchanged(self, tmp_path: Path) -> None:
        """Ohne doppelte Keys bleiben alle Keys unverändert."""
        data = {
            "info": [],
            "races": [{"FLD_RACE": 1, "FLD_RACEDUR": 10}],
            "starter": [
                {"FLD_BOATNR": 100, "FLD_HOTKEY": "a", "FLD_RACE": 1, "FLD_LINE": 1},
                {"FLD_BOATNR": 200, "FLD_HOTKEY": "b", "FLD_RACE": 1, "FLD_LINE": 1},
                {"FLD_BOATNR": 300, "FLD_HOTKEY": "c", "FLD_RACE": 1, "FLD_LINE": 1},
            ],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        _, _, starters = JsonRaceStore(path).read()
        assert [s.boot_key for s in starters] == ["A", "B", "C"]

    def test_excel_key_has_priority_over_auto(self, tmp_path: Path) -> None:
        """Excel-Hotkey hat Vorrang vor automatischer Vergabe (2026-09-02).

        Regression: Ein Starter ohne Key, der VOR einem Excel-Starter mit
        Key 'A' in der Liste steht, darf 'A' NICHT belegen – sonst würde der
        Excel-Key überschrieben. Die automatische Vergabe muss alle
        Excel-Keys des Rennens kennen (auch die späteren).
        """
        data = {
            "info": [],
            "races": [{"FLD_RACE": 1, "FLD_RACEDUR": 10}],
            "starter": [
                # Ohne Key – steht VOR dem Excel-Starter mit 'A'
                {"FLD_BOATNR": 100, "FLD_SKIER": "Ohne Key", "FLD_HOTKEY": None,
                 "FLD_RACE": 1, "FLD_LINE": 1},
                # Excel-Key 'A' – muss Vorrang behalten
                {"FLD_BOATNR": 200, "FLD_SKIER": "Mit Key A", "FLD_HOTKEY": "a",
                 "FLD_RACE": 1, "FLD_LINE": 1},
            ],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        _, _, starters = JsonRaceStore(path).read()
        assert len(starters) == 2
        # Excel-Key 'A' bleibt beim Excel-Starter
        assert starters[1].boot_key == "A"
        # Automatischer Starter bekommt den nächsten freien Key (nicht 'A')
        assert starters[0].boot_key == "B"


class TestLegacyFormatRejection:
    """Altes deutsches IMPORT.json-Format wird klar abgelehnt."""

    def test_legacy_races_rejected(self, tmp_path: Path) -> None:
        """Rennen ohne FLD_RACE → JsonReadError (kein stilles 0-Rennen)."""
        data = {
            "info": [],
            "races": [{"Race": 1, "Renndauer\n[min]": 10}],
            "starter": [{"FLD_BOATNR": 1, "FLD_RACE": 1}],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(JsonReadError, match="alte Feldformat"):
            JsonRaceStore(path).read()

    def test_legacy_starter_rejected(self, tmp_path: Path) -> None:
        """Starter ohne FLD_BOATNR/FLD_SKIER → JsonReadError."""
        data = {
            "info": [],
            "races": [{"FLD_RACE": 1, "FLD_RACEDUR": 10}],
            "starter": [{"BoatNr": 1, "Skier ": "Test"}],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(JsonReadError, match="alte Feldformat"):
            JsonRaceStore(path).read()

    def test_non_object_root_rejected(self, tmp_path: Path) -> None:
        """JSON-Wurzel ist kein Objekt → JsonReadError."""
        path = tmp_path / "IMPORT.json"
        path.write_text("[]", encoding="utf-8")
        with pytest.raises(JsonReadError, match="Wurzel"):
            JsonRaceStore(path).read()

    def test_races_without_valid_entries_rejected(self, tmp_path: Path) -> None:
        """Nicht-leere RACES ohne gültige FLD_RACE → JsonReadError."""
        data = {
            "info": [],
            "races": [{"FLD_RACE": None}],
            "starter": [{"FLD_BOATNR": 1, "FLD_RACE": 1}],
        }
        path = tmp_path / "IMPORT.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(JsonReadError, match="keine gültigen Rennen"):
            JsonRaceStore(path).read()
