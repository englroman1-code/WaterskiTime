"""LockoutManager – Sperrzeit je Boot (Pflichtenheft §5.2).

Verhindert Doppelerfassungen: Eingaben innerhalb der Sperrzeit werden als
UNGÜLTIG (INVALID) markiert, aber trotzdem vollständig protokolliert
(Nachvollziehbarkeit, Beweisfunktion – siehe RaceEngine.handle_key_press).

Die Sperrzeit ist ein APP-Parameter (Q1, Entscheidung 2026-08-13) und liegt
in `AppSettings.lockout_seconds` (JSON), nicht im RaceConfig.

Zeitquelle: `datetime` wird injiziert (now-Parameter) → deterministisch testbar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class LockoutManager:
    """Verwaltet die Sperrzeit je Boot-Key.

    Pro Boot wird der Zeitpunkt der letzten GÜLTIGEN Eingabe gemerkt
    (`_last_valid`). `is_allowed()` vergleicht mit der aktuellen Zeit.

    Threading-Hinweis: Die Engine läuft im Main-Thread (ADR-007), deshalb
    ist dieser Manager nicht thread-safe ausgelegt.
    """

    lockout_seconds: float = 2.0   # Sperrzeit in Sekunden (App-Parameter, Q1)
    _last_valid: dict[str, datetime] = field(default_factory=dict, init=False)

    def is_allowed(self, boot_key: str, now: datetime) -> bool:
        """Prüft, ob eine Eingabe für das Boot erlaubt ist.

        Erlaubt, wenn:
            - noch nie eine gültige Eingabe erfolgte, ODER
            - seit der letzten gültigen Eingabe ≥ Sperrzeit vergangen ist.

        Args:
            boot_key: Boot-Key (A–Z, normalisiert als UPPER).
            now: aktueller Zeitpunkt (Zeitquelle, injizierbar für Tests).

        Returns:
            True → Eingabe erlaubt; False → Sperrzeit läuft noch.
        """
        last = self._last_valid.get(boot_key.upper())
        if last is None:
            return True
        return (now - last) >= timedelta(seconds=self.lockout_seconds)

    def register(self, boot_key: str, now: datetime) -> None:
        """Merkt die letzte gültige Eingabe für ein Boot.

        Wird NUR bei gültigen Eingaben aufgerufen (in der Engine nach
        erfolgreicher Sperrzeit-Prüfung).

        Args:
            boot_key: Boot-Key (A–Z).
            now: Zeitpunkt der gültigen Eingabe.
        """
        self._last_valid[boot_key.upper()] = now

    def remaining(self, boot_key: str, now: datetime) -> timedelta:
        """Verbleibende Sperrzeit für die GUI-Anzeige (z. B. "SPERRZEIT (35s)").

        Args:
            boot_key: Boot-Key (A–Z).
            now: aktueller Zeitpunkt.

        Returns:
            Restzeit als timedelta (0 wenn keine Sperrzeit aktiv).
        """
        last = self._last_valid.get(boot_key.upper())
        if last is None:
            return timedelta()
        elapsed = now - last
        remaining = timedelta(seconds=self.lockout_seconds) - elapsed
        return max(remaining, timedelta())

    def reset(self) -> None:
        """Setzt alle Sperrzeit-Zustände zurück (neues Rennen)."""
        self._last_valid.clear()


__all__ = ["LockoutManager"]
