"""JsonRaceStore – Liest Renndaten aus IMPORT.json.

IMPORT.json wird vom VBA-Makro "ExportExpRangesToJSON" erzeugt und enthält
alle _EXP_ Named Ranges als JSON. Dieses Modul konvertiert die JSON-Daten
in die Domänenmodelle (Event, RaceConfig, Starter).

Die JSON-Struktur (vom VBA-Makro erzeugt):
    {
        "info": [ {"CODE": "PAR_EVENT", "Parameter ": "...", "Wert": "..."} ],
        "races": [ {"FLD_RACE": 1, "FLD_RACEDUR": 10, ...} ],
        "starter": [ {"FLD_BOATNR": 173, "FLD_SKIER": "...", ...} ]
    }

Die Felder werden über die CODE/FLD_-Präfixe direkt gematcht – kein Fuzzy
Matching oder Substring-Suche mehr nötig.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from python.core.models import Event, RaceConfig, Starter
from python.core.starter_utils import StarterList


class JsonReadError(Exception):
    """Fehler beim Lesen der IMPORT.json."""
    pass


class JsonRaceStore:
    """Liest IMPORT.json und gibt Domain-Objekte zurück."""

    def __init__(self, json_path: str | Path) -> None:
        """Initialisierung.

        Args:
            json_path: Pfad zur IMPORT.json.
        """
        self._path = Path(json_path)

    def read(self) -> tuple[Event, list[RaceConfig], list[Starter]]:
        """Liest IMPORT.json und gibt Domain-Objekte zurück.

        Returns:
            Tuple von (Event, RaceConfigs, Starter).

        Raises:
            FileNotFoundError: Datei nicht gefunden.
            JsonReadError: Ungültiges JSON oder fehlende Daten.
        """
        if not self._path.exists():
            raise FileNotFoundError(f"IMPORT.json nicht gefunden: {self._path}")

        try:
            # utf-8-sig: VBA schreibt JSON mit UTF-8 BOM – wird automatisch entfernt
            raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError) as exc:
            raise JsonReadError(f"IMPORT.json nicht lesbar: {exc}") from exc

        if not isinstance(raw, dict):
            raise JsonReadError(
                "IMPORT.json: Die Wurzel muss ein JSON-Objekt sein.")

        races_raw = raw.get("races", [])
        starter_raw = raw.get("starter", [])
        if not isinstance(races_raw, list) or not isinstance(starter_raw, list):
            raise JsonReadError(
                "IMPORT.json: 'races' und 'starter' müssen Listen sein.")

        # Altes deutsches Feldformat (vor 2026-09-04) klar ablehnen, statt
        # still 0 Rennen/0 Starter zu laden.
        if self._is_legacy_format(races_raw, starter_raw):
            raise JsonReadError(
                "IMPORT.json verwendet das alte Feldformat (ohne FLD_/CODE). "
                "Bitte die Excel-Datei mit der aktuellen Vorlage neu "
                "exportieren (Makro ExportExpRangesToJSON).")

        event = self._parse_info(raw.get("info", []))
        race_configs = self._parse_races(races_raw)
        starters = self._parse_starters(starter_raw)

        if races_raw and not race_configs:
            raise JsonReadError(
                "IMPORT.json enthält keine gültigen Rennen "
                "(FLD_RACE fehlt oder ist ungültig).")
        if starter_raw and not starters:
            raise JsonReadError(
                "IMPORT.json enthält keine gültigen Starter "
                "(FLD_BOATNR/FLD_SKIER fehlt).")

        logger.info(
            f"IMPORT.json gelesen: {len(race_configs)} Rennen, "
            f"{len(starters)} Starter"
        )
        return event, race_configs, starters

    @staticmethod
    def _is_legacy_format(races_raw: list, starter_raw: list) -> bool:
        """Erkennt das alte deutsche Feldformat ohne FLD_/CODE-Präfixe.

        Args:
            races_raw: Roh-Liste der Rennen aus IMPORT.json.
            starter_raw: Roh-Liste der Starter aus IMPORT.json.

        Returns:
            True wenn mindestens eine nicht-leere Sektion ausschließlich
            alte Feldnamen enthält.
        """
        race_items = [item for item in races_raw if isinstance(item, dict)]
        starter_items = [item for item in starter_raw if isinstance(item, dict)]

        if race_items and not any("FLD_RACE" in item for item in race_items):
            return True
        if starter_items and not any(
                ("FLD_BOATNR" in item or "FLD_SKIER" in item)
                for item in starter_items):
            return True
        return False

    # ------------------------------------------------------------------
    # INFO → Event (CODE-Spalte: PAR_EVENT, PAR_DATE, PAR_ORG)
    # ------------------------------------------------------------------

    def _parse_info(self, info_list: list[dict]) -> Event:
        """Parst die INFO-Sektion anhand der CODE-Spalte."""
        event = Event()
        for item in info_list:
            code = str(item.get("CODE", "") or "").strip()
            val = str(item.get("Wert", "")).strip()

            if not code or not val:
                continue

            if code == "PAR_EVENT":
                event.title = val
            elif code == "PAR_DATE":
                event.date = val
            elif code == "PAR_ORG":
                event.organizer = val

        return event

    # ------------------------------------------------------------------
    # RACES → RaceConfig (FLD_-Präfixe)
    # ------------------------------------------------------------------

    def _parse_races(self, races_list: list[dict]) -> list[RaceConfig]:
        """Parst die RACES-Sektion (Array von Objekten)."""
        configs: list[RaceConfig] = []
        for item in races_list:
            config = self._parse_race_item(item)
            if config and config.race_number > 0:
                configs.append(config)
        return configs

    def _parse_race_item(self, item: dict) -> RaceConfig | None:
        """Parst ein einzelnes Race-Objekt."""
        config = RaceConfig()

        # Race-Nummer
        race_num = item.get("FLD_RACE")
        if race_num is None:
            return None
        try:
            config.race_number = int(float(str(race_num)))
        except (ValueError, TypeError):
            return None

        # Renndauer (Minuten)
        config.race_duration_min = self._get_int(item, "FLD_RACEDUR")

        # Rundenlängen (km → Meter)
        lap1_km = self._get_float(item, "FLD_ROUND1")
        std_km = self._get_float(item, "FLD_ROUND")
        config.lap1_length_m = int(lap1_km * 1000) if lap1_km > 0 else 0
        config.standard_lap_length_m = int(std_km * 1000) if std_km > 0 else 0

        # Startintervall (Sekunden, PFLICHTFELD)
        config.start_interval_s = self._get_int(item, "FLD_STARTINT")

        # Grid Time (Sekunden, PFLICHTFELD)
        config.grid_time_s = self._get_int(item, "FLD_GRIDTIME")

        return config

    # ------------------------------------------------------------------
    # STARTER → Starter (FLD_/FLC_-Präfixe)
    # ------------------------------------------------------------------

    def _parse_starters(self, starters_list: list[dict]) -> list[Starter]:
        """Parst die STARTER-Sektion (Array von Objekten).

        Nutzt StarterList für automatische Key-Eindeutigkeit pro Rennen.
        - Komplett leere Einträge (Platzhalter-Zeilen ohne BoatNr/Skier/Race)
          werden verworfen.
        - Echte Starter ohne FLD_HOTKEY (Boot-Key) bekommen automatisch den
          nächsten freien Buchstaben (A–Z) im Rennen (Feature, 2026-09-02).
        - WICHTIG: Hotkeys aus der Excel haben VORRANG. Die automatische
          Vergabe berücksichtigt ALLE Excel-Keys des Rennens (auch die, die
          erst später in der Liste stehen), damit kein Excel-Key überschrieben
          wird. Dazu werden die Excel-Keys in einem ersten Durchgang gesammelt.
        """
        # 1. Durchgang: alle Starter parsen + Excel-Keys pro Rennen sammeln
        parsed: list[Starter] = []
        excel_keys_per_race: dict[int, set[str]] = {}
        for item in starters_list:
            starter = self._parse_starter_item(item)
            if starter is None:
                continue
            # Komplett leeren Platzhalter-Eintrag verwerfen (keine Daten:
            # weder Bootnummer noch Fahrer). Ein Eintrag mit Race-Nummer aber
            # ohne Boot/Fahrer ist ein leerer Platzhalter in der Excel.
            if not starter.boat_number and not starter.skier:
                continue
            parsed.append(starter)
            if starter.boot_key:
                excel_keys_per_race.setdefault(
                    starter.race_number, set()).add(starter.boot_key.upper())

        # 2. Durchgang: fehlende Keys automatisch vergeben (Excel-Keys haben
        # Vorrang – sie werden nie überschrieben).
        sl = StarterList()
        for starter in parsed:
            if not starter.boot_key:
                starter.boot_key = sl.next_free_key_for(
                    starter.race_number, reserved=excel_keys_per_race.get(
                        starter.race_number, set()))
                logger.info(
                    "Starter ohne RundenTaste: Boot {} ({}) in Rennen {} – "
                    "Key '{}' automatisch vergeben.",
                    starter.boat_number, starter.skier, starter.race_number,
                    starter.boot_key)
            sl.add(starter)
        return sl.as_list()

    def _parse_starter_item(self, item: dict) -> Starter | None:
        """Parst ein einzelnes Starter-Objekt.

        Hinweis (2026-09-02): Fehlt die FLD_HOTKEY (Boot-Key), wird der
        Starter NICHT mehr verworfen – er bleibt sichtbar, bekommt aber einen
        leeren Key. Die Validierung (DataValidator) meldet dann klar
        "Boot ohne Key", damit der Kunde die Excel korrigieren kann.
        """
        starter = Starter()

        # Boot-Key (FLD_HOTKEY) – optional: fehlt er, bleibt der Key leer
        key_raw = item.get("FLD_HOTKEY")
        starter.boot_key = str(key_raw).strip().upper()[:1] if key_raw else ""

        # Boot-Nummer
        boat_nr = item.get("FLD_BOATNR")
        starter.boat_number = str(boat_nr).strip() if boat_nr else ""

        # Fahrer
        starter.skier = self._get_str(item, "FLD_SKIER")
        starter.team = self._get_str(item, "FLD_TEAM")
        starter.driver = self._get_str(item, "FLD_DRIVER")
        starter.observer = self._get_str(item, "FLD_OBSERVER")
        starter.club = self._get_str(item, "FLC_CLUB")
        starter.federation = self._get_str(item, "FLD_FED")
        starter.klasse = self._get_str(item, "FLD_CLASS")

        # Race-Nummer
        race_num = item.get("FLD_RACE")
        if race_num is not None:
            try:
                starter.race_number = int(float(str(race_num)))
            except (ValueError, TypeError):
                starter.race_number = 0

        # Startreihe
        startreihe = item.get("FLD_LINE")
        if startreihe is not None:
            try:
                starter.startreihe = int(float(str(startreihe)))
            except (ValueError, TypeError):
                starter.startreihe = 0

        return starter

    # ------------------------------------------------------------------
    # Helper: direkte Typ-Konvertierung
    # ------------------------------------------------------------------

    @staticmethod
    def _get_int(item: dict, key: str, default: int = 0) -> int:
        """Liest einen Integer-Wert direkt aus einem Dict."""
        val = item.get(key)
        if val is None:
            return default
        try:
            return int(float(str(val)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _get_float(item: dict, key: str, default: float = 0.0) -> float:
        """Liest einen Float-Wert direkt aus einem Dict."""
        val = item.get(key)
        if val is None:
            return default
        try:
            return float(str(val))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _get_str(item: dict, key: str, default: str = "") -> str:
        """Liest einen String-Wert direkt aus einem Dict."""
        val = item.get(key)
        if val is None:
            return default
        return str(val).strip()


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------

def read_race_json(json_path: str | Path) -> tuple[Event, list[RaceConfig], list[Starter]]:
    """Liest Renndaten aus einer IMPORT.json.

    Args:
        json_path: Pfad zur IMPORT.json.

    Returns:
        Tuple von (Event, RaceConfigs, Starter).
    """
    store = JsonRaceStore(json_path)
    return store.read()
