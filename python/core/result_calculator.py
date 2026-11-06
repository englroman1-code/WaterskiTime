"""ResultCalculator – Runden, Zeiten und Platzierung (04_race_logic §3).

Berechnet aus den BoatStates:
    - Runden (Lap-Objekte): erste Runde = Rennstart → erste Passage,
      Folge-Runden = vorige Passage → aktuelle Passage
    - Gesamtzeit (Summe aller Rundenzeiten), schnellste Runde
    - Platzierung: primär Rundenzahl (mehr = besser),
      sekundär Gesamtzeit (weniger = besser) – Pflichtenheft §5.3
"""

from __future__ import annotations

from datetime import datetime, timedelta

from python.core.models import BoatResult, BoatState, Lap


class ResultCalculator:
    """Statische Helfer für Rundenberechnung und Wertung."""

    @staticmethod
    def add_lap(state: BoatState, end_time: datetime,
                race_start: datetime) -> Lap:
        """Schließt eine Runde ab und hängt sie an den Boots-Zustand an.

        - Erste Runde: start_time = individueller Startzeitpunkt des Boots
          (state.start_time, Variante A – Startreihe) bzw. Fallback Rennstart
          (race_start), wenn kein individueller Start gesetzt ist.
        - Folge-Runden: start_time = letzte Passage (state.last_passage)
        - Anschließend wird state.last_passage auf end_time gesetzt.

        Hinweis: Gegenüber dem Objektplan (add_lap(state, end_time)) benötigt
        die erste Runde den Startzeitpunkt – daher der Zusatzparameter.

        Args:
            state: Laufzeitzustand des Boots (wird verändert!).
            end_time: Zeitpunkt der Zielpassage.
            race_start: offizieller Rennstart (Fallback für die erste Runde,
                        wenn state.start_time nicht gesetzt ist).

        Returns:
            Das neu angelegte Lap (bereits an state.laps angehängt).

        Raises:
            ValueError: wenn end_time vor dem Rundenbeginn bzw. vor der letzten Passage.
        """
        if state.last_passage is None:
            # Variante A: erste Runde ab dem individuellen Startzeitpunkt des
            # Boots (Startreihe). Fallback: globaler Rennstart.
            start_time = state.start_time or race_start
        else:
            start_time = state.last_passage

        if end_time < start_time:
            raise ValueError(
                f"Passage {end_time} liegt vor Rundenbeginn {start_time}")

        lap = Lap(number=len(state.laps) + 1,
                  start_time=start_time, end_time=end_time)
        state.laps.append(lap)
        state.last_passage = end_time
        return lap

    @staticmethod
    def compute_results(boats: dict[str, BoatState]) -> list[BoatResult]:
        """Berechnet die Wertung für alle Boote.

        Sortierung (Pflichtenheft §5.3):
            1. Rundenzahl absteigend
            2. bei gleicher Rundenzahl: Gesamtzeit aufsteigend

        Die Platzierung wird **pro Klasse** vergeben (2026-09-04): In jeder
        Klasse gibt es einen Ersten, Zweiten, … – nicht global über alle
        Boote. Boote ohne vollständige Runde (laps_count == 0) erscheinen
        mit Platz 0 am Ende.

        Args:
            boats: boot_key → BoatState (Live-Zustände).

        Returns:
            Liste der BoatResults, sortiert (beste Platzierung zuerst).
        """
        results = []
        for state in boats.values():
            results.append(BoatResult(
                starter=state.starter,
                laps_count=state.laps_count,
                total_time=state.total_time,
                best_lap=state.best_lap,
            ))

        # Platzierung PRO KLASSE: Runden absteigend, Gesamtzeit aufsteigend.
        # Die Platznummern starten in jeder Klasse wieder bei 1.
        ranked = [r for r in results if r.laps_count > 0]
        ranked.sort(key=lambda r: (-r.laps_count, r.total_time))
        by_class: dict[str, list[BoatResult]] = {}
        for result in ranked:
            by_class.setdefault(result.starter.klasse, []).append(result)
        for klasse_results in by_class.values():
            for place, result in enumerate(klasse_results, start=1):
                result.place = place

        # Boote ohne Runde bekommen Platz 0 (keine Wertung)
        unranked = [r for r in results if r.laps_count == 0]
        for result in unranked:
            result.place = 0
        return ranked + unranked


__all__ = ["ResultCalculator"]
