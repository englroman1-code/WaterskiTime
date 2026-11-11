"""Smoke-Tests für das GUI-Grundgerüst (Controller + RaceEngine).

Prüft, dass Fenster und Controller ohne mainloop() konstruiert werden können
(keine Layout-/Import-Fehler) und dass der AppController die RaceEngine korrekt
ansteuert (Countdown-Q8, Sperrzeit-Q1, Reset-Q4).

WICHTIG: Es wird NUR EIN Tk-Fenster über das gesamte Modul erstellt
(Module-Fixture). Mehrfaches Tk()-Erstellen und destroy() im selben Prozess
führt unter Windows zu "Can't find a usable tk.tcl" (Tk 8.6/Python 3.14).
Jeder Test stellt am Ende den Ausgangszustand wieder her (Rennen 2, PRESTART),
damit die Reihenfolge egal ist.

Hinweis: Diese Tests benötigen einen Desktop (Windows) – in headless-Umgebungen
überspringen.
"""

from __future__ import annotations

import queue
from datetime import datetime, timedelta
from pathlib import Path

import pytest

customtkinter = pytest.importorskip("customtkinter")

import json

from python.config.app_config import AppConfig as Cfg
from python.core.models import (
    BoatResult,
    Event,
    RaceConfig,
    RacePhase,
    Starter,
)
from python.excel.json_result_writer import (
    JsonResultWriter,
    JsonWriteError,
    RaceResultExport,
)
from python.gui.main_window import AppController, MainWindow
from python.logger.blackbox import BlackboxWriter
from tests.demo_data import create_demo_scenario


@pytest.fixture(scope="module")
def app(tk_window):
    """Ein Controller auf dem Session-Fenster (kein Tk-Re-Init nötig).

    Das Fenster stammt aus conftest.py (scope="session") und wird erst am
    Session-Ende zerstört – so entsteht im Prozess nur EIN Tk-Fenster.
    Demo-Daten werden explizit übergeben (AppController lädt keine Fallback-Daten).
    """
    from pathlib import Path

    # Crash-Recovery-State aus früheren Testläufen entfernen, damit der
    # Controller garantiert die übergebenen Demo-Daten lädt (Test-Isolation).
    state_file = Path.cwd() / "race_state.json"
    if state_file.exists():
        state_file.unlink()
    scenario = create_demo_scenario()
    controller = AppController(tk_window, data=scenario)
    tk_window.update_idletasks()
    yield tk_window, controller
    controller.stop_tick()                           # after()-Loop stoppen (Datei-Lock vermeiden)
    controller.on_reset(confirm=False)               # Ausgangszustand (statt destroy)


def _start_race(controller: AppController) -> None:
    """Bringt die Engine über den Countdown ins Rennen (Q8).

    1. Startet den Countdown (Play-Button)
    2. Simuliert einen abgelaufenen Countdown: countdown_end liegt in der
       Vergangenheit, der nächste Tick startet das Rennen zur echten Zeit.
    """
    controller.on_start_race()
    controller.engine.countdown_end = datetime.now() - timedelta(seconds=1)
    controller.engine.tick(datetime.now())
    assert controller.engine.phase == RacePhase.ACTIVE


def test_main_window_constructs(app) -> None:
    """Das Hauptfenster lässt sich bauen (4-Bereichs-Layout)."""
    window, _ = app
    assert window.title() != ""
    assert window.live_table is not None
    assert window.hotkeys is not None
    assert window.countdown is not None


def test_hotkey_status_and_started_keys(app) -> None:
    """Hotkey-Status (Admin) + set_started_keys (2026-09-03).

    - set_hotkey_status() zeigt den Admin-Status neben der Überschrift.
    - set_started_keys() aktiviert nur gestartete Boote (grün), nicht
      gestartete bleiben inaktiv.
    """
    window, _ = app
    # Admin-Status anzeigen (aktiv/inaktiv)
    window.hotkeys.set_hotkey_status("Hotkeys aktiv", active=True)
    assert window.hotkeys._status_label.cget("text") == "Hotkeys aktiv"
    window.hotkeys.set_hotkey_status("Hotkeys inaktiv", active=False)
    assert window.hotkeys._status_label.cget("text") == "Hotkeys inaktiv"

    # set_started_keys: nur gestartete Boote aktiv
    window.hotkeys.set_started_keys({"A", "B"})
    assert window.hotkeys._started_keys == {"A", "B"}
    # Nicht gestartete Keys bleiben inaktiv
    assert "C" not in window.hotkeys._started_keys

    # set_finished_keys: Boote beendeter Klassen werden inaktiv (2026-09-03)
    window.hotkeys.set_finished_keys({"A"})
    assert window.hotkeys._finished_keys == {"A"}
    # Gestarteter Key A ist jetzt inaktiv (grau, disabled)
    assert str(window.hotkeys._buttons["A"].cget("state")) == "disabled"
    assert window.hotkeys._buttons["A"].cget("fg_color") == "#3A3A3A"
    # Nicht beendeter gestarteter Key B bleibt aktiv (grün)
    assert str(window.hotkeys._buttons["B"].cget("state")) == "normal"
    assert window.hotkeys._buttons["B"].cget("fg_color") == Cfg.COLOR_ACTIVE


def test_app_controller_loads_demo_scenario(app) -> None:
    """Der Controller lädt das Demo-Szenario und füllt alle Panels."""
    window, controller = app

    # Rennen 2 (U18 Open) ist das Demo-Ausgangsrennen
    assert controller.scenario.selected_config.race_number == 2

    # Die RaceEngine ist geladen, Phase = RESET (wartet auf Play-Button)
    assert controller.engine.phase == RacePhase.RESET
    assert len(controller.engine.boats) > 0

    # Panels sind mit Daten befüllt
    assert window.race_end_status is not None
    assert window.log_feed is not None


def test_race_switch_updates_panels(app) -> None:
    """Rennen-Wechsel per Dropdown-Callback lädt frische Engine-Zustände (Q5)."""
    window, controller = app
    start_config = controller.scenario.selected_config
    try:
        # Auf Rennen 1 (MEN + DAMEN) wechseln
        controller._on_race_selected("Rennen 1 (DAMEN, MEN)")
        assert controller.scenario.selected_config.race_number == 1
        # Frische Engine-Zustände: alle Boote 0 Runden
        assert all(b.laps_count == 0 for b in controller.engine.boats.values())
    finally:
        controller._load_race(start_config)   # Ausgangszustand wiederherstellen
        window.update_idletasks()


def test_race_switch_after_finished_race_resets_countdown(app) -> None:
    """Bugfix 2026-09-02: Rennwechsel nach beendetem Rennen (FINISHED) muss
    die Engine auf RESET setzen – sonst bleibt die Vorstartzeit 0 und der
    PLAY-Button ist wirkungslos (User-Report: "Start drücken → nichts")."""
    window, controller = app
    start_config = controller.scenario.selected_config
    try:
        # --- Rennen 1 laden und komplett durchspielen bis FINISHED --------
        controller._on_race_selected("Rennen 1 (DAMEN, MEN)")
        _start_race(controller)
        # Renndauer ablaufen lassen → Endphase (FINISHING)
        controller.engine.race_end = datetime.now() - timedelta(seconds=1)
        controller.engine.tick(datetime.now())
        assert controller.engine.phase == RacePhase.FINISHING
        # Alle Klassen manuell beenden (2026-09-03: keine Auto-Ziellogik)
        now = datetime.now()
        for klasse in ("MEN", "DAMEN"):
            controller.engine.finish_class(klasse, now)
        assert controller.engine.phase == RacePhase.FINISHED

        # --- Wechsel zu Rennen 2 (User-Flow) ------------------------------
        controller._on_race_selected("Rennen 2 (U18)")
        assert controller.scenario.selected_config.race_number == 2
        assert controller.engine.phase == RacePhase.RESET
        assert controller.engine.countdown_end is None

        # PLAY-Button muss funktionieren (Bug: "Start drücken → nichts")
        controller.on_start_race()
        assert controller.engine.phase == RacePhase.PRESTART
        assert controller.engine.countdown_end is not None
    finally:
        controller._load_race(start_config)   # Ausgangszustand wiederherstellen
        controller.on_reset(confirm=False)
        window.update_idletasks()


def test_key_press_sets_lockout(app) -> None:
    """Hotkey-Klick setzt die Sperrzeit (App-Parameter) und loggt (Q1)."""
    window, controller = app
    try:
        _start_race(controller)
        controller.on_key_press("A")
        state = controller.engine.boats["A"]
        assert state.lockout_until is not None
        assert state.lockout_until > datetime.now()

        feed_text = window.log_feed._textbox.get("1.0", "end")
        assert "Boot A Passage" in feed_text
    finally:
        controller.on_reset(confirm=False)   # zurück in den Vorstart


def test_key_press_logs_exactly_once(app) -> None:
    """Fix 2026-08-14: Ein Hotkey-Klick erzeugt genau EINEN Log-Eintrag.

    Regression gegen das Doppel-Logging: Früher zeigte `_process_boot_key`
    das Event sofort UND der Tick holte es über `_last_event_count` nach
    (Slice ab altem Stand) – jedes Event erschien doppelt im Feed.
    """
    window, controller = app
    try:
        _start_race(controller)
        window.log_feed.clear()
        controller.on_key_press("A")
        feed_text = window.log_feed._textbox.get("1.0", "end")
        assert feed_text.count("Boot A Passage") == 1
    finally:
        controller.on_reset(confirm=False)


def test_countdown_auto_starts_race(app) -> None:
    """Q8: Play-Button startet den Countdown, nach Ablauf → ACTIVE."""
    _, controller = app
    try:
        assert controller.engine.phase == RacePhase.RESET
        _start_race(controller)
        assert controller.engine.phase == RacePhase.ACTIVE
    finally:
        controller.on_reset(confirm=False)


def test_countdown_pause_and_resume(app) -> None:
    """Q8: PAUSE friert den Countdown ein, WEITER setzt ihn fort."""
    window, controller = app
    try:
        controller.on_start_race()
        assert controller.engine.phase == RacePhase.PRESTART
        assert not controller.engine.countdown_paused

        # Pausieren → Restzeit eingefroren, Button zeigt "WEITER"
        controller.on_pause_toggle()
        assert controller.engine.countdown_paused
        assert window.countdown._pause_button.cget("text") == "WEITER"

        # Fortsetzen → Button zeigt "PAUSE", Restzeit läuft wieder
        controller.on_pause_toggle()
        assert not controller.engine.countdown_paused
        assert window.countdown._pause_button.cget("text") == "PAUSE"
    finally:
        if controller.engine.countdown_paused:
            controller.on_pause_toggle()


def test_countdown_paused_does_not_finish(app) -> None:
    """Q8: Ein pausierter Countdown startet das Rennen nicht."""
    _, controller = app
    try:
        controller.on_start_race()
        controller.on_pause_toggle()          # pausieren
        controller.engine.tick(datetime.now() + timedelta(seconds=300))
        assert controller.engine.phase == RacePhase.PRESTART  # NICHT gestartet
    finally:
        if controller.engine.countdown_paused:
            controller.on_pause_toggle()


def test_reset_restarts_countdown(app) -> None:
    """Q4/Q8: NEUSTART setzt den Countdown zurück (Rennen zurück zum Vorstart)."""
    window, controller = app
    # Erst einmal ins Rennen gehen lassen
    _start_race(controller)
    assert controller.engine.phase == RacePhase.ACTIVE

    # NEUSTART → zurück in RESET, Play-Button sichtbar
    controller.on_reset(confirm=False)
    assert controller.engine.phase == RacePhase.RESET
    # Nach Play-Button → zurück in PRESTART
    controller.on_start_race()
    assert controller.engine.phase == RacePhase.PRESTART
    assert not controller.engine.countdown_paused


def test_reset_clears_remaining_clock(app) -> None:
    """Bugfix 2026-11-09: NEUSTART setzt die rechte Uhr auf 00:00 zurück."""
    window, controller = app
    try:
        _start_race(controller)
        controller._tick()
        # Während des Rennens zeigt die rechte Uhr die verbleibende Renndauer
        assert window.countdown._race_value.cget("text") != "00:00"

        controller.on_reset(confirm=False)
        controller._tick()
        assert window.countdown._race_value.cget("text") == "00:00"
    finally:
        controller.on_reset(confirm=False)


def test_left_clock_shows_race_elapsed_after_all_lines_started(app) -> None:
    """Feature 2026-11-09: Nach allen Startreihen zeigt links die Renndauer."""
    window, controller = app
    try:
        _start_race(controller)
        # Rennen 2 startet nur in Startreihe 1 → keine weitere Reihe offen.
        # Startzeit künstlich 75 s in die Vergangenheit legen.
        past = datetime.now() - timedelta(seconds=75)
        controller.engine.race_start = past
        for state in controller.engine.boats.values():
            state.start_time = past
        controller._tick()
        assert window.countdown._prestart_title.cget("text") == "RENNDAUER:"
        assert window.countdown._prestart_value.cget("text") == "01:15"
    finally:
        controller.on_reset(confirm=False)


def test_blackbox_records_engine_events(app, tmp_path) -> None:
    """Die Blackbox protokolliert verarbeitete Engine-Events (START, PASSAGE)."""
    window, controller = app
    box_path = tmp_path / "blackbox.log"
    box = BlackboxWriter(box_path)
    try:
        controller.blackbox = box           # bestehenden Controller anhängen
        _start_race(controller)
        controller._tick()                  # START-Event nachziehen (wie in der App)
        controller.on_key_press("A")
        controller.on_reset(confirm=False)
        box.close()
        controller.blackbox = None          # Controller wieder entkoppeln

        lines = box_path.read_text(encoding="utf-8").splitlines()
        # START + STARTLINE (Reihe 1) + Passage A
        assert len(lines) == 3
        assert "EVENT: START STATUS: VALID" in lines[0]
        assert "EVENT: STARTLINE STATUS: VALID" in lines[1]
        assert "EVENT: PASSAGE STATUS: VALID" in lines[2]
        assert "TASTE: 'A'" in lines[2]
    finally:
        controller.blackbox = None
        controller.on_reset(confirm=False)


def test_input_queue_drains_to_engine(app) -> None:
    """System-Hotkeys aus der Queue werden im Tick als Passagen verarbeitet."""
    _, controller = app
    try:
        controller._input_queue = queue.Queue()   # Queue ohne echten Handler
        _start_race(controller)
        controller._input_queue.put("A")
        controller._tick()
        assert controller.engine.boats["A"].laps_count == 1
    finally:
        controller._input_queue = None
        controller.on_reset(confirm=False)


# ---------------------------------------------------------------------------
# Ergebnis-Export (Pflichtenheft §7 „Excel-Log") – läuft auf dem SELBEN
# Modul-Fenster, damit im Prozess nicht mehr als 2 Tk-Fenster entstehen
# (Tk-Stabilität, siehe Modul-Docstring). Jeder Test nutzt einen eigenen
# Controller mit export_dir=tmp_path.
# ---------------------------------------------------------------------------

def test_export_button_invokes_callback(app) -> None:
    """Klick auf den Export-Button ruft den verdrahteten Callback auf."""
    window, _ = app
    calls: list[int] = []
    window.header.set_export_callback(lambda: calls.append(1))
    window.header._on_export_clicked()
    assert calls == [1]


def test_export_creates_json_with_meta(app, tmp_path) -> None:
    """on_export_results() schreibt eine Ergebnisdatei mit allen fertigen Rennen."""
    window, _ = app
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        # Rennen 2 (U18) durchspielen und beenden → finished_races gefüllt
        _start_race(controller)
        controller.engine.finish_class("U18", datetime.now())
        assert controller.engine.phase == RacePhase.FINISHED

        controller.on_export_results()

        files = list(tmp_path.glob("RESULT_*.json"))
        assert len(files) == 1

        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert "event" in data
        assert "races" in data
        assert len(data["races"]) == 1
        assert data["races"][0]["race_number"] == 2
        assert "classes" in data["races"][0]
        assert "log" in data["races"][0]
    finally:
        controller.stop_tick()  # Tick-Loop sauber beenden
        controller.on_reset(confirm=False)


def test_export_success_updates_status_label(app, tmp_path) -> None:
    """Nach erfolgreichem Export zeigt das Status-Label den Dateinamen (grün)."""
    window, _ = app
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        _start_race(controller)
        controller.engine.finish_class("U18", datetime.now())

        controller.on_export_results()

        label = window.header._export_status
        assert label.cget("text").startswith("Gespeichert: RESULT_")
        assert label.cget("text_color") == Cfg.COLOR_ACTIVE     # Erfolg = grün
    finally:
        controller.stop_tick()  # Tick-Loop sauber beenden
        controller.on_reset(confirm=False)


def test_export_error_shows_red_status(app, tmp_path, monkeypatch) -> None:
    """Fehler beim Schreiben (z. B. Datei gesperrt) → rote Status-Meldung."""
    window, _ = app

    def fake_write(self, path, exports, event=None) -> Path:
        raise JsonWriteError("Datei gesperrt (Test)")

    monkeypatch.setattr(JsonResultWriter, "write_all_races", fake_write)
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        _start_race(controller)
        controller.engine.finish_class("U18", datetime.now())

        controller.on_export_results()

        label = window.header._export_status
        assert label.cget("text") == "Datei gesperrt (Test)"
        assert label.cget("text_color") == Cfg.COLOR_ERROR      # Fehler = rot
    finally:
        controller.stop_tick()  # Tick-Loop sauber beenden
        controller.on_reset(confirm=False)


def test_race_switch_resets_export_status(app, tmp_path) -> None:
    """Nach dem Export zeigt ein Renn-Wechsel wieder „Noch kein Export"."""
    window, _ = app
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        _start_race(controller)
        controller.engine.finish_class("U18", datetime.now())
        controller.on_export_results()
        assert window.header._export_status.cget("text") \
            .startswith("Gespeichert:")

        controller._load_race(controller.scenario.race_configs[0])
        assert window.header._export_status.cget("text") \
            == "Noch kein Export"
    finally:
        controller.stop_tick()  # Tick-Loop sauber beenden
        controller.on_reset(confirm=False)


def test_write_all_races_groups_by_race_and_class(tmp_path) -> None:
    """write_all_races() gruppiert Ergebnisse nach Rennen und Klasse (2026-09-03).

    Option 1: Der Export enthält ALLE fertigen Rennen, sortiert nach
    Rennnummer, und innerhalb jedes Rennens die Ergebnisse nach Klasse
    gruppiert (Kundenwunsch: "Rennen 1 Klasse Herren: ...").
    """
    event = Event(title="ÖM Ybbs 2026", date="2026-08-14", organizer="ÖSV")

    def _starter(key: str, klasse: str, race_number: int) -> Starter:
        return Starter(boot_key=key, boat_number=key, skier=f"Boot {key}",
                       klasse=klasse, race_number=race_number, startreihe=1)

    def _result(starter: Starter, laps: int, place: int) -> BoatResult:
        return BoatResult(starter=starter, laps_count=laps,
                          total_time=timedelta(seconds=place * 10),
                          best_lap=timedelta(seconds=5), place=place)

    # Rennen 2 (zwei Klassen) – wird absichtlich VOR Rennen 1 übergeben,
    # um die Sortierung nach Rennnummer zu prüfen
    export_2 = RaceResultExport(
        event=event,
        config=RaceConfig(race_number=2, race_duration_min=12,
                          start_interval_s=7, grid_time_s=10),
        results=[
            _result(_starter("A", "MEN", 2), 3, 1),
            _result(_starter("B", "MEN", 2), 2, 2),
            _result(_starter("C", "DAMEN", 2), 4, 1),
        ],
    )
    # Rennen 1 (eine Klasse)
    export_1 = RaceResultExport(
        event=event,
        config=RaceConfig(race_number=1, race_duration_min=10,
                          start_interval_s=20, grid_time_s=15),
        results=[
            _result(_starter("D", "JUN", 1), 5, 1),
        ],
    )

    out = tmp_path / "RESULT_test.json"
    JsonResultWriter().write_all_races(out, [export_2, export_1])

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["event"]["title"] == "ÖM Ybbs 2026"

    # Sortierung nach Rennnummer (1 vor 2), unabhängig von Übergabe-Reihenfolge
    races = data["races"]
    assert [r["race_number"] for r in races] == [1, 2]

    # Rennen 1: eine Klasse "JUN" mit einem Ergebnis
    assert races[0]["classes"][0]["klasse"] == "JUN"
    assert races[0]["classes"][0]["results"][0]["place"] == 1

    # Rennen 2: zwei Klassen, gruppiert nach Klasse
    klasse_list = [c["klasse"] for c in races[1]["classes"]]
    assert set(klasse_list) == {"MEN", "DAMEN"}
    men = next(c for c in races[1]["classes"] if c["klasse"] == "MEN")
    assert [r["boat_nr"] for r in men["results"]] == ["A", "B"]
    assert [r["place"] for r in men["results"]] == [1, 2]


def test_export_button_always_enabled(app) -> None:
    """Export-Button ist immer aktiv (2026-09-03).

    Der Export enthält ALLE fertigen Rennen auf einmal – er ist damit
    unabhängig vom aktuellen Rennen. Auch ohne beendetes Rennen ist er
    klickbar (exportiert dann nur die Stammdaten).
    """
    window, controller = app
    # Ohne beendetes Rennen (Phase RESET) muss der Button aktiv sein
    assert window.header._export_button.cget("state") == "normal"


def test_export_without_finished_race_writes_stammdaten(app, tmp_path) -> None:
    """Export ohne beendetes Rennen erzeugt Datei mit nur Stammdaten (2026-09-03).

    Wenn noch kein Rennen beendet ist, wird eine Datei mit dem Event und
    leerer races-Liste geschrieben (keine Fehlermeldung).
    """
    window, _ = app
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        # Kein Rennen beendet → Export erzeugt Datei mit nur Stammdaten
        controller.on_export_results()

        files = list(tmp_path.glob("RESULT_*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["event"]["title"] == scenario.event.title
        assert data["races"] == []
        label = window.header._export_status
        assert label.cget("text").startswith("Gespeichert: RESULT_")
    finally:
        controller.stop_tick()
        controller.on_reset(confirm=False)


def test_start_button_disabled_for_finished_race(app, tmp_path) -> None:
    """Start-Button ist deaktiviert, wenn ein beendetes Rennen geladen wird (2026-09-03).

    Beim Zurückwechseln zu einem bereits beendeten Rennen (Ergebnisse
    wiederhergestellt) ist kein Start mehr möglich – der Button ist grau.
    """
    window, _ = app
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        # Rennen 2 (U18) durchspielen und beenden → finished_races gefüllt
        _start_race(controller)
        controller.engine.finish_class("U18", datetime.now())
        assert controller.engine.phase == RacePhase.FINISHED

        # Zu Rennen 1 wechseln (nicht beendet) → Start aktiv
        controller._load_race(controller.scenario.race_configs[0])
        assert window.countdown._start_button.cget("state") == "normal"

        # Zurück zu Rennen 2 (beendet) → Start deaktiviert
        controller._load_race(controller.scenario.race_configs[1])
        assert window.countdown._start_button.cget("state") == "disabled"
    finally:
        controller.stop_tick()
        controller.on_reset(confirm=False)


# ---------------------------------------------------------------------------
# Header: Refresh-Button + Datenquellen-Anzeige (§4)
# ---------------------------------------------------------------------------

def test_header_shows_data_source(app) -> None:
    """Der Header zeigt die aktuelle Datenquelle an."""
    window, controller = app
    source_text = window.header._source_label.cget("text")
    assert "Datenquelle:" in source_text


def test_refresh_button_disabled_during_race(app) -> None:
    """Refresh-Button ist deaktiviert wenn Rennen läuft."""
    window, controller = app
    try:
        # IMMER in RESET bringen – unabhängig vom Vorzustand
        controller.on_reset(confirm=False)
        assert controller.engine.phase == RacePhase.RESET, \
            f"Reset fehlgeschlagen: {controller.engine.phase}"
        controller.on_start_race()
        assert controller.engine.phase == RacePhase.PRESTART
        state = window.header._refresh_button.cget("state")
        assert state == "disabled", f"Button state={state}"
    finally:
        controller.on_reset(confirm=False)


def test_refresh_button_enabled_in_reset(app) -> None:
    """Refresh-Button ist aktiv wenn kein Rennen läuft (Phase RESET)."""
    window, controller = app
    assert window.header._refresh_button.cget("state") == "normal"


def test_refresh_with_demo_source_does_nothing(app) -> None:
    """Refresh mit Demo-Daten (kein Datei-Pfad) → Feed-Meldung."""
    window, controller = app
    controller.on_refresh_data()
    # Demo-Daten haben keinen Datei-Pfad → Feed-Meldung "nicht möglich"
    feed_text = window.log_feed._textbox.get("1.0", "end")
    assert "Refresh nicht möglich" in feed_text


def test_validation_blocks_start_with_invalid_data(app, tmp_path) -> None:
    """Ungültige Daten → on_start_race() blockiert und zeigt Warnung."""
    from unittest.mock import patch
    window, _ = app
    scenario = create_demo_scenario()
    controller = AppController(window, data=scenario, export_dir=tmp_path)
    try:
        # Ungültig machen
        original_title = controller.scenario.event.title
        controller.scenario.event.title = ""
        with patch("tkinter.messagebox.showwarning") as mock_warn:
            controller.on_start_race()
            assert mock_warn.called, "showwarning nicht aufgerufen"
        assert controller.engine.phase == RacePhase.RESET  # nicht gestartet
    finally:
        controller.scenario.event.title = original_title
        controller.stop_tick()  # Tick-Loop sauber beenden
        controller.on_reset(confirm=False)


# ---------------------------------------------------------------------------
# Kundenanforderungen 2026-09-03: Geschw.-Spalte, Runner-Abschneidung,
# Beenden-Button erst nach Rennende aktiv
# ---------------------------------------------------------------------------

def test_live_table_format_speed(tk_window) -> None:
    """_format_speed liefert 'letzte Runde / gesamt' (oder '–' bei fehlenden Werten)."""
    from datetime import datetime, timedelta

    from python.core.models import BoatState, Lap, Starter
    from python.gui.panels import LiveTablePanel

    panel = LiveTablePanel(tk_window)
    panel.set_lap_lengths(2000, 3500)
    start = datetime(2026, 6, 17, 14, 30, 0)

    # Ohne Runden → "–/–"
    empty = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
    assert panel._format_speed(empty) == "–/–"

    # Eine Runde (2000 m in 100 s = 72 km/h), kein last_passage → "72.0/–"
    one = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
    one.laps.append(Lap(1, start, start + timedelta(seconds=100)))
    assert panel._format_speed(one) == "72.0/–"

    # Zwei Runden + last_passage → "126.0/99.0"
    two = BoatState(starter=Starter(boot_key="A", skier="S. Huber", klasse="U18"))
    two.start_time = start
    two.laps.append(Lap(1, start, start + timedelta(seconds=100)))
    two.laps.append(Lap(2, start + timedelta(seconds=100),
                        start + timedelta(seconds=200)))
    two.last_passage = start + timedelta(seconds=200)
    assert panel._format_speed(two) == "126.0/99.0"


def test_live_table_truncates_runner_name(tk_window) -> None:
    """Zu lange Runner-Namen werden auf RUNNER_MAX_CHARS gekürzt (mit '…')."""
    from python.gui.panels import LiveTablePanel

    panel = LiveTablePanel(tk_window)
    long_name = "X" * 40
    truncated = panel._truncate_runner(long_name)
    assert len(truncated) <= LiveTablePanel.RUNNER_MAX_CHARS
    assert truncated.endswith("…")
    # Kurzer Name bleibt unverändert
    assert panel._truncate_runner("Kurz") == "Kurz"


def test_live_table_runner_shows_boat_and_team_without_class(tk_window) -> None:
    """Runner-Spalte: Boot-Nr + Team; die Klasse steht nur in ihrer Spalte."""
    from python.core.models import BoatState, Starter
    from python.gui.panels import LiveTablePanel

    panel = LiveTablePanel(tk_window)
    state = BoatState(starter=Starter(
        boot_key="A", boat_number="101", skier="S. Huber",
        klasse="U18", team="Team X"))
    panel.update_boats({"A": state}, datetime.now())

    row = panel._rows["A"]
    assert row.labels[1].cget("text") == "101 Team X"
    assert "U18" not in row.labels[1].cget("text")
    assert row.labels[2].cget("text") == "U18"


def test_live_table_status_dot_after_race_end(tk_window) -> None:
    """Ampel: grüner/roter Punkt direkt neben dem Status (nach Rennende)."""
    from python.core.models import BoatState, Starter
    from python.gui.panels import LiveTablePanel

    panel = LiveTablePanel(tk_window)
    boats = {
        "A": BoatState(starter=Starter(boot_key="A", boat_number="101")),
        "B": BoatState(starter=Starter(boot_key="B", boat_number="102")),
    }
    now = datetime.now()

    panel.update_boats(boats, now)
    assert panel._rows["A"].status_dot.cget("text") == ""   # vor Rennende

    panel.update_boats(boats, now, {"A": True, "B": False})
    assert panel._rows["A"].status_dot.cget("text") == "●"
    assert panel._rows["A"].status_dot.cget("text_color") == Cfg.COLOR_ACTIVE
    assert panel._rows["B"].status_dot.cget("text_color") == Cfg.COLOR_ERROR


def test_hotkey_panel_letter_follows_race_end_dot(tk_window) -> None:
    """Klickbare Hotkey-Taste: rot bei rotem Punkt, weiß bei grünem Punkt."""
    from python.gui.panels import HotkeyPanel

    panel = HotkeyPanel(tk_window)
    panel.set_starters([
        Starter(boot_key="A", boat_number="101"),
        Starter(boot_key="B", boat_number="102"),
    ])
    panel.set_started_keys({"A", "B"})

    # Vor Rennende: weiße Schrift auf grüner Taste.
    assert panel._buttons["A"].cget("text_color") == Cfg.COLOR_TEXT
    assert panel._buttons["B"].cget("text_color") == Cfg.COLOR_TEXT

    # Nach Rennende: A im Ziel (grün) → weiß, B offen (rot) → rot.
    panel.set_crossed_keys({"A": True, "B": False})
    assert panel._buttons["A"].cget("text_color") == Cfg.COLOR_TEXT
    assert panel._buttons["B"].cget("text_color") == Cfg.COLOR_ERROR
    # Die rote Taste bleibt klickbar und grün hinterlegt.
    assert panel._buttons["B"].cget("state") == "normal"
    assert panel._buttons["B"].cget("fg_color") == Cfg.COLOR_ACTIVE

    # B kreuzt später: Punkt grün, Schrift wieder weiß.
    panel.set_crossed_keys({"A": True, "B": True})
    assert panel._buttons["B"].cget("text_color") == Cfg.COLOR_TEXT

    # Rennen zurückgesetzt: Ampel aus, normale Schrift.
    panel.set_crossed_keys(None)
    assert panel._buttons["B"].cget("text_color") == Cfg.COLOR_TEXT

    # Beendete Klasse bleibt grau/deaktiviert (Ampel überschreibt nicht).
    panel.set_crossed_keys({"A": True, "B": False})
    panel.set_finished_keys({"B"})
    assert panel._buttons["B"].cget("text_color") == "#666666"
    assert panel._buttons["B"].cget("state") == "disabled"


def test_rennenende_ampel_im_controller_tick(app) -> None:
    """Integration: Der Tick füllt die Ampel (grün/rot) in der Live-Tabelle."""
    window, controller = app
    start_config = controller.scenario.selected_config
    try:
        # Rennen 1 kann von früheren Tests bereits beendet sein (die
        # Ergebnisse bleiben im Speicher). Für diesen Test brauchen wir ein
        # frisches Rennen – sonst sind die Boote schon `finished_at`.
        controller.engine.finished_races.pop(1, None)
        controller._on_race_selected("Rennen 1 (DAMEN, MEN)")
        _start_race(controller)

        # Rennzeit abgelaufen → Endphase
        controller.engine.race_end = datetime.now() - timedelta(seconds=1)
        controller._tick()
        assert controller.engine.phase == RacePhase.FINISHING

        # Ein MEN-Boot passiert nach Rennende die Ziellinie
        controller.engine.handle_key_press("E", datetime.now())
        controller._tick()

        panel = window.race_end_status
        assert panel._boat_status.get("MEN")
        assert panel._count_labels["MEN"].cget("text") == "1/2"
        assert panel._finish_buttons["MEN"].cget("fg_color") == Cfg.COLOR_ERROR

        # Die Punkte stehen neben dem Statustext in der Live-Tabelle
        live = window.live_table
        assert live._rows["E"].status_dot.cget("text") == "●"
        assert live._rows["E"].status_dot.cget("text_color") == Cfg.COLOR_ACTIVE
        assert live._rows["G"].status_dot.cget("text_color") == Cfg.COLOR_ERROR
    finally:
        controller._load_race(start_config)
        window.update_idletasks()


def test_finish_button_disabled_before_race_over(tk_window) -> None:
    """Beenden-Button ist vor Rennende sichtbar, aber inaktiv (grau)."""
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    panel.update_classes({"MEN": RaceClass("MEN"), "DAMEN": RaceClass("DAMEN")})
    button = panel._finish_buttons["MEN"]
    # Vor Rennende: disabled
    assert str(button.cget("state")) == "disabled"
    assert button.cget("fg_color") == "#3A3A3A"


def test_finish_button_enabled_after_race_over(tk_window) -> None:
    """Beenden-Button wird nach Rennende aktiv (gelb), solange Klasse offen."""
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    panel.update_classes({"MEN": RaceClass("MEN"), "DAMEN": RaceClass("DAMEN")})
    panel.set_race_over(True)
    button = panel._finish_buttons["MEN"]
    assert str(button.cget("state")) == "normal"
    assert button.cget("fg_color") == Cfg.COLOR_WARNING


def test_finish_button_disabled_again_when_class_closed(tk_window) -> None:
    """Beenden-Button wird wieder inaktiv, sobald die Klasse CLOSED ist."""
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    panel.update_classes({"MEN": RaceClass("MEN")})
    panel.set_race_over(True)
    # Klasse als FERTIG markieren (CLOSED)
    panel.update_states({"MEN": "CLOSED"})
    button = panel._finish_buttons["MEN"]
    assert str(button.cget("state")) == "disabled"
    assert button.cget("fg_color") == "#3A3A3A"


def test_finish_button_green_when_all_boats_crossed(tk_window) -> None:
    """Rennende-Ampel: sind alle Boote im Ziel, wird der Button grün."""
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    panel.update_classes({"MEN": RaceClass("MEN")})
    panel.set_race_over(True)
    panel.update_states({"MEN": "WAITING"},
                        {"MEN": [("A", True), ("B", True)]})

    button = panel._finish_buttons["MEN"]
    assert str(button.cget("state")) == "normal"
    assert button.cget("fg_color") == Cfg.COLOR_ACTIVE
    assert panel._count_labels["MEN"].cget("text") == "2/2"


def test_finish_button_red_when_one_boat_missing(tk_window) -> None:
    """Rennende-Ampel: fehlt ein Boot, wird der Button rot – bleibt aber aktiv."""
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    panel.update_classes({"MEN": RaceClass("MEN")})
    panel.set_race_over(True)
    panel.update_states({"MEN": "WAITING"},
                        {"MEN": [("A", True), ("B", False)]})

    button = panel._finish_buttons["MEN"]
    assert str(button.cget("state")) == "normal"   # Kundenwunsch: nicht verbieten
    assert button.cget("fg_color") == Cfg.COLOR_ERROR
    assert panel._count_labels["MEN"].cget("text") == "1/2"


def test_finish_button_disabled_when_closed_with_red_boats(tk_window) -> None:
    """Nach dem Beenden bleibt die Ampel sichtbar, der Button ist aber grau."""
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    panel.update_classes({"MEN": RaceClass("MEN")})
    panel.set_race_over(True)
    panel.update_states({"MEN": "CLOSED"},
                        {"MEN": [("A", False)]})

    button = panel._finish_buttons["MEN"]
    assert str(button.cget("state")) == "disabled"
    assert button.cget("fg_color") == "#3A3A3A"
    assert panel._count_labels["MEN"].cget("text") == "0/1"


def test_race_end_status_no_empty_line_when_classes_loaded(tk_window) -> None:
    """Keine Leerzeile unter 'Rennende-Status', wenn Klassen geladen sind.

    Kundenanforderung (2026-09-03): Das Info-Label ("Keine Klassen geladen")
    wird nur gepackt, wenn wirklich keine Klassen vorhanden sind – sonst
    entsteht eine unnötige Leerzeile unter der Überschrift.
    """
    from python.core.models import RaceClass
    from python.gui.panels import RaceEndStatusPanel

    panel = RaceEndStatusPanel(tk_window)
    # Mit Klassen: Info-Label wird NICHT gepackt (kein Platzverbrauch)
    panel.update_classes({"MEN": RaceClass("MEN")})
    assert panel._info.winfo_manager() != "pack", \
        "Info-Label darf bei geladenen Klassen nicht gepackt sein"

    # Ohne Klassen: Info-Label wird gepackt (Hinweis sichtbar)
    panel.update_classes({})
    assert panel._info.winfo_manager() == "pack", \
        "Info-Label muss ohne Klassen gepackt sein"
