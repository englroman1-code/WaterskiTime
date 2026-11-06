"""Tests für den DataValidator (Pflichtenheft §4).

Prüft, dass validate_scenario() alle Pflichtfelder vollständig
und korrekt validates und bei Fehlern klare Meldungen zurückgibt.
"""

from __future__ import annotations

import pytest

from python.core.data_validator import validate_scenario
from tests.demo_data import create_demo_scenario


class TestValidateScenario:
    """Tests für validate_scenario mit Demo-Szenario."""

    def test_valid_scenario_has_no_errors(self) -> None:
        """Das Demo-Szenario ist valide (0 Fehler)."""
        scenario = create_demo_scenario()
        errors = validate_scenario(scenario)
        assert errors == []

    def test_empty_event_title_fails(self) -> None:
        """Ohne Event-Titel → Fehler."""
        scenario = create_demo_scenario()
        scenario.event.title = ""
        errors = validate_scenario(scenario)
        assert any("Event-Titel" in e for e in errors)

    def test_whitespace_event_title_fails(self) -> None:
        """Nur Leerzeichen als Titel → Fehler."""
        scenario = create_demo_scenario()
        scenario.event.title = "   "
        errors = validate_scenario(scenario)
        assert any("Event-Titel" in e for e in errors)

    def test_no_race_configs_fails(self) -> None:
        """Keine Rennkonfiguration → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs = []
        errors = validate_scenario(scenario)
        assert any("Rennkonfiguration" in e for e in errors)

    def test_zero_duration_fails(self) -> None:
        """Renndauer 0 → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs[0].race_duration_min = 0
        errors = validate_scenario(scenario)
        assert any("Renndauer" in e for e in errors)

    def test_negative_duration_fails(self) -> None:
        """Negative Renndauer → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs[0].race_duration_min = -5
        errors = validate_scenario(scenario)
        assert any("Renndauer" in e for e in errors)

    def test_zero_start_interval_fails(self) -> None:
        """Startintervall (Vorlaufzeit) 0 → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs[0].start_interval_s = 0
        errors = validate_scenario(scenario)
        assert any("Startintervall" in e for e in errors)

    def test_zero_grid_time_fails(self) -> None:
        """Grid Time 0 → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs[0].grid_time_s = 0
        errors = validate_scenario(scenario)
        assert any("Grid Time" in e for e in errors)

    def test_zero_lap1_length_fails(self) -> None:
        """Länge Runde 1 = 0 → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs[0].lap1_length_m = 0
        errors = validate_scenario(scenario)
        assert any("Länge Runde 1" in e for e in errors)

    def test_zero_standard_lap_length_fails(self) -> None:
        """Länge Standard-Runde = 0 → Fehler."""
        scenario = create_demo_scenario()
        scenario.race_configs[0].standard_lap_length_m = 0
        errors = validate_scenario(scenario)
        assert any("Standard-Runde" in e for e in errors)

    def test_no_starters_fails(self) -> None:
        """Keine Starter → Fehler."""
        scenario = create_demo_scenario()
        scenario.starters = []
        errors = validate_scenario(scenario)
        assert any("Starter" in e for e in errors)

    def test_starter_without_boot_key_ok(self) -> None:
        """Starter ohne Boot-Key → KEIN Fehler (automatische Vergabe, 2026-09-02).

        Starter ohne RundenTaste bekommen beim Laden automatisch einen
        Platzhalter-Key (A–Z). Ein leerer Key ist daher kein Validierungsfehler
        mehr – die automatische Vergabe löst das Problem.
        """
        scenario = create_demo_scenario()
        scenario.starters[0].boot_key = ""
        errors = validate_scenario(scenario)
        assert not any("Boot ohne Key" in e for e in errors)

    def test_duplicate_boot_keys_fails(self) -> None:
        """Doppelte Boot-Keys im SELBEN Rennen → Fehler."""
        scenario = create_demo_scenario()
        scenario.starters[0].boot_key = "A"
        scenario.starters[1].boot_key = "A"
        # Beide müssen im selben Rennen sein
        scenario.starters[1].race_number = scenario.starters[0].race_number
        errors = validate_scenario(scenario)
        assert any("Doppelter Boot-Key" in e for e in errors)

    def test_same_key_different_races_ok(self) -> None:
        """Gleicher Boot-Key in VERSCHIEDENEN Rennen → kein Fehler."""
        scenario = create_demo_scenario()
        # Starters[0] (Rennen 2) und starters[2] (Rennen 1) → gleicher Key
        scenario.starters[0].boot_key = "X"
        scenario.starters[2].boot_key = "X"
        errors = validate_scenario(scenario)
        assert not any("Doppelter Boot-Key" in e for e in errors)

    def test_starter_without_class_fails(self) -> None:
        """Starter ohne Klasse → Fehler."""
        scenario = create_demo_scenario()
        scenario.starters[0].klasse = ""
        errors = validate_scenario(scenario)
        assert any("Keine Klasse" in e for e in errors)

    def test_invalid_boot_key_fails(self) -> None:
        """Ungültiger Boot-Key (Mehrzahl) → Fehler."""
        scenario = create_demo_scenario()
        scenario.starters[0].boot_key = "AB"
        errors = validate_scenario(scenario)
        assert any("Ungültiger Boot-Key" in e for e in errors)

    def test_race_without_starters_fails(self) -> None:
        """Rennen ohne zugeordnete Starter → Fehler."""
        scenario = create_demo_scenario()
        # Alle Starter auf Rennen 99 setzen (kein Rennen hat Starter)
        for s in scenario.starters:
            s.race_number = 99
        errors = validate_scenario(scenario)
        assert any("Keine Starter zugeordnet" in e for e in errors)

    def test_multiple_errors_collected(self) -> None:
        """Mehrere Fehler werden gesammelt (nicht beim ersten abgebrochen)."""
        scenario = create_demo_scenario()
        scenario.event.title = ""
        scenario.race_configs[0].race_duration_min = 0
        scenario.starters[0].klasse = ""
        errors = validate_scenario(scenario)
        assert len(errors) >= 3

    def test_startreihe_zero_fails(self) -> None:
        """Startreihe 0 → Fehler (Boot würde nie starten)."""
        scenario = create_demo_scenario()
        scenario.starters[0].startreihe = 0
        errors = validate_scenario(scenario)
        assert any("Startreihe muss > 0" in e for e in errors)

    def test_startreihe_negative_fails(self) -> None:
        """Negative Startreihe → Fehler."""
        scenario = create_demo_scenario()
        scenario.starters[0].startreihe = -1
        errors = validate_scenario(scenario)
        assert any("Startreihe muss > 0" in e for e in errors)
