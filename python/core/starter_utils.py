"""StarterList – zentrale Starter-Verwaltung mit automatischer Key-Eindeutigkeit.

Beide Reader (JsonRaceStore + ExcelReaderV2) geben Starter zurück.
StarterList sorgt beim Hinzufügen automatisch dafür, dass Boot-Keys
innerhalb desselben Rennens eindeutig sind. Bei doppelten Keys bekommt
der zweite Starter den nächsten freien Buchstaben (A–Z) + Log-Warnung.

Gleicher Key in verschiedenen Rennen ist erlaubt.
"""

from __future__ import annotations

from loguru import logger

from python.core.models import Starter


class StarterList:
    """Liste von Startern mit automatischer Boot-Key-Eindeutigkeit pro Rennen."""

    def __init__(self) -> None:
        self._starters: list[Starter] = []
        # Keys die bereits pro Rennen vergeben sind: race_num → {key → "BoatNr (Skier)"}
        self._keys_per_race: dict[int, dict[str, str]] = {}

    def add(self, starter: Starter) -> None:
        """Fügt einen Starter hinzu. Prüft automatisch auf doppelte Keys.

        Args:
            starter: Der hinzuzufügende Starter.
        """
        race_num = starter.race_number
        race_keys = self._keys_per_race.setdefault(race_num, {})
        key = starter.boot_key.upper()

        if key in race_keys:
            new_key = self._next_free_key(race_keys)
            old_key = key
            starter.boot_key = new_key
            race_keys[new_key] = f"{starter.boat_number} ({starter.skier})"
            logger.warning(
                "Doppelter Hotkey '{}' in Rennen {} – Boot {} ({}) "
                "erhält '{}' stattdessen (Belegt von {})",
                old_key, race_num, starter.boat_number, starter.skier,
                new_key, race_keys[old_key])
        else:
            race_keys[key] = f"{starter.boat_number} ({starter.skier})"

        self._starters.append(starter)

    def as_list(self) -> list[Starter]:
        """Gibt die interne Starter-Liste zurück."""
        return self._starters

    def next_free_key_for(self, race_number: int,
                          reserved: set[str] | None = None) -> str:
        """Liefert den nächsten freien Boot-Key (A–Z) für ein Rennen.

        Wird für Starter ohne RundenTaste verwendet (2026-09-02): Sie bleiben
        sichtbar und bekommen automatisch einen Key. Die bereits per `add()`
        registrierten Keys des Rennens werden berücksichtigt, ebenso optional
        `reserved` (z. B. alle Excel-Keys des Rennens), damit ein automatisch
        vergebener Key nie einen Excel-Key überschreibt.

        Args:
            race_number: Rennnummer, für die ein freier Key gesucht wird.
            reserved: Zusätzlich als belegt zu betrachtende Keys (z. B. alle
                Excel-Keys des Rennens). Default: keine.

        Returns:
            Nächster freier Buchstabe (A–Z).
        """
        used = dict(self._keys_per_race.get(race_number, {}))
        if reserved:
            for k in reserved:
                used.setdefault(k, "")
        return self._next_free_key(used)

    @staticmethod
    def _next_free_key(used_keys: dict[str, str]) -> str:
        """Findet den nächsten freien Buchstaben A–Z."""
        for c in range(ord("A"), ord("Z") + 1):
            candidate = chr(c)
            if candidate not in used_keys:
                return candidate
        raise ValueError("Keine freien Boot-Keys mehr verfügbar (A–Z belegt)")

    def __len__(self) -> int:
        return len(self._starters)

    def __iter__(self):
        return iter(self._starters)

    def __repr__(self) -> str:
        return f"StarterList({len(self._starters)} Starter)"


__all__ = ["StarterList"]
