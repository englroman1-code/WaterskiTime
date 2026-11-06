"""BlackboxWriter – unveränderliches Tastendruck-Protokoll (Beweisfunktion).

Die Blackbox ist der digitale Ersatz für einen unverfälschbaren
Zeilendrucker (Pflichtenheft §7, Objektplan §7.3, 03_data_flow.txt):

    - append-only: Bestehende Zeilen werden NIE verändert oder gelöscht,
      neue Einträge werden nur angehängt.
    - Nach jedem Eintrag werden flush() und fsync() aufgerufen → die Daten
      liegen sofort auf dem Datenträger (auch bei einem Absturz / Stromausfall).
    - Thread-sicher (Lock): Die Blackbox wird sowohl vom Keyboard-Thread
      (sofortiger Rohdruck) als auch vom GUI-Thread (Verarbeitungsergebnis)
      beschrieben.
    - Automatische Rotation bei > 10 MB (03_data_flow.txt Zeile 74): Die
      volle Datei wird mit Zeitstempel-Suffix umbenannt, eine neue begonnen.

Zeilenformat (Objektplan §7.3):

    [YYYY-MM-DD HH:MM:SS,mmm] TASTE: 'A' EVENT: PASSAGE STATUS: VALID

TASTE kann fehlen (Systemereignisse wie START); EVENT/STATUS fehlen beim
rohen Tastendruck (wird sofort im Keyboard-Thread geschrieben, bevor die
Verarbeitung das Ergebnis kennt).
"""

from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path


class BlackboxWriter:
    """Append-only TXT-Protokoll mit sofortigem flush() und Thread-Sicherheit."""

    # Rotationsgrenze aus 03_data_flow.txt (10 MB)
    DEFAULT_MAX_BYTES: int = 10 * 1024 * 1024

    def __init__(self, path: str | Path,
                 max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        """BlackboxWriter initialisieren.

        Args:
            path: Zieldatei (Verzeichnisse werden angelegt; vorhandene
                  Datei wird NICHT geleert – append-only!).
            max_bytes: Rotationsgrenze in Bytes (Default 10 MB).
        """
        self.path = Path(path)
        self.max_bytes = int(max_bytes)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()
        # "a" = anhängen: eine vorhandene Blackbox bleibt vollständig erhalten
        self._file = open(self.path, "a", encoding="utf-8")

    # ------------------------------------------------------------------
    # Schreiben
    # ------------------------------------------------------------------

    def write(self, entry: str) -> None:
        """Hängt einen Eintrag an (mit Zeilenumbruch) und flusht sofort.

        Args:
            entry: Eintragstext OHNE Zeilenumbruch.
        """
        line = f"{entry}\n"
        with self._lock:
            self._file.write(line)
            self._file.flush()
            # fsync: Daten auch bei Stromausfall/Absturz auf der Platte
            # (Beweisfunktion, Pflichtenheft §7). Fehler nicht eskalieren –
            # die Blackbox darf den Rennbetrieb nie blockieren.
            try:
                os.fsync(self._file.fileno())
            except OSError:
                pass
            if self._file.tell() > self.max_bytes:
                self._rotate_locked()

    def write_key_event(self, timestamp: datetime, key: str | None,
                        event_type: str | None, status: str | None) -> None:
        """Schreibt einen Eintrag im definierten Zeilenformat.

        Teile, die None sind, werden weggelassen:

            [2026-08-14 08:00:00,123] TASTE: 'A' EVENT: PASSAGE STATUS: VALID
            [2026-08-14 08:00:01,456] EVENT: START STATUS: VALID
            [2026-08-14 08:00:02,789] TASTE: 'a'          (Rohdruck)

        Args:
            timestamp: Ereigniszeitpunkt (Zeitquelle, injizierbar für Tests).
            key: gedrückte Taste (z. B. 'A'); None bei Systemereignissen.
            event_type: Ereignistyp (z. B. 'PASSAGE'); None beim Rohdruck.
            status: Verarbeitungsstatus ('VALID'/'INVALID'); None beim Rohdruck.
        """
        parts = [f"[{format_timestamp(timestamp)}]"]
        if key is not None:
            parts.append(f"TASTE: '{key}'")
        if event_type is not None:
            parts.append(f"EVENT: {event_type}")
        if status is not None:
            parts.append(f"STATUS: {status}")
        self.write(" ".join(parts))

    # ------------------------------------------------------------------
    # Lesen / Wiederherstellung
    # ------------------------------------------------------------------

    def replay(self) -> list[str]:
        """Liest alle Einträge (ohne Zeilenumbrüche) für die Rekonstruktion.

        Wird nach einem Absturz verwendet, um den Rennzustand wieder
        herzustellen (04_race_logic.txt: "Bei Neustart: Ereignisliste aus
        Blackbox-Log rekonstruieren").

        Returns:
            Alle Blackbox-Zeilen in chronologischer Reihenfolge.
        """
        with self._lock:
            self._file.flush()
        return [line.rstrip("\n") for line in self.path.read_text(
            encoding="utf-8").splitlines()]

    def close(self) -> None:
        """Schließt die Datei (danach kein write() mehr)."""
        with self._lock:
            self._file.close()

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def _rotate_if_needed(self) -> None:
        """Rotiert beim Öffnen, wenn die vorhandene Datei bereits voll ist."""
        if self.path.exists() and self.path.stat().st_size > self.max_bytes:
            self._rotate_locked()

    def _rotate_locked(self) -> None:
        """Benennt die volle Datei um und beginnt eine neue.

        Muss unter dem Blackbox-Lock aufgerufen werden. Wird auch aus
        __init__ aufgerufen, bevor die Datei geöffnet wurde.
        """
        suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived = self.path.with_name(
            f"{self.path.stem}_{suffix}{self.path.suffix}")
        if hasattr(self, "_file"):
            self._file.close()
        self.path.rename(archived)
        self._file = open(self.path, "a", encoding="utf-8")


def format_timestamp(ts: datetime) -> str:
    """Formatiert einen Zeitstempel als 'YYYY-MM-DD HH:MM:SS,mmm'.

    Die Mikrosekunden werden auf Millisekunden gekürzt (Objektplan-Format).

    Args:
        ts: Zeitpunkt.

    Returns:
        Formatierter Zeitstempel.
    """
    ms = ts.microsecond // 1000
    return f"{ts:%Y-%m-%d %H:%M:%S},{ms:03d}"


__all__ = ["BlackboxWriter", "format_timestamp"]
