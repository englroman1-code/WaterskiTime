"""ClassFinishTracker – manuelle Klassen-Beendigung (2026-09-03).

Hintergrund (Kundenentscheidung 2026-09-03): Die Ziellogik wurde vereinfacht.
Nach Ablauf der Renndauer (Phase FINISHING) passiert NICHTS automatisch.
Der Bediener beendet jede Klasse MANUELL über einen "Beenden"-Button im
GUI-Panel 'Rennende-Status'. Beim Beenden werden alle Boote der Klasse als
fertig markiert (finished_at = Zeitpunkt der Beendigung) und das Ergebnis
steht fest (meiste Runden in kürzester Zeit).

Die frühere "Letzte Runde"-Logik (finish_mode, TRIGGERED-Zustand) wurde
komplett entfernt.

Zustände je Klasse:
    WAITING → Klasse ist offen (Rennen läuft noch für diese Klasse)
    CLOSED  → Klasse wurde manuell beendet (alle Boote fertig)

Hinweis zur API: Der Tracker hält Referenzen auf die Klassen- und
Boots-Dictionaries der Engine – dadurch sind die finish_class-Aufrufe ohne
Zusatzparameter möglich.
"""

from __future__ import annotations

from datetime import datetime

from python.core.models import BoatState, RaceClass

# Klassen-Zustände (werden auch von der GUI angezeigt – Übersetzung dort)
STATE_WAITING = "WAITING"
STATE_CLOSED = "CLOSED"


class ClassFinishTracker:
    """Verwaltet die manuelle Klassen-Beendigung der Engine."""

    def __init__(self, classes: dict[str, RaceClass],
                 boats: dict[str, BoatState]) -> None:
        """ClassFinishTracker initialisieren.

        Args:
            classes: Klassenname → RaceClass (Live-Zustände, Referenz!).
            boats: boot_key → BoatState (Live-Zustände, Referenz!).
        """
        self._classes = classes
        self._boats = boats

    def finish_class(self, klasse: str, now: datetime) -> bool:
        """Beendet eine Klasse manuell: alle Boote der Klasse werden fertig.

        Setzt für jedes Boot der Klasse `finished_at = now` (falls noch nicht
        fertig) und markiert die Klasse als CLOSED.

        Args:
            klasse: Klassenname.
            now: Zeitpunkt der Beendigung.

        Returns:
            True, wenn die Klasse (jetzt) CLOSED ist; sonst False.
        """
        race_class = self._classes.get(klasse)
        if race_class is None:
            return False
        for state in self._boats.values():
            if state.starter.klasse == klasse and state.finished_at is None:
                state.finished_at = now
        race_class.finish_state = STATE_CLOSED
        return True

    def all_closed(self) -> bool:
        """True, wenn alle Klassen des Rennens CLOSED sind.

        Damit ist das Rennen komplett → Phase FINISHED (Engine).
        """
        return all(
            race_class.finish_state == STATE_CLOSED
            for race_class in self._classes.values()
        )

    def status(self) -> dict[str, str]:
        """Aktueller Zustand je Klasse (für das GUI-Panel 'Rennende-Status').

        Returns:
            Klassenname → "WAITING" | "CLOSED".
        """
        return {name: cls.finish_state for name, cls in self._classes.items()}

    def reset(self) -> None:
        """Setzt alle Klassen zurück auf WAITING (neues Rennen)."""
        for race_class in self._classes.values():
            race_class.finish_state = STATE_WAITING


__all__ = ["ClassFinishTracker", "STATE_WAITING", "STATE_CLOSED"]
