"""DataValidator – Prüfung aller Pflichtfelder vor Rennfreigabe (§4).

Das Pflichtenheft §4 fordert: „Erst nach erfolgreicher Prüfung aller
erforderlichen Daten darf ein Rennen zur Durchführung freigegeben werden."

Dieses Modul validiert die geladenen Renndaten (RaceData) auf Vollständigkeit
und Korrektheit und gibt eine Liste von Fehlermeldungen zurück (leer = alles OK).
"""

from __future__ import annotations

import re
from python.core.race_data import RaceData


def validate_scenario(scenario: RaceData,
                      race_number: int | None = None) -> list[str]:
    """Validiert die Renndaten auf Vollständigkeit (Pflichtenheft §4).

    Prüft:
        - Event: Titel vorhanden
        - Mindestens ein RaceConfig mit Renndauer > 0
        - Mindestens ein Starter pro (geprüftem) Rennen
        - Keine doppelten Boot-Keys (innerhalb desselben Rennens)
        - Alle Boot-Keys gültig (A-Z, einzelner Buchstabe)
        - Alle Starter haben eine Klasse

    Hinweis (2026-09-02): Starter ohne RundenTaste (Boot-Key) sind KEIN
    Validierungsfehler mehr – sie bekommen beim Laden automatisch einen
    Platzhalter-Key (A–Z) zugewiesen (JsonRaceStore).

    Args:
        scenario: Das zu prüfende Szenario.
        race_number: Wenn angegeben, werden nur Daten für dieses Rennen
                     geprüft (Starter + RaceConfig). None = alles prüfen.

    Returns:
        Liste von Fehlertexten (leer = alles OK).
    """
    errors: list[str] = []

    # --- Event-Validierung (immer) ---
    if not scenario.event.title or not scenario.event.title.strip():
        errors.append("Event-Titel fehlt")

    # --- RaceConfig-Validierung ---
    if not scenario.race_configs:
        errors.append("Keine Rennkonfiguration vorhanden")
    else:
        configs = scenario.race_configs
        if race_number is not None:
            configs = [c for c in configs if c.race_number == race_number]
        for config in configs:
            prefix = f"Rennen {config.race_number}: "
            if config.race_duration_min <= 0:
                errors.append(f"{prefix}Renndauer muss > 0 sein "
                              f"(aktuell: {config.race_duration_min} min)")
            if config.start_interval_s <= 0:
                errors.append(f"{prefix}Startintervall (Vorlaufzeit) muss > 0 sein "
                              f"(aktuell: {config.start_interval_s} s)")
            if config.grid_time_s <= 0:
                errors.append(f"{prefix}Grid Time (Zeit zwischen Startreihen) "
                              f"muss > 0 sein (aktuell: {config.grid_time_s} s)")
            if config.lap1_length_m <= 0:
                errors.append(f"{prefix}Länge Runde 1 muss > 0 sein "
                              f"(aktuell: {config.lap1_length_m} m)")
            if config.standard_lap_length_m <= 0:
                errors.append(f"{prefix}Länge Standard-Runde muss > 0 sein "
                              f"(aktuell: {config.standard_lap_length_m} m)")

    # --- Starter-Validierung ---
    starters = scenario.starters
    if race_number is not None:
        starters = [s for s in starters if s.race_number == race_number]

    if not starters:
        errors.append("Keine Starter vorhanden" if race_number is None
                       else f"Rennen {race_number}: Keine Starter")
    else:
        # Boot-Keys nur INNERHALB desselben Rennens eindeutig
        # (bei race_number=None: pro Rennen getrennt; bei race_number: nur ein Rennen)
        keys_per_race: dict[int, dict[str, str]] = {}
        key_pattern = re.compile(r'^[A-Z]$')

        for starter in starters:
            key = starter.boot_key.strip().upper() if starter.boot_key else ""
            if not key:
                # Kein Fehler mehr: Starter ohne RundenTaste bekommen automatisch
                # einen Platzhalter-Key (A–Z) beim Laden (JsonRaceStore,
                # Entscheidung 2026-09-02). Ein leerer Key hier ist nur möglich,
                # wenn Starter direkt (ohne Reader) erzeugt wurden.
                continue
            if not key_pattern.match(key):
                errors.append(
                    f"Ungültiger Boot-Key '{key}' für "
                    f"Boot {starter.boat_number}")
            else:
                race_keys = keys_per_race.setdefault(starter.race_number, {})
                if key in race_keys:
                    errors.append(
                        f"Doppelter Boot-Key '{key}' in Rennen "
                        f"{starter.race_number}: "
                        f"Boot {starter.boat_number} ({starter.skier}) "
                        f"kollidiert mit {race_keys[key]}")
                else:
                    race_keys[key] = (f"Boot {starter.boat_number} "
                                      f"({starter.skier})")

            if not starter.klasse or not starter.klasse.strip():
                errors.append(
                    f"Boot {starter.boat_number} ({starter.skier}): "
                    f"Keine Klasse zugewiesen")

            if starter.startreihe <= 0:
                errors.append(
                    f"Boot {starter.boat_number} ({starter.skier}): "
                    f"Startreihe muss > 0 sein "
                    f"(aktuell: {starter.startreihe})")

    # Prüfe ob pro (geprüftem) Rennen mindestens ein Starter existiert
    if race_number is None and scenario.race_configs:
        race_numbers = {c.race_number for c in scenario.race_configs}
        starters_per_race = {s.race_number for s in scenario.starters}
        for rn in race_numbers:
            if rn not in starters_per_race:
                errors.append(
                    f"Rennen {rn}: Keine Starter zugeordnet")

    return errors


__all__ = ["validate_scenario"]
