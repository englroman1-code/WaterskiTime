"""RaceEngine – zentrale Steuerung der Rennlogik (Zustandsmaschine).

Verantwortlich (Objektplan Kapitel 5.1):
    - Rennphasen: PRESTART → ACTIVE → FINISHING → FINISHED
    - Countdown-Verwaltung inkl. Pause/Weiter (Q8, Entscheidung 2026-08-14:
      Der Countdown startet das Rennen automatisch – kein Startsignal)
    - Ereignisverarbeitung: Hotkeys (Passage), manuelle Korrektur (+1, Q6),
      Sperrzeit-Prüfung (LockoutManager)
    - Manuelle Klassen-Beendigung (ClassFinishTracker, 2026-09-03)
    - Wertung (ResultCalculator: Runden primär, Gesamtzeit sekundär)

Threading (ADR-007): Die Engine läuft ausschließlich im GUI-/Main-Thread.
Die Zeitquelle wird als `now`-Parameter injiziert → deterministisch testbar.

Startlinien-Offsets (Entscheidung 2026-09-02): Die Zeit zwischen den
Startreihen kommt aus `RaceConfig.grid_time_s` (Grid Time, Excel/IMPORT.json,
Pflichtfeld) – es gibt KEINEN festen Offset mehr aus der App-Config und
keine hartcodierten Defaults.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from python.core.class_finish_tracker import ClassFinishTracker
from python.core.lockout_manager import LockoutManager
from python.core.models import (
    BoatResult,
    BoatState,
    Event,
    EventType,
    Lap,
    RaceClass,
    RaceConfig,
    RaceEvent,
    RacePhase,
    StartLine,
    Starter,
)
from loguru import logger
from python.core.result_calculator import ResultCalculator


class RaceEngine:
    """Kernlogik: Rennphasen, Ereignisverarbeitung, Ergebnisberechnung."""

    def __init__(self) -> None:
        """RaceEngine initialisieren (leer – erst load_race() aufrufen)."""
        self.phase: RacePhase = RacePhase.RESET
        self.race: Event = Event()
        self.config: RaceConfig = RaceConfig()
        self.boats: dict[str, BoatState] = {}
        self.classes: dict[str, RaceClass] = {}
        self.events: list[RaceEvent] = []          # append-only (Rekonstruktion)
        self._starters: list[Starter] = []
        self.start_lines: dict[int, StartLine] = {}
        self._lockout: LockoutManager | None = None
        self._tracker: ClassFinishTracker | None = None

        # Zeitbasis
        self.countdown_end: datetime | None = None
        self.countdown_paused: bool = False        # Q8: Countdown unterbrechbar
        self._countdown_remaining: timedelta = timedelta()
        self.race_start: datetime | None = None
        self.race_end: datetime | None = None
        self._started_lines: set[int] = set()      # bereits gestartete Startreihen

        # Ergebnisse beendeter Rennen (Option 1, 2026-09-03): Damit die
        # Ergebnisse eines beendeten Rennens beim Rennwechsel erhalten bleiben,
        # werden sie hier pro Rennnummer gespeichert (in-memory). Beim
        # Zurückwechseln (load_race) werden sie wiederhergestellt.
        self.finished_races: dict[int, dict] = {}

    # ------------------------------------------------------------------
    # Konfiguration / Rennen laden
    # ------------------------------------------------------------------

    def load_race(self, race: Event, config: RaceConfig,
                  starters: list[Starter], lockout_seconds: float) -> None:
        """Lädt ein Rennen (Countdown wird NICHT automatisch gestartet).

        Der Benutzer muss explizit start_countdown() aufrufen (Play-Button).

        Args:
            race: Veranstaltungsdaten (Event).
            config: Rennkonfiguration (Dauer, Countdown, Grid Time).
            starters: Starterliste des Rennens.
            lockout_seconds: Sperrzeit in Sekunden (App-Parameter, Q1).
        """
        self.race = race
        self.config = config
        self._starters = starters
        self.boats = {s.boot_key.upper(): BoatState(starter=s)
                      for s in starters}
        # Klassen aus den Startern ableiten (statt class_mapping)
        class_names = sorted({s.klasse for s in starters if s.klasse})
        self.classes = {name: RaceClass(name=name) for name in class_names}
        # Startreihen aus den Startern ableiten; Offset = Grid Time aus der
        # Rennkonfiguration (Excel/IMPORT.json, Pflichtfeld, Entscheidung 2026-09-02)
        startreihe_numbers = sorted(
            {s.startreihe for s in starters if s.startreihe > 0})
        self.start_lines = {
            num: StartLine(
                number=num,
                offset_seconds=(num - 1) * config.grid_time_s)
            for num in startreihe_numbers
        }
        self.events = []
        self._lockout = LockoutManager(lockout_seconds=lockout_seconds)
        self._tracker = ClassFinishTracker(self.classes, self.boats)
        # Frisch geladenes Rennen steht immer auf RESET (Bugfix 2026-09-02):
        # Nach einem beendeten Rennen (Phase FINISHED) blieb die Phase beim
        # Rennwechsel stehen → Countdown-Anzeige 0 und PLAY-Button wirkungslos.
        self.phase = RacePhase.RESET
        self.race_start = None
        self.race_end = None
        self.countdown_end = None
        self.countdown_paused = False
        self._started_lines = set()
        # Countdown wird NICHT automatisch gestartet – Play-Button nötig!

        # Option 1 (2026-09-03): Bereits beendete Ergebnisse dieses Rennens
        # wiederherstellen, damit sie beim Zurückwechseln erhalten bleiben.
        self._restore_finished_race()

    def _restore_finished_race(self) -> None:
        """Stellt die Ergebnisse eines bereits beendeten Rennens wieder her.

        Wenn für die aktuelle Rennnummer bereits Ergebnisse in
        `finished_races` gespeichert sind (Rennen wurde früher beendet),
        werden die Boot-Zustände (Runden, Zeiten, finished_at, Platzierung),
        die Events und der Klassen-Status wiederhergestellt.

        Die Phase bleibt RESET (frisch geladen) – der Bediener kann das
        Rennen erneut starten oder die Ergebnisse ansehen/exportieren.
        """
        race_number = self.config.race_number
        saved = self.finished_races.get(race_number)
        if saved is None:
            return

        # Boot-Zustände wiederherstellen (Runden, Zeiten, finished_at, Platz)
        saved_boats = saved.get("boats", {})
        for key, state in self.boats.items():
            old = saved_boats.get(key)
            if old is None:
                continue
            state.laps = list(old.laps)
            state.last_passage = old.last_passage
            # getattr: sehr alte In-Memory-States kennen das Feld noch nicht
            state.last_real_passage = getattr(old, "last_real_passage", None)
            state.finished_at = old.finished_at
            state.place = old.place
            state.start_time = old.start_time

        # Events wiederherstellen (Renn-Log bleibt erhalten)
        self.events = list(saved.get("events", []))

        # Klassen-Status wiederherstellen (WARTEND/FERTIG)
        # Der Tracker hält Referenzen auf dieselben RaceClass-Objekte,
        # daher ist er automatisch synchronisiert.
        saved_classes = saved.get("classes", {})
        for name, cls in self.classes.items():
            if name in saved_classes:
                cls.finish_state = saved_classes[name]

    # ------------------------------------------------------------------
    # Phasen-Steuerung
    # ------------------------------------------------------------------

    def start_countdown(self, now: datetime | None = None) -> None:
        """Startet/neustartet den Countdown (PRESTART).

        Q8: Es gibt kein Startsignal – der Countdown startet das Rennen,
        sobald er auf 0 läuft (siehe tick).

        Args:
            now: Zeitbasis (injizierbar für Tests; Default: datetime.now()).
        """
        self.phase = RacePhase.PRESTART
        self.countdown_paused = False
        self.race_start = None
        self.race_end = None
        base = now or datetime.now()
        self.countdown_end = base + timedelta(seconds=self.config.start_interval_s)

    def pause_countdown(self, now: datetime | None = None) -> None:
        """Unterbricht den Countdown (Q8): Restzeit wird eingefroren.

        Args:
            now: Zeitpunkt der Pause (injizierbar für Tests).
        """
        if self.phase != RacePhase.PRESTART or self.countdown_paused:
            return
        base = now or datetime.now()
        self._countdown_remaining = max(self.countdown_end - base, timedelta())
        self.countdown_paused = True

    def resume_countdown(self, now: datetime | None = None) -> None:
        """Setzt den Countdown fort (Q8): Restzeit läuft exakt weiter.

        Args:
            now: Zeitpunkt der Fortsetzung (injizierbar für Tests).
        """
        if self.phase != RacePhase.PRESTART or not self.countdown_paused:
            return
        base = now or datetime.now()
        self.countdown_end = base + self._countdown_remaining
        self.countdown_paused = False

    def countdown_remaining(self, now: datetime) -> timedelta:
        """Verbleibende Countdown-Zeit (für die GUI-Anzeige).

        Args:
            now: aktueller Zeitpunkt.

        Returns:
            Restzeit (0 wenn abgelaufen/pausiert → pausiert liefert eingefrorene Zeit).
        """
        if self.countdown_paused:
            return self._countdown_remaining
        if self.countdown_end is None:
            return timedelta()
        return max(self.countdown_end - now, timedelta())

    def start_race(self, now: datetime) -> None:
        """Startet das Rennen offiziell (ACTIVE).

        Setzt race_start (= now) und race_end (= race_start + Renndauer)
        und protokolliert das START-Ereignis (Systemereignis).

        Zeitversetzte Starts (Variante A, Entscheidung 2026-09-03):
        Jedes Boot bekommt einen individuellen Startzeitpunkt, wenn seine
        Startreihe startet: Startreihe 1 → sofort (now), Startreihe 2 →
        now + Grid Time, Startreihe 3 → now + 2 × Grid Time, usw.
        Die erste Runde eines Boots wird ab diesem Startzeitpunkt gemessen.

        Args:
            now: offizieller Rennstart-Zeitpunkt (Start der Startreihe 1).
        """
        self.phase = RacePhase.ACTIVE
        self.race_start = now
        self.race_end = now + timedelta(minutes=self.config.race_duration_min)
        # Individuelle Startzeitpunkte pro Boot (Startreihen-Offset, Variante A)
        for state in self.boats.values():
            startreihe = state.starter.startreihe
            offset = (startreihe - 1) * self.config.grid_time_s
            state.start_time = now + timedelta(seconds=offset)
        self.events.append(RaceEvent(
            timestamp=now, boot_key="", event_type=EventType.START,
            valid=True, source="SYSTEM",
            detail=f"Race={self.config.race_number}"))

    # ------------------------------------------------------------------
    # Ereignisverarbeitung (Hotkeys)
    # ------------------------------------------------------------------

    def handle_key_press(self, boot_key: str, now: datetime) -> RaceEvent:
        """Verarbeitet eine Hotkey-Eingabe (Passage) eines Boots.

        Ablauf (Objektplan Kapitel 9):
            1. Nur in ACTIVE/FINISHING gültig – sonst INVALID-Ereignis
            2. Sperrzeit-Prüfung (LockoutManager) → INVALID, wenn verletzt
               (wird trotzdem vollständig protokolliert!)
            3. Runde abschließen (ResultCalculator.add_lap)

        Hinweis (2026-09-03): Die automatische Ziellogik wurde entfernt.
        In der Endphase (FINISHING) passiert nach einer Passage NICHTS
        automatisch – der Bediener beendet Klassen manuell (finish_class).

        Args:
            boot_key: Boot-Key (A–Z).
            now: Zeitpunkt der Eingabe (Zeitquelle).

        Returns:
            Das erzeugte RaceEvent (PASSAGE oder INVALID).
        """
        key = boot_key.upper()
        state = self.boats.get(key)
        if state is None:
            raise ValueError(f"Unbekannter Boot-Key: {key}")

        # --- 1. Nur während des Rennens gültig ----------------------------
        if self.phase not in (RacePhase.ACTIVE, RacePhase.FINISHING):
            event = RaceEvent(timestamp=now, boot_key=key,
                              event_type=EventType.INVALID, valid=False)
            self.events.append(event)
            return event

        # --- 1a. Boot noch nicht gestartet (Startreihe noch nicht dran) ----
        # Variante A: Ein Boot darf erst Passagen machen, wenn seine
        # Startreihe gestartet ist (individueller Startzeitpunkt erreicht).
        if state.start_time is not None and now < state.start_time:
            event = RaceEvent(timestamp=now, boot_key=key,
                              event_type=EventType.INVALID, valid=False)
            self.events.append(event)
            return event

        # --- 1b. Boot bereits fertig → keine weitere Runde ----------------
        if state.finished_at is not None:
            event = RaceEvent(timestamp=now, boot_key=key,
                              event_type=EventType.INVALID, valid=False)
            self.events.append(event)
            return event

        # --- 2. Sperrzeit-Prüfung (Pflichtenheft §5.2) --------------------
        assert self._lockout is not None
        if not self._lockout.is_allowed(key, now):
            event = RaceEvent(timestamp=now, boot_key=key,
                              event_type=EventType.INVALID, valid=False)
            self.events.append(event)
            return event
        self._lockout.register(key, now)
        # Anzeige-Feld für die Live-Tabelle (SPERRZEIT-Zelle): ab jetzt gilt
        # die Sperrzeit für dieses Boot. Aufräumen übernimmt die GUI (Tick).
        state.lockout_until = now + timedelta(
            seconds=self._lockout.lockout_seconds)

        # --- 3. Runde abschließen -----------------------------------------
        assert self.race_start is not None
        ResultCalculator.add_lap(state, now, self.race_start)
        # Echte Zielpassage merken (2026-11-10): Grundlage für die
        # Rennende-Ampel. +1-Korrekturen setzen dieses Feld bewusst NICHT,
        # weil ihr Zeitstempel die Klickzeit und keine Zielpassage ist.
        state.last_real_passage = now
        event = RaceEvent(timestamp=now, boot_key=key,
                          event_type=EventType.PASSAGE, valid=True)
        self.events.append(event)

        return event

    def finish_class(self, klasse: str, now: datetime) -> bool:
        """Beendet eine Klasse manuell (Kundenentscheidung 2026-09-03).

        Alle Boote der Klasse werden als fertig markiert (finished_at = now)
        und die Klasse wird CLOSED. Das Ergebnis steht damit fest
        (meiste Runden in kürzester Zeit).

        Wenn alle Klassen beendet sind, wechselt die Engine zu FINISHED.

        Args:
            klasse: Klassenname der zu beendenden Klasse.
            now: Zeitpunkt der Beendigung.

        Returns:
            True, wenn die Klasse beendet wurde; sonst False.
        """
        assert self._tracker is not None
        if self.phase not in (RacePhase.ACTIVE, RacePhase.FINISHING):
            return False
        if not self._tracker.finish_class(klasse, now):
            return False
        # FINISH-Ereignis für jedes Boot der Klasse protokollieren
        for state in self.boats.values():
            if state.starter.klasse == klasse and state.finished_at == now:
                self.events.append(RaceEvent(
                    timestamp=now, boot_key=state.starter.boot_key,
                    event_type=EventType.FINISH, valid=True))
        if self._tracker.all_closed():
            self.phase = RacePhase.FINISHED
            self._store_finished_race()
        return True

    def _store_finished_race(self) -> None:
        """Speichert die Ergebnisse des aktuellen (fertigen) Rennens.

        Option 1 (2026-09-03): Damit die Ergebnisse eines beendeten Rennens
        beim Rennwechsel erhalten bleiben, werden sie in `finished_races`
        (keyed by race_number) abgelegt. Beim Zurückwechseln (load_race)
        werden sie wiederhergestellt.

        Gespeichert werden die Platzierungen (BoatResult) sowie die
        Rohdaten (Events, Klassen-Status), damit das Rennen vollständig
        rekonstruiert werden kann.
        """
        race_number = self.config.race_number
        if race_number <= 0:
            return
        self.finished_races[race_number] = {
            "config": self.config,
            "results": self.get_placements(),
            "events": list(self.events),
            "classes": {name: cls.finish_state
                        for name, cls in self.classes.items()},
            "boats": {key: state for key, state in self.boats.items()},
        }

    def handle_manual_correction(self, boot_key: str, delta: int,
                                 now: datetime) -> RaceEvent:
        """Manuelle Rundengutschrift (Pflichtenheft §6).

        Q6 (Entscheidung 2026-08-14): Im MVP ist NUR +1 erlaubt –
        eine −1-Korrektur gibt es nicht.

        Die Korrektur-Runde wird wie eine Passage verbucht (von der letzten
        Passage bis jetzt), erzeugt aber kein FINISH/Trigger.

        Args:
            boot_key: Boot-Key (A–Z).
            delta: nur +1 zulässig.
            now: Zeitpunkt der Korrektur.

        Returns:
            Das CORRECTION_PLUS-Ereignis.

        Raises:
            ValueError: bei delta != 1 (Q6) oder unbekanntem Boot-Key
                        oder Korrektur vor Rennstart.
        """
        if delta != 1:
            raise ValueError(f"Q6: nur +1 erlaubt, delta={delta} nicht unterstützt")
        key = boot_key.upper()
        state = self.boats.get(key)
        if state is None:
            raise ValueError(f"Unbekannter Boot-Key: {key}")
        if self.phase not in (RacePhase.ACTIVE, RacePhase.FINISHING):
            raise ValueError(f"Korrektur nicht möglich in Phase {self.phase}")
        assert self.race_start is not None

        ResultCalculator.add_lap(state, now, self.race_start)
        event = RaceEvent(timestamp=now, boot_key=key,
                          event_type=EventType.CORRECTION_PLUS,
                          valid=True, source="MANUAL")
        self.events.append(event)
        return event

    # ------------------------------------------------------------------
    # Tick / Zeitsteuerung (vom GUI im after()-Poll aufgerufen)
    # ------------------------------------------------------------------

    def tick(self, now: datetime) -> None:
        """Zeitprüfung: Countdown, Renndauer, Endphase (vom GUI getaktet).

        Args:
            now: aktueller Zeitpunkt.
        """
        if self.phase == RacePhase.PRESTART:
            if not self.countdown_paused and self.countdown_end is not None:
                if now >= self.countdown_end:
                    # Q8: Countdown abgelaufen → Rennen startet automatisch
                    self.start_race(now)
        elif self.phase == RacePhase.ACTIVE:
            if self.race_end is not None and now >= self.race_end:
                self.phase = RacePhase.FINISHING   # Endphase beginnt (§5.3)
            else:
                self._check_start_lines(now)
        elif self.phase == RacePhase.FINISHING:
            # Kein Zeitkriterium und keine automatische Ziellogik mehr
            # (2026-09-03): Der Bediener beendet Klassen manuell über
            # finish_class(). Das Rennen endet, wenn alle Klassen beendet sind.
            pass

    def _check_start_lines(self, now: datetime) -> None:
        """Protokolliert STARTLINE-Ereignisse für Startreihen, die starten.

        Variante A (zeitversetzte Starts): Sobald der individuelle
        Startzeitpunkt einer Startreihe erreicht ist, wird ein STARTLINE-
        Ereignis protokolliert (Renn-Log, Zeilendrucker-Stil).

        Args:
            now: aktueller Zeitpunkt.
        """
        for state in self.boats.values():
            startreihe = state.starter.startreihe
            if (state.start_time is not None
                    and now >= state.start_time
                    and startreihe not in self._started_lines):
                self._started_lines.add(startreihe)
                self.events.append(RaceEvent(
                    timestamp=state.start_time, boot_key="",
                    event_type=EventType.STARTLINE, valid=True,
                    source="SYSTEM",
                    detail=f"Race={self.config.race_number};"
                           f"Line={startreihe}"))

    def race_remaining(self, now: datetime) -> timedelta:
        """Verbleibende Renndauer (für die GUI-Anzeige).

        Args:
            now: aktueller Zeitpunkt.

        Returns:
            Restzeit (0 wenn nicht aktiv bzw. abgelaufen).
        """
        if self.race_end is None:
            return timedelta()
        return max(self.race_end - now, timedelta())

    def race_elapsed(self, now: datetime) -> timedelta:
        """Vergangene Renndauer seit dem ersten Start (für die GUI-Anzeige).

        Die linke Uhr zeigt nach dem Start aller Startreihen nicht mehr den
        Startreihen-Countdown, sondern die tatsächliche Renndauer. Basis ist
        `race_start` (Start der Startreihe 1). In der Phase FINISHED wird die
        Anzeige auf den Zeitpunkt des letzten Zieleinlaufs eingefroren, damit
        sie nach Rennende nicht weiterläuft.

        Args:
            now: aktueller Zeitpunkt.

        Returns:
            Vergangene Zeit seit dem ersten Start (0 wenn noch nicht gestartet).
        """
        if self.race_start is None:
            return timedelta()
        end = now
        if self.phase == RacePhase.FINISHED:
            finished = [state.finished_at for state in self.boats.values()
                        if state.finished_at is not None]
            if finished:
                end = max(finished)
        return max(end - self.race_start, timedelta())

    def start_line_remaining(self, now: datetime) -> timedelta:
        """Zeit bis zum Start der nächsten noch nicht gestarteten Startreihe.

        Variante A (zeitversetzte Starts): Nach dem Rennstart (ACTIVE) starten
        die Startreihen nacheinander im Abstand der Grid Time. Diese Methode
        liefert die Restzeit bis zum Start der nächsten Startreihe – für die
        Countdown-Anzeige "START REIHE N".

        Args:
            now: aktueller Zeitpunkt.

        Returns:
            Restzeit bis zum nächsten Startreihen-Start (0 wenn alle
            Startreihen gestartet sind oder das Rennen nicht aktiv ist).
        """
        if self.phase != RacePhase.ACTIVE or self.race_start is None:
            return timedelta()
        # Nächste noch nicht gestartete Startreihe (kleinster Startzeitpunkt
        # in der Zukunft)
        next_start = None
        for state in self.boats.values():
            if state.start_time is not None and state.start_time > now:
                if next_start is None or state.start_time < next_start:
                    next_start = state.start_time
        if next_start is None:
            return timedelta()
        return max(next_start - now, timedelta())

    def next_start_line(self, now: datetime) -> int | None:
        """Nummer der nächsten noch nicht gestarteten Startreihe.

        Args:
            now: aktueller Zeitpunkt.

        Returns:
            Startreihen-Nummer der nächsten Startreihe, die noch nicht
            gestartet ist (None wenn alle gestartet sind).
        """
        next_start = None
        next_num = None
        for state in self.boats.values():
            if state.start_time is not None and state.start_time > now:
                if next_start is None or state.start_time < next_start:
                    next_start = state.start_time
                    next_num = state.starter.startreihe
        return next_num

    # ------------------------------------------------------------------
    # Reset / Wertung
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Setzt das Rennen zurück – bereit für einen neuen Durchgang (Q4/Q8).

        Boots-Zustände, Ereignisliste, Sperrzeit und Klassen-Zustände werden
        geleert; die Engine steht auf Phase RESET. Der Play-Button muss
        explizit gedrückt werden um den Countdown zu starten (§6).
        """
        self.boats = {s.boot_key.upper(): BoatState(starter=s)
                      for s in self._starters}
        # Klassen aus den Startern ableiten (statt class_mapping)
        class_names = sorted({s.klasse for s in self._starters if s.klasse})
        self.classes = {name: RaceClass(name=name) for name in class_names}
        self.events = []
        self._lockout = LockoutManager(lockout_seconds=self._lockout.lockout_seconds)
        self._tracker = ClassFinishTracker(self.classes, self.boats)
        self.phase = RacePhase.RESET
        self.race_start = None
        self.race_end = None
        self.countdown_end = None
        self.countdown_paused = False
        self._started_lines = set()

    def get_placements(self) -> list[BoatResult]:
        """Berechnet die Wertung (Runden primär, Gesamtzeit sekundär).

        Schreibt die Plätze zusätzlich in die BoatStates zurück,
        damit die Live-Tabelle sie anzeigen kann.

        Returns:
            Sortierte Ergebnisliste (1. Platz zuerst).
        """
        results = ResultCalculator.compute_results(self.boats)
        for result in results:
            state = self.boats[result.starter.boot_key.upper()]
            state.place = result.place if result.place > 0 else None
        return results

    def get_class_finish_status(self) -> dict[str, str]:
        """Aktuelle Klassen-Zustände für das GUI-Panel 'Rennende-Status'.

        Returns:
            Klassenname → "WAITING" | "CLOSED".
        """
        assert self._tracker is not None
        return self._tracker.status()

    def get_crossed_after_race_end(self) -> dict[str, bool]:
        """Je Boot: hat es nach dem Rennende noch eine echte Zielpassage gehabt?

        Grundlage ist `BoatState.last_real_passage` – also nur echte
        Hotkey-Passagen, keine manuellen +1-Korrekturen. Die GUI zeigt damit
        nach Ablauf der Renndauer pro Boot einen grünen Punkt (im Ziel
        angekommen) oder einen roten Punkt (noch nicht).

        Returns:
            boot_key → True, wenn die letzte echte Passage am oder nach
            `race_end` liegt; sonst False. Vor dem Rennstart (kein
            `race_end`) sind alle Werte False.
        """
        if self.race_end is None:
            return {key: False for key in self.boats}
        return {
            key: (state.last_real_passage is not None
                  and state.last_real_passage >= self.race_end)
            for key, state in self.boats.items()
        }

    # ------------------------------------------------------------------
    # Serialisierung (Crash-Recovery)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialisiert den aktuellen Engine-Zustand als JSON-kompatiblen Dict.

        Enthält alle Daten, die für die Wiederherstellung nach Absturz nötig sind:
        Rennnummer, Phase, Zeitstempel, Boot-Zustände, Events, Klassen.

        Returns:
            Dict mit dem vollständigen Zustand.
        """
        boats_dict = {}
        for key, state in self.boats.items():
            boats_dict[key] = {
                "boat_number": state.starter.boat_number,
                "skier": state.starter.skier,
                "klasse": state.starter.klasse,
                "race_number": state.starter.race_number,
                "startreihe": state.starter.startreihe,
                "boot_key": state.starter.boot_key,
                "laps_count": state.laps_count,
                "total_time_s": state.total_time.total_seconds(),
                "last_passage": state.last_passage.isoformat() if state.last_passage else None,
                "last_real_passage": (state.last_real_passage.isoformat()
                                      if state.last_real_passage else None),
                "finished_at": state.finished_at.isoformat() if state.finished_at else None,
                "place": state.place,
                "start_time": state.start_time.isoformat() if state.start_time else None,
                # Vollständige Runden (2026-11-06): exakte Start-/Endzeiten,
                # damit nach einem Crash keine synthetischen Zeiten entstehen.
                "laps": [
                    {
                        "number": lap.number,
                        "start_time": lap.start_time.isoformat(),
                        "end_time": lap.end_time.isoformat(),
                    }
                    for lap in state.laps
                ],
            }

        events_list = []
        for event in self.events:
            events_list.append({
                "timestamp": event.timestamp.isoformat(),
                "boot_key": event.boot_key,
                "event_type": event.event_type.value,
                "valid": event.valid,
                "source": event.source,
                "detail": event.detail,
            })

        classes_dict = {}
        for name, cls in self.classes.items():
            classes_dict[name] = {
                "finish_state": cls.finish_state,
            }

        return {
            "race_number": self.config.race_number,
            "phase": self.phase.value,
            "race_start": self.race_start.isoformat() if self.race_start else None,
            "race_end": self.race_end.isoformat() if self.race_end else None,
            "countdown_end": self.countdown_end.isoformat() if self.countdown_end else None,
            "countdown_paused": self.countdown_paused,
            "started_lines": sorted(self._started_lines),
            "boats": boats_dict,
            "events": events_list,
            "classes": classes_dict,
        }

    def restore_from_state(self, state: dict) -> None:
        """Stellt den Engine-Zustand aus einem gespeicherten Dict wieder her.

        Wird für Crash-Recovery aufgerufen nach load_race().
        Setzt Phase, Zeitstempel, Boot-Zustände und Events.

        Args:
            state: Dict aus RaceStateManager.load() (race_state.json).
        """
        # Phase wiederherstellen
        phase_str = state.get("phase", "RESET")
        try:
            self.phase = RacePhase(phase_str)
        except ValueError:
            self.phase = RacePhase.RESET

        # Zeitstempel wiederherstellen
        def _parse_dt(val: str | None) -> datetime | None:
            if val is None:
                return None
            try:
                return datetime.fromisoformat(val)
            except (ValueError, TypeError):
                return None

        self.race_start = _parse_dt(state.get("race_start"))
        self.race_end = _parse_dt(state.get("race_end"))
        self.countdown_end = _parse_dt(state.get("countdown_end"))
        self.countdown_paused = state.get("countdown_paused", False)
        self._started_lines = set(state.get("started_lines", []))

        # Boot-Zustände wiederherstellen
        for key, boat_data in state.get("boats", {}).items():
            if key in self.boats:
                bs = self.boats[key]
                saved_laps = boat_data.get("laps_count", 0)
                bs.last_passage = _parse_dt(boat_data.get("last_passage"))
                bs.last_real_passage = _parse_dt(
                    boat_data.get("last_real_passage"))
                bs.finished_at = _parse_dt(boat_data.get("finished_at"))
                bs.place = boat_data.get("place")
                bs.start_time = _parse_dt(boat_data.get("start_time"))

                # Runden exakt wiederherstellen (2026-11-06). Nur wenn der
                # State keine Lap-Details enthält (altes Schema), wird NICHT
                # synthetisch gemittelt – falsche Rundenzeiten wären schlimmer
                # als fehlende. In diesem Fall bleibt die Liste leer.
                saved_laps_data = boat_data.get("laps")
                restored_laps: list[Lap] = []
                if isinstance(saved_laps_data, list):
                    for index, lap_data in enumerate(saved_laps_data, start=1):
                        if not isinstance(lap_data, dict):
                            continue
                        lap_start = _parse_dt(lap_data.get("start_time"))
                        lap_end = _parse_dt(lap_data.get("end_time"))
                        if lap_start is None or lap_end is None:
                            continue
                        try:
                            lap_number = int(lap_data.get("number", index))
                        except (TypeError, ValueError):
                            lap_number = index
                        restored_laps.append(Lap(
                            number=lap_number,
                            start_time=lap_start,
                            end_time=lap_end,
                        ))
                elif saved_laps > 0:
                    logger.warning(
                        "Crash-Recovery: Boot {} hat keine Lap-Details im "
                        "State – Runden werden nicht synthetisch "
                        "rekonstruiert", key)
                bs.laps = restored_laps

        # Events wiederherstellen
        self.events = []
        for evt_data in state.get("events", []):
            try:
                evt_type = EventType(evt_data["event_type"])
            except (KeyError, ValueError):
                continue
            self.events.append(RaceEvent(
                timestamp=_parse_dt(evt_data["timestamp"]) or datetime.now(),
                boot_key=evt_data.get("boot_key", ""),
                event_type=evt_type,
                valid=evt_data.get("valid", True),
                source=evt_data.get("source", "SYSTEM"),
                detail=evt_data.get("detail", ""),
            ))

        # Rückwärtskompatibilität (2026-11-10): Ältere Crash-States enthalten
        # noch kein `last_real_passage`. Es wird aus den wiederhergestellten
        # echten PASSAGE-Events abgeleitet – Korrekturen zählen NICHT.
        for key, bs in self.boats.items():
            if bs.last_real_passage is not None:
                continue
            passages = [
                event.timestamp for event in self.events
                if event.valid
                and event.event_type == EventType.PASSAGE
                and event.boot_key.upper() == key
            ]
            if passages:
                bs.last_real_passage = max(passages)

        # Klassen-Zustände wiederherstellen
        for name, cls_data in state.get("classes", {}).items():
            if name in self.classes:
                self.classes[name].finish_state = cls_data.get(
                    "finish_state", "WAITING")

        logger.info("Crash-Recovery: Phase={}, Rennen={}, {} Events restored",
                    self.phase.value, self.config.race_number, len(self.events))


__all__ = ["RaceEngine"]
