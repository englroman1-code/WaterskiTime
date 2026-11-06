"""RaceStateManager – Crash-Recovery für laufende Rennen.

Speichert den aktuellen RaceEngine-Zustand als JSON (race_state.json).
Bei App-Start wird geprüft, ob ein geretteter Zustand vorhanden ist –
dieser wird SOFORT wiederhergestellt (keine Nachfrage, da Zeit kritisch!).

Sicherheitsregeln (2026-11-06):
    - Der State enthält `_saved_at` (Zeitpunkt der letzten Speicherung),
      `_version` (Schema-Version) und `_source_fingerprint` (Fingerabdruck
      der geladenen Datenquelle).
    - Beim Laden werden veraltete States (älter als `max_age_hours`) und
      States mit falscher Rennnummer bzw. falscher Datenquelle verworfen.
    - Geschrieben wird atomar (Temp-Datei + os.replace), damit ein Absturz
      während des Schreibens keine halbe JSON hinterlässt.
    - Unveränderte States werden nicht bei jedem GUI-Tick geschrieben:
      gleicher Inhalt wird nur alle `HEARTBEAT_SECONDS` erneut gespeichert
      (frische Zeitbasis für die Altersprüfung, aber wenig Platten-I/O).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from python.config.app_config import get_runtime_dir


class RaceStateManager:
    """Verwaltet race_state.json für Crash-Recovery.

    Die Datei enthält den vollständigen Zustand der RaceEngine:
    Rennnummer, Phase, Zeitstempel, Boot-Zustände, Events und Klassen.
    """

    STATE_FILENAME = "race_state.json"
    SCHEMA_VERSION = 2
    DEFAULT_MAX_AGE_HOURS = 12.0
    HEARTBEAT_SECONDS = 30.0

    def __init__(self, state_dir: str | Path | None = None,
                 max_age_hours: float = DEFAULT_MAX_AGE_HOURS) -> None:
        """Initialisierung.

        Args:
            state_dir: Verzeichnis für race_state.json. None = Laufzeitordner
                       (neben der .exe bzw. Projekt-Root in der Entwicklung).
            max_age_hours: Maximale Lebensdauer eines States in Stunden.
        """
        self._dir = Path(state_dir) if state_dir else get_runtime_dir()
        self._path = self._dir / self.STATE_FILENAME
        self._max_age = timedelta(hours=max_age_hours)
        self._last_payload_hash: str | None = None
        self._last_save_monotonic: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Pfad zur race_state.json."""
        return self._path

    def exists(self) -> bool:
        """Prüft ob race_state.json vorhanden ist.

        Returns:
            True wenn die Datei existiert.
        """
        return self._path.exists()

    def save(self, state: dict[str, Any], *,
             source_fingerprint: str | None = None,
             force: bool = False) -> bool:
        """Speichert den Engine-Zustand in race_state.json.

        Überschreibt die Datei atomar. Unveränderte Zustände werden nur
        alle `HEARTBEAT_SECONDS` erneut geschrieben (frische `_saved_at`-
        Zeit, aber kein I/O bei jedem GUI-Tick).

        Args:
            state: Serialisierter Zustand der RaceEngine.
            source_fingerprint: Fingerabdruck der geladenen Datenquelle
                (JSON/Excel). Wird im State gespeichert und beim Laden
                geprüft.
            force: True = immer schreiben (z. B. beim Beenden/Reset).

        Returns:
            True wenn geschrieben wurde, False wenn der Aufruf gedrosselt
            wurde oder ein Schreibfehler auftrat.
        """
        payload = dict(state)
        payload["_version"] = self.SCHEMA_VERSION
        if source_fingerprint is not None:
            payload["_source_fingerprint"] = source_fingerprint

        # Hash ohne den veränderlichen Zeitstempel: gleicher Inhalt → kein I/O
        hash_payload = {k: v for k, v in payload.items() if k != "_saved_at"}
        digest = hashlib.sha256(
            json.dumps(hash_payload, sort_keys=True, ensure_ascii=False,
                       default=str).encode("utf-8")
        ).hexdigest()

        now_mono = time.monotonic()
        if (not force
                and digest == self._last_payload_hash
                and (now_mono - self._last_save_monotonic)
                < self.HEARTBEAT_SECONDS):
            return False

        payload["_saved_at"] = datetime.now().astimezone().isoformat(
            timespec="seconds")

        if not self._atomic_write(payload):
            return False

        self._last_payload_hash = digest
        self._last_save_monotonic = now_mono
        logger.debug("Race state gespeichert: {}", self._path)
        return True

    def load(self) -> dict[str, Any] | None:
        """Lädt den geretteten Zustand aus race_state.json.

        Verwirft States, die:
            - nicht vorhanden/leer/kein gültiges JSON sind,
            - ein anderes Schema als `SCHEMA_VERSION` haben,
            - keinen `_saved_at`-Zeitstempel haben,
            - älter als `max_age_hours` sind.

        Returns:
            Dict mit dem geretteten Zustand, oder None.
        """
        if not self._path.exists():
            return None

        try:
            raw = self._path.read_text(encoding="utf-8")
            if not raw.strip():
                return None
            state = json.loads(raw)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Race state konnte nicht gelesen werden: {}", exc)
            return None

        if not isinstance(state, dict):
            logger.warning("Race state ist kein JSON-Objekt – verworfen")
            return None

        version = state.get("_version")
        if version != self.SCHEMA_VERSION:
            logger.warning(
                "Race state: veraltetes Schema (Version {} statt {}) – "
                "verworfen", version, self.SCHEMA_VERSION)
            return None

        saved_at = self._parse_saved_at(state.get("_saved_at"))
        if saved_at is None:
            logger.warning("Race state ohne gültigen _saved_at – verworfen")
            return None

        age = datetime.now().astimezone() - saved_at
        if age > self._max_age:
            logger.warning(
                "Race state ist zu alt ({} > {}) – verworfen",
                self._format_age(age), self._format_age(self._max_age))
            return None

        logger.info("Race state geladen: {} (gespeichert: {})",
                    self._path, state.get("_saved_at", "?"))
        return state

    def is_compatible(self, state: dict[str, Any], *,
                      race_number: int | None = None,
                      source_fingerprint: str | None = None) -> bool:
        """Prüft, ob ein geladener State zur aktuellen Datenquelle passt.

        Args:
            state: State aus `load()`.
            race_number: Erwartete Rennnummer (None = nicht prüfen).
            source_fingerprint: Erwarteter Fingerabdruck der Datenquelle
                (None = nicht prüfen).

        Returns:
            True wenn der State verwendet werden darf.
        """
        if state.get("_version") != self.SCHEMA_VERSION:
            return False

        if race_number is not None and state.get("race_number") != race_number:
            logger.warning(
                "Race state gehört zu Rennen {} statt {} – verworfen",
                state.get("race_number"), race_number)
            return False

        if source_fingerprint is not None:
            saved_fp = state.get("_source_fingerprint")
            if saved_fp != source_fingerprint:
                logger.warning(
                    "Race state gehört zu einer anderen Datenquelle "
                    "(Fingerprint {} statt {}) – verworfen",
                    saved_fp, source_fingerprint)
                return False

        return True

    def clear(self) -> None:
        """Löscht race_state.json (nach erfolgreichem Recovery oder Reset).

        Wird aufgerufen, wenn:
        - Das Rennen normal abgeschlossen wurde
        - Der Benutzer ein neues Rennen startet
        - Die Daten aus IMPORT.json geladen wurden
        """
        self._last_payload_hash = None
        self._last_save_monotonic = 0.0
        if self._path.exists():
            try:
                self._path.unlink()
                logger.info("Race state gelöscht: {}", self._path)
            except OSError as exc:
                logger.warning("Race state konnte nicht gelöscht werden: {}", exc)

    # ------------------------------------------------------------------
    # Interne Helfer
    # ------------------------------------------------------------------

    def _atomic_write(self, payload: dict[str, Any]) -> bool:
        """Schreibt die JSON atomar (Temp-Datei + os.replace)."""
        tmp_path: str | None = None
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=self._dir, prefix=".race_state_", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False,
                          default=str)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self._path)
            return True
        except OSError as exc:
            logger.error("Race state konnte nicht gespeichert werden: {}", exc)
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            return False

    @staticmethod
    def _parse_saved_at(value: Any) -> datetime | None:
        """Parst `_saved_at`; naive Zeitstempel gelten als lokale Zeit."""
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.astimezone()
        return parsed

    @staticmethod
    def _format_age(age: timedelta) -> str:
        """Formatiert ein timedelta kompakt für Logmeldungen."""
        total_minutes = int(age.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}min"


__all__ = ["RaceStateManager"]
