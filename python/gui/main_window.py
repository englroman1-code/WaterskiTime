"""Hauptfenster und App-Controller des Zeitnehmungs-Systems.

Aufbau:
    MainWindow   – 4-Bereichs-Layout nach 05_a_GUI_Description.txt (Grid)
    AppController – verbindet Panels mit der RaceEngine (Kernlogik), treibt
                    die Anzeige per after()-Timer (ADR-007: Polling im
                    Main-Thread, keine Threads).

Datenquelle (Lade-Kette, siehe Manual.md):
    1. race_state.json → Crash-Recovery (sofort weiter, keine Nachfrage!)
    2. IMPORT.json → vom VBA-Makro erzeugt
    3. Excel + VBA-Makro → Makro aufrufen → IMPORT.json → laden
    4. Nichts davon → Fehlermeldung "Keine Renndaten gefunden"
"""

from __future__ import annotations

import hashlib
import queue
import sys
import traceback
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from python.config.app_config import (
    AppConfig as Cfg,
    get_runtime_dir,
    get_settings,
)
from python.config.version import APP_TITLE, VERSION
from python.core.data_validator import validate_scenario
from python.core.input_handler import HotkeyMapping, InputHandler
from python.core.race_data import RaceData
from python.core.models import (
    EventType,
    RaceConfig,
    RaceEvent,
    RacePhase,
)
from python.core.race_engine import RaceEngine
from python.core.race_state_manager import RaceStateManager
from python.excel.json_result_writer import (
    JsonResultWriter,
    JsonWriteError,
    RaceResultExport,
)
from python.excel.json_race_store import JsonRaceStore, JsonReadError
from python.excel.vba_macro_caller import VbaMacroCaller, VbaMacroError
from python.gui.panels import (
    CountdownPanel,
    HeaderPanel,
    HotkeyPanel,
    LiveTablePanel,
    LogFeedPanel,
    ManualCorrectionPanel,
    RaceEndStatusPanel,
    RaceInfoPanel,
)
from python.logger.app_logger import log_progress, logger
from python.logger.blackbox import BlackboxWriter

# --- Workaround (wichtig, nicht entfernen!) ---------------------------------
# CustomTkinter's `_windows_set_titlebar_color()` (Windows-Titelbar-Manipulation)
# enthält zwei logische Bugs (Tautologie mit `or` statt `and`), wodurch das
# Fenster mit `withdraw()` versteckt und die mainloop mit
# "can't invoke wm command: application has been destroyed" crasht
# (reproduziert mit Python 3.14 + Tk 8.6). Der offizielle Schalter deaktiviert
# die Titelbar-Manipulation komplett – das Fenster bleibt dadurch normal sichtbar.
ctk.CTk._deactivate_windows_window_header_manipulation = True


class MainWindow(ctk.CTk):
    """Hauptfenster: dunkles 4-Bereichs-Layout (Grid, responsiv).

    Layout-Struktur (responsiv, 2 Spalten):
        Äußeres Grid: 2 Spalten (weight 5:2) – passt sich an Bildschirmgröße an.

        Linke Spalte (left_col):
            row=0: RaceInfoPanel      (fix高度, kompakt)
            row=1: LogFeedPanel       (fix 7 Zeilen)
            row=2: LiveTablePanel     (weight=1 → RESTLICHER PLATZ)

        Rechte Spalte (right_col):
            row=0: CountdownPanel     (fix高度)
            row=1: HotkeyPanel        (fix高度, KOMPAKT ohne Export)
            row=2: RaceEndStatusPanel (weight=1 → dehnt sich)
            row=3: ManualCorrectionPanel (weight=1 → dehnt sich)

        Fußzeile: unteres Band (Datenquelle + Branding)
    """

    def __init__(self) -> None:
        """MainWindow initialisieren (Fenster, Layout, Panels)."""
        super().__init__(fg_color=Cfg.COLOR_BG)

        self.title(APP_TITLE)
        self.geometry(f"{Cfg.WINDOW_WIDTH}x{Cfg.WINDOW_HEIGHT}")
        self.minsize(1280, 800)

        # Äußeres Grid: 2 Spalten (5:2) – responsiv
        self.grid_columnconfigure(0, weight=5, uniform="main")
        self.grid_columnconfigure(1, weight=2, uniform="main")
        self.grid_rowconfigure(1, weight=1)  # Hauptbereich dehnt sich vertikal

        # Bereich 1: Kopf (spannt beide Spalten, fix高度)
        log_progress("Panel 1/4: Header", step=1, total=4)
        self.header = HeaderPanel(self, version=f"v{VERSION}")
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # --- Linke Spalte: RaceInfo + LogFeed + LiveTable ---------------------
        log_progress("Panel 2/4: Linke Spalte", step=2, total=4)
        self._left_col = ctk.CTkFrame(self, fg_color="transparent")
        self._left_col.grid(row=1, column=0, sticky="nsew",
                            padx=(12, 6), pady=6)
        self._left_col.grid_columnconfigure(0, weight=1)
        self._left_col.grid_rowconfigure(0, weight=0)  # RaceInfo: fix
        self._left_col.grid_rowconfigure(1, weight=0)  # LogFeed: fix (7 Zeilen)
        self._left_col.grid_rowconfigure(2, weight=1)  # LiveTable: REST

        self.race_info = RaceInfoPanel(self._left_col)
        self.race_info.grid(row=0, column=0, sticky="ew")

        self.log_feed = LogFeedPanel(self._left_col, visible_lines=7)
        self.log_feed.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.live_table = LiveTablePanel(self._left_col)
        self.live_table.grid(row=2, column=0, sticky="nsew", pady=(6, 0))

        # --- Rechte Spalte: Countdown + Hotkeys + Status + Manuell ------------
        log_progress("Panel 2/4: Rechte Spalte", step=2, total=4)
        self._right_col = ctk.CTkFrame(self, fg_color="transparent")
        self._right_col.grid(row=1, column=1, sticky="nsew",
                             padx=(6, 12), pady=6)
        self._right_col.grid_columnconfigure(0, weight=1)
        self._right_col.grid_rowconfigure(0, weight=0)  # Countdown: fix
        self._right_col.grid_rowconfigure(1, weight=0)  # Hotkeys: fix
        self._right_col.grid_rowconfigure(2, weight=1)  # RaceEnd: dehnt sich
        self._right_col.grid_rowconfigure(3, weight=1)  # Manual: dehnt sich

        self.countdown = CountdownPanel(self._right_col)
        self.countdown.grid(row=0, column=0, sticky="ew")

        self.hotkeys = HotkeyPanel(self._right_col)
        self.hotkeys.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.race_end_status = RaceEndStatusPanel(self._right_col)
        self.race_end_status.grid(row=2, column=0, sticky="nsew", pady=(6, 0))

        self.manual_correction = ManualCorrectionPanel(self._right_col)
        self.manual_correction.grid(row=3, column=0, sticky="nsew", pady=(6, 0))

        # Fußzeile
        self._build_footer()
        logger.info("MainWindow: alle Panels erstellt")

    def report_callback_exception(self, exc, val, tb) -> None:
        """Fängt Fehler aus Tk-Callbacks (after/Button) und schreibt sie ins Log.

        Ohne diesen Hook werden solche Fehler nur stumm verschluckt –
        genau das macht die Fehlersuche schwer, wenn ein Fenster hängt.
        """
        logger.error(f"Tk-Callback-Fehler: {exc}: {val}\n"
                     f"{''.join(traceback.format_tb(tb))}")


    def _build_footer(self) -> None:
        """Fußzeile: Datenquelle links, Branding mitte/rechts (GUI-Description)."""
        footer = ctk.CTkFrame(self, fg_color=Cfg.COLOR_BG, corner_radius=0)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        footer.grid_columnconfigure(1, weight=1)

        self.footer_source = ctk.CTkLabel(footer, text="Datenquelle: –",
                                          font=("Segoe UI", 11),
                                          text_color=Cfg.COLOR_TEXT_SECONDARY)
        self.footer_source.grid(row=0, column=0, sticky="w", padx=16)

        ctk.CTkLabel(footer,
                     text=f"{Cfg.BRANDING_NAME} | {Cfg.BRANDING_URL} | {Cfg.BRANDING_EMAIL}",
                     font=("Segoe UI", 11),
                     text_color=Cfg.COLOR_TEXT_SECONDARY).grid(row=0, column=2,
                                                               sticky="e", padx=16)


class AppController:
    """Verbinder zwischen RaceEngine (Kernlogik) und GUI-Panels.

    Verantwortlich:
        - lädt das Szenario und verteilt die Daten auf die Panels
        - Rennen-Auswahl per Dropdown (Q5) → RaceEngine neu laden
        - after()-Tick: engine.tick() + Tabellen-Refresh (ADR-007)
        - Hotkey-/Korrektur-/Countdown-Callbacks → RaceEngine
    """

    def __init__(self, window: MainWindow,
                 data: RaceData | None = None,
                 blackbox_path: str | None = None,
                 enable_keyboard: bool = False,
                 export_dir: str | Path | None = None,
                 excel_path: str | Path | None = None,
                 json_path: str | Path | None = None,
                 is_admin: bool = False) -> None:
        """AppController initialisieren.

        Lade-Kette (Manual.md):
            1. race_state.json → Crash-Recovery (sofort weiter!)
            2. json_path (IMPORT.json) → direkt laden
            3. excel_path → VBA-Makro aufrufen → laden
            4. Nichts davon → Fehlermeldung

        Args:
            window: das Hauptfenster (MainWindow).
            data: vorab geladene Renndaten (nur für Tests); None.
            blackbox_path: Zielpfad der Blackbox (append-only);
                           None → Blackbox deaktiviert.
            enable_keyboard: systemweite Hotkey-Erfassung aktivieren.
            export_dir: Zielordner für Excel-Ergebnis-Exporte.
            excel_path: Pfad zur Excel-Datei (Named Ranges).
            json_path: Pfad zur IMPORT.json (vom VBA-Makro erzeugt).
            is_admin: True wenn die App mit Administrator-Rechten läuft
                      (für die Hotkey-Status-Anzeige, 2026-09-03).
        """
        self.window = window
        self.settings = get_settings()
        self.engine = RaceEngine()
        self.blackbox: BlackboxWriter | None = None
        self._input_queue: queue.Queue | None = None
        self._input_handler: InputHandler | None = None
        self._tick_after_id: str | None = None  # after()-ID zum Stoppen
        self._tick_running: bool = False  # False → Tick-Loop beendet
        self._last_event_count: int = 0
        self._race_total_seconds: float = 0.0
        self._last_phase: RacePhase | None = RacePhase.PRESTART
        self._export_dir = Path(export_dir) if export_dir is not None \
            else self._default_export_dir()
        self._export_dir.mkdir(parents=True, exist_ok=True)

        # Crash-Recovery: StateManager prüft race_state.json
        self._state_manager = RaceStateManager()
        self._saved_state: dict | None = None  # für Crash-Recovery

        # Refresh-Pfad: Original-Quelle für Neuladen merken
        self._source_path: str | Path | None = None
        self._source_type: str = "unbekannt"  # "json" | "excel" | "crash"

        # Datenquelle: Lade-Kette (Manual.md)
        self.scenario = None
        self._data_source = "unbekannt"
        self._load_data(json_path, excel_path, data)
        # Crash-Recovery-State gegen die tatsächlich geladene Quelle prüfen
        # (Rennnummer + Fingerprint). Ein alter/fremder State wird verworfen.
        self._validate_saved_state()

        logger.info("AppController: initialisiere ...")
        # Blackbox (Beweis-Protokoll): append-only TXT, thread-sicher
        if blackbox_path is not None:
            self.blackbox = BlackboxWriter(blackbox_path)
            logger.info("AppController: Blackbox aktiv -> {}", blackbox_path)
        # Q8: Kein eigenes Startsignal – der Countdown startet das Rennen.
        # PAUSE/WEITER + NEUSTART steuern den Countdown der Engine.
        self.window.countdown.set_callbacks(
            self.on_pause_toggle, self.on_reset, self.on_start_race)
        self.window.hotkeys.set_on_key(self.on_key_press)
        self.window.manual_correction.set_on_correct(self.on_manual_correction)
        self.window.race_end_status.set_on_finish_class(self.on_finish_class)

        # Refresh-Button: Datenquelle anzeigen + Neuladen (§4)
        self.window.header.set_source(self._data_source)
        self.window.header.set_refresh_callback(self.on_refresh_data)
        # Export-Button: Ergebnis-Export (§7), Button wird nach Rennen aktiv
        self.window.header.set_export_callback(self.on_export_results)
        self.window.header.set_export_status("")

        self._setup_race_selector()
        self._load_race(self.scenario.selected_config)
        # Systemweite Hotkey-Erfassung (sofortiger Rohdruck in die Blackbox)
        if enable_keyboard:
            if self.blackbox is None:
                raise ValueError("enable_keyboard benötigt blackbox_path")
            self._input_queue = queue.Queue()
            mapping = HotkeyMapping.from_starters(list(self.engine.boats.keys()))
            self._input_handler = InputHandler(self._input_queue, mapping,
                                               self.blackbox)
            self._input_handler.start()
            logger.info("AppController: systemweite Hotkeys aktiv (Admin nötig)")
        # Hotkey-Status anzeigen (Admin-Rechte, 2026-09-03): informativ bei
        # der Überschrift "Tastaturbedienung", ob Hotkeys aktiv oder inaktiv.
        if enable_keyboard:
            self.window.hotkeys.set_hotkey_status("Hotkeys aktiv", active=True)
        elif is_admin:
            self.window.hotkeys.set_hotkey_status(
                "Hotkeys inaktiv (Admin, aber deaktiviert)", active=False)
        else:
            self.window.hotkeys.set_hotkey_status(
                "Hotkeys inaktiv (keine Admin-Rechte)", active=False)
        self._start_tick()
        logger.info("AppController: fertig – Rennen {} geladen",
                    self.scenario.selected_config.race_number)

    # ------------------------------------------------------------------
    # Setup – Lade-Kette (Manual.md)
    # ------------------------------------------------------------------

    def _load_data(self, json_path: str | Path | None,
                   excel_path: str | Path | None,
                   data: RaceData | None) -> None:
        """Lädt Renndaten über die Lade-Kette (Manual.md, ADR-009).

        Reihenfolge:
            1. race_state.json → Crash-Recovery (sofort weiter!)
            2. json_path (--json) → direkt laden
            3. excel_path (--excel) → VBA-Makro aufrufen → IMPORT.json → laden
            4. data (Tests) → wenn übergeben, sofort laden
            5. Auto-Suche im Arbeitsverzeichnis: IMPORT.json, dann *.xlsm/*.xlsx
               (Excel: VBA-Makro aufrufen → IMPORT.json erzeugen → laden)
               → Bestätigungsdialog gemäß Pflichtenheft §4
            6. Nichts → Fehlermeldung

        Args:
            json_path: Pfad zur IMPORT.json.
            excel_path: Pfad zur Excel-Datei (VBA-Makro wird aufgerufen).
            data: vorab geladene Renndaten (nur für Tests).
        """
        import tkinter.messagebox as messagebox

        # 1. Crash-Recovery: race_state.json?
        saved_state = None
        if self._state_manager.exists():
            saved_state = self._state_manager.load()
            if saved_state is None:
                # Datei vorhanden, aber ungültig/zu alt/falsches Schema:
                # nicht liegen lassen, sonst wird sie bei jedem Start erneut
                # geprüft und verworfen.
                logger.warning(
                    "Crash-Recovery: vorhandener State ist ungültig oder zu "
                    "alt – wird gelöscht")
                self._state_manager.clear()
            else:
                logger.info("Crash-Recovery: race_state.json gefunden – "
                            "werde nach dem Laden wiederherstellen!")
                self._data_source = "Crash-Recovery (race_state.json)"
                self._source_type = "crash"
                self._saved_state = saved_state

                # Crash-Recovery: racedaten aus IMPORT.json laden,
                # aber NICHT nachfragen (race_state.json hat Vorrang)
                if json_path is not None:
                    try:
                        self.scenario = self._load_from_json(json_path)
                        self._source_path = Path(json_path)
                        self._source_type = "json"
                        return
                    except (JsonReadError, FileNotFoundError) as exc:
                        logger.warning("Crash-Recovery: IMPORT.json nicht "
                                       "lesbar: {}", exc)

                # Keine IMPORT.json → Auto-Suche OHNE Bestätigungsdialog
                search_dir = self._get_search_dir()
                auto_json = search_dir / "IMPORT.json"
                if auto_json.exists():
                    try:
                        self.scenario = self._load_from_json(auto_json)
                        self._source_path = auto_json
                        self._source_type = "json"
                        return
                    except (JsonReadError, FileNotFoundError) as exc:
                        logger.warning("Crash-Recovery: Auto-Suche fehlgeschlagen: {}", exc)

                for ext in ("*.xlsm", "*.xlsx"):
                    found = list(search_dir.glob(ext))
                    if found:
                        try:
                            self.scenario = self._load_from_excel(found[0])
                            self._source_path = found[0]
                            self._source_type = "excel"
                            return
                        except (FileNotFoundError,
                                PermissionError, VbaMacroError):
                            pass

                # Keine Daten gefunden – Crash-Recovery allein reicht nicht
                logger.warning("Crash-Recovery: keine Renndaten gefunden")
                self._state_manager.clear()
                self._saved_state = None
                saved_state = None  # weiter mit normaler Lade-Kette

        # 2. IMPORT.json (--json)?
        if json_path is not None:
            try:
                self.scenario = self._load_from_json(json_path)
                if not saved_state:
                    self._data_source = f"JSON: {Path(json_path).name}"
                self._source_path = Path(json_path)
                self._source_type = "json"
                return
            except (JsonReadError, FileNotFoundError) as exc:
                logger.warning("IMPORT.json konnte nicht gelesen werden: {}", exc)

        # 3. Excel (--excel)?
        if excel_path is not None:
            try:
                self.scenario = self._load_from_excel(excel_path)
                if not saved_state:
                    self._data_source = f"Excel: {Path(excel_path).name}"
                self._source_path = Path(excel_path)
                self._source_type = "excel"
                return
            except (FileNotFoundError, PermissionError,
                    VbaMacroError) as exc:
                logger.warning("Excel konnte nicht gelesen werden: {}", exc)

        # 4. Vorab geladene Daten (Tests) – VOR Auto-Suche!
        if data is not None:
            self.scenario = data
            if not saved_state:
                self._data_source = "Testdaten"
            self._source_type = "test"
            return

        # 5. Auto-Suche im Arbeitsverzeichnis (EXE-Ordner oder CWD)
        search_dir = self._get_search_dir()
        logger.info("Auto-Suche in: {}", search_dir)
        auto_json = search_dir / "IMPORT.json"
        if auto_json.exists():
            if not self._confirm_source(auto_json):
                raise FileNotFoundError(
                    "Datenquelle wurde nicht bestätigt.\n\n"
                    "Bitte IMPORT.json oder Excel-Datei (.xlsm/.xlsx) "
                    "in den Programmordner legen."
                )
            try:
                self.scenario = self._load_from_json(auto_json)
                if not saved_state:
                    self._data_source = f"JSON: {auto_json.name} (auto)"
                self._source_path = auto_json
                self._source_type = "json"
                return
            except (JsonReadError, FileNotFoundError) as exc:
                logger.warning("Auto-Suche IMPORT.json fehlgeschlagen: {}", exc)

        # Excel-Dateien suchen (*.xlsm zuerst, dann *.xlsx)
        for ext in ("*.xlsm", "*.xlsx"):
            found = list(search_dir.glob(ext))
            if found:
                excel_file = found[0]  # erste gefundene Datei
                if not self._confirm_source(excel_file):
                    raise FileNotFoundError(
                        "Datenquelle wurde nicht bestätigt.\n\n"
                        "Bitte IMPORT.json oder Excel-Datei (.xlsm/.xlsx) "
                        "in den Programmordner legen."
                    )
                try:
                    self.scenario = self._load_from_excel(excel_file)
                    if not saved_state:
                        self._data_source = f"Excel: {excel_file.name} (auto)"
                    self._source_path = excel_file
                    self._source_type = "excel"
                    return
                except (FileNotFoundError, PermissionError,
                        VbaMacroError) as exc:
                    logger.warning("Auto-Suche Excel fehlgeschlagen: {}", exc)

        # 6. Nichts gefunden → Fehlermeldung
        # (Crash-Recovery ohne Daten ist ungültig – löschen)
        if saved_state:
            self._state_manager.clear()
        raise FileNotFoundError(
            f"Keine Renndaten gefunden in: {search_dir}\n\n"
            "Bitte IMPORT.json oder Excel-Datei (.xlsm/.xlsx) "
            "in den Programmordner legen."
        )

    def _confirm_source(self, filepath: Path) -> bool:
        """Zeigt einen Bestätigungsdialog für die gefundene Datenquelle (§4).

        Das Pflichtenheft §4 fordert: „...fordert den Benutzer zur
        Bestätigung der zu verwendenden Datenquelle auf."

        Args:
            filepath: Pfad zur gefundenen Datei.

        Returns:
            True wenn der Benutzer bestätigt hat, False bei Abbruch.
        """
        import tkinter.messagebox as messagebox

        msg = (f"Gefundene Datenquelle:\n\n"
               f"  {filepath.name}\n\n"
               f"  ({filepath})\n\n"
               f"Möchten Sie diese Datei verwenden?")
        return messagebox.askyesno(
            "Datenquelle bestätigen",
            msg,
            icon="question"
        )

    def _get_search_dir(self) -> Path:
        """Ermittelt den Ordner für die Auto-Suche.

        Gebaute .exe (.exe-Ordner), Entwicklung: Projekt-Root.

        Returns:
            Pfad zum Suchordner.
        """
        if getattr(sys, "frozen", False):
            # PyInstaller .exe → Ordner der .exe
            return Path(sys.executable).resolve().parent
        # Entwicklung → Projekt-Root (python/gui/../../)
        return Path(__file__).resolve().parent.parent.parent

    def _source_fingerprint(self) -> str | None:
        """Fingerabdruck der aktuellen Datenquelle für die Crash-Recovery.

        Enthält Pfad, Größe und Änderungszeit. Damit wird verhindert, dass
        ein race_state.json von einer anderen Veranstaltung/einem anderen
        IMPORT.json wiederhergestellt wird.

        Returns:
            SHA-256-Hex-String oder None (keine Datei-Quelle/Testdaten).
        """
        if self._source_path is None or self._source_type == "test":
            return None
        path = Path(self._source_path)
        try:
            stat = path.stat()
            raw = f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
        except OSError:
            raw = str(path.resolve())
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _validate_saved_state(self) -> None:
        """Verwirft einen Crash-Recovery-State, der nicht zur Quelle passt.

        Geprüft werden Rennnummer und Fingerabdruck der Datenquelle. Bei
        Testdaten (data=...) wird ein vorhandener State immer verworfen,
        damit Tests nicht von einem früheren Lauf beeinflusst werden.
        """
        if self._saved_state is None:
            return

        if self._source_type == "test":
            logger.warning("Crash-Recovery: Testdaten – State wird verworfen")
            self._state_manager.clear()
            self._saved_state = None
            return

        race_number = None
        if self.scenario is not None and self.scenario.selected_config:
            race_number = self.scenario.selected_config.race_number

        if not self._state_manager.is_compatible(
                self._saved_state,
                race_number=race_number,
                source_fingerprint=self._source_fingerprint()):
            logger.warning(
                "Crash-Recovery: State passt nicht zur Datenquelle – "
                "wird verworfen")
            self._state_manager.clear()
            self._saved_state = None
            if self._source_type == "json" and self._source_path is not None:
                self._data_source = f"JSON: {Path(self._source_path).name}"
            elif self._source_type == "excel" and self._source_path is not None:
                self._data_source = f"Excel: {Path(self._source_path).name}"

    def _load_from_json(self, json_path: str | Path) -> RaceData:
        """Lädt Renndaten aus einer IMPORT.json.

        Args:
            json_path: Pfad zur IMPORT.json.

        Returns:
            RaceData mit den geladenen Daten.
        """
        store = JsonRaceStore(json_path)
        event, race_configs, starters = store.read()
        return RaceData(
            event=event,
            race_configs=race_configs,
            starters=starters,
            selected_config=race_configs[0] if race_configs else RaceConfig(),
        )

    def _load_from_excel(self, excel_path: str | Path) -> RaceData:
        """Lädt Renndaten aus einer Excel-Datei via VBA-Makro.

        Ablauf (ADR-009):
            1. VBA-Makro ``ExportExpRangesToJSON`` aufrufen
            2. Warten bis IMPORT.json erzeugt ist
            3. IMPORT.json mit JsonRaceStore lesen

        Args:
            excel_path: Pfad zur Excel-Datei mit VBA-Modul ``mdlEngl``.

        Returns:
            RaceData mit den geladenen Daten.

        Raises:
            VbaMacroError: wenn das VBA-Makro fehlschlägt.
            JsonReadError: wenn die erzeugte IMPORT.json ungültig ist.
        """
        excel_file = Path(excel_path)

        # VBA-Makro aufrufen → IMPORT.json erzeugen
        caller = VbaMacroCaller(excel_file)
        json_path = caller.export_json()
        logger.info("VBA-Makro hat IMPORT.json erzeugt: {}", json_path)

        # IMPORT.json lesen
        return self._load_from_json(json_path)

    def _setup_race_selector(self) -> None:
        """Baut das Rennen-Dropdown (Q5) im CountdownPanel."""
        labels = []
        for c in self.scenario.race_configs:
            race_starters = [s for s in self.scenario.starters
                             if s.race_number == c.race_number]
            classes = ", ".join(sorted({s.klasse for s in race_starters}))
            labels.append(f"Rennen {c.race_number} ({classes})")
        self.window.countdown.add_race_selector(labels, self._on_race_selected)

    def _load_race(self, config: RaceConfig) -> None:
        """Lädt ein Rennen in die RaceEngine und befüllt die Panels.

        Args:
            config: das zu ladende RaceConfig.
        """
        self.scenario.selected_config = config
        # Nur Starter berücksichtigen, die in diesem Rennen starten
        starters = [s for s in self.scenario.starters
                    if s.race_number == config.race_number]
        self.engine.load_race(
            race=self.scenario.event,
            config=config,
            starters=starters,
            lockout_seconds=self.settings.lockout_seconds,
        )
        self._last_event_count = 0
        self._race_total_seconds = float(config.race_duration_min * 60)
        self._last_phase = self.engine.phase

        # Tastenzuordnung bei Renn-Wechsel neu aufbauen (aktive Starter)
        if self._input_handler is not None:
            self._input_handler.update_mapping(
                HotkeyMapping.from_starters(list(self.engine.boats.keys())))

        # Panels befüllen
        self.window.race_info.set_event(self.scenario.event, config, starters)
        self.window.hotkeys.set_starters(starters)
        self.window.header.set_export_status("Noch kein Export")
        self.window.manual_correction.set_boats(self.engine.boats)
        self.window.race_end_status.update_classes(self.engine.classes)
        # Streckenlängen für die Geschw.-Spalte (Kundenanforderung 2026-09-03)
        self.window.live_table.set_lap_lengths(
            config.lap1_length_m, config.standard_lap_length_m)

        # Fußzeile: Datenquelle anzeigen
        self.window.footer_source.configure(
            text=f"Datenquelle: {self._data_source} (Rennen {config.race_number})")
        self.window.header.set_source(self._data_source)

        # Crash-Recovery: Gespeicherten Zustand wiederherstellen
        if self._saved_state is not None:
            self.engine.restore_from_state(self._saved_state)
            self._last_event_count = len(self.engine.events)
            self._last_phase = self.engine.phase
            self.window.countdown.show_race_buttons()  # PAUSE/NEUSTART anzeigen
            self.window.log_feed.log(
                f"Crash-Recovery: Rennen {config.race_number} wiederhergestellt "
                f"(Phase: {self.engine.phase.value})", valid=True)
            self._saved_state = None  # Nur einmal wiederherstellen
        else:
            # Frisches Rennen: PLAY-Button anzeigen
            self.window.countdown.show_start_button()
            self.window.log_feed.clear()
            # Bereits beendetes Rennen (Option 1, 2026-09-03): Ergebnisse
            # wurden wiederhergestellt, aber das Rennen ist fertig – kein
            # Start mehr möglich, nur noch Anzeige/Export.
            if config.race_number in self.engine.finished_races:
                self.window.countdown.set_start_enabled(False)
                self.window.log_feed.log(
                    f"Rennen {config.race_number} geladen – bereits beendet, "
                    f"Ergebnisse wiederhergestellt (kein Start möglich)",
                    valid=True)
            else:
                self.window.countdown.set_start_enabled(True)
                self.window.log_feed.log(
                    f"Rennen {config.race_number} geladen – "
                    f"Play-Button drücken zum Starten", valid=True)

        # Refresh-Button: nur bei Phase RESET erlauben
        self.window.header.set_refresh_enabled(
            self.engine.phase == RacePhase.RESET)

    # ------------------------------------------------------------------
    # Callbacks (Buttons, Dropdown, Hotkeys)
    # ------------------------------------------------------------------

    def _on_race_selected(self, label: str) -> None:
        """Dropdown-Auswahl: passende RaceConfig laden (Q5).

        Args:
            label: gewählter Dropdown-Text ("Rennen N (Klassen)").
        """
        for config in self.scenario.race_configs:
            if label.startswith(f"Rennen {config.race_number}"):
                self._load_race(config)
                return
        self.window.log_feed.log(f"Unbekannte Rennen-Auswahl: {label}", valid=False)

    def on_start_race(self) -> None:
        """PLAY-Button: Startet den Countdown (Vorlaufzeit beginnt).

        Wechselt von Phase RESET → PRESTART und zeigt PAUSE/NEUSTART-Buttons.
        Prüft vorher die Datenvalidierung (Pflichtenheft §4).
        """
        if self.engine.phase != RacePhase.RESET:
            return

        # Datenvalidierung (§4: „Erst nach erfolgreicher Prüfung...")
        # Nur das aktuelle Rennen prüfen (Keys anderer Rennen sind irrelevant)
        race_num = self.scenario.selected_config.race_number
        errors = validate_scenario(self.scenario, race_number=race_num)
        if errors:
            import tkinter.messagebox as messagebox
            msg = "Datenvalidierung fehlgeschlagen:\n\n• " + "\n• ".join(errors)
            messagebox.showwarning("Rennen nicht freigegeben", msg)
            self.window.log_feed.log(
                f"Rennen nicht freigegeben: {len(errors)} Fehler", valid=False)
            return

        self.engine.start_countdown()
        self.window.countdown.show_race_buttons()
        self.window.header.set_refresh_enabled(False)  # Refresh während Rennen gesperrt
        self.window.log_feed.log("Countdown gestartet", valid=True)

    def on_pause_toggle(self) -> None:
        """PAUSE/WEITER-Button: Countdown der Engine unterbrechen/fortsetzen (Q8).

        Nur im Vorstart relevant – während des Rennens ist der Button
        deaktiviert. Beim Fortsetzen läuft die eingefrorene Restzeit exakt
        weiter (Engine verschiebt countdown_end).
        """
        if self.engine.phase != RacePhase.PRESTART:
            return
        if self.engine.countdown_paused:
            self.engine.resume_countdown()
            self.window.countdown.set_pause_mode(False)
            self.window.log_feed.log("Countdown fortgesetzt", valid=True)
        else:
            self.engine.pause_countdown()
            self.window.countdown.set_pause_mode(True)
            self.window.log_feed.log("Countdown pausiert", valid=True)

    def on_reset(self, confirm: bool = True) -> None:
        """NEUSTART-Button: Engine zurücksetzen → Vorstart (Q4/Q8).

        Zeigt optionally einen Bestätigungsdialog. Erst nach Bestätigung wird
        der Zustand zurückgesetzt: Boots-Zustände, Ereignisse und Sperrzeiten
        werden geleert, Race-State wird gelöscht.

        Args:
            confirm: True → Bestätigungsdialog anzeigen; False → direkt
                     zurücksetzen (für Tests und interne Aufrufe).
        """
        if confirm:
            import tkinter.messagebox as messagebox

            if not messagebox.askyesno(
                "Neustart bestätigen",
                "Sind Sie sicher, dass Sie das Rennen neu starten möchten?\n\n"
                "Alle bisherigen Ereignisse und Runden gehen verloren.",
                icon="warning"
            ):
                return

        self.engine.reset()
        self._last_event_count = 0
        self._last_phase = self.engine.phase
        self._state_manager.clear()  # Crash-Recovery-State löschen
        self.window.countdown.show_start_button()  # PLAY-Button wieder anzeigen
        self.window.header.set_refresh_enabled(True)  # Refresh wieder erlauben
        self.window.manual_correction.set_boats(self.engine.boats)
        self.window.race_end_status.update_classes(self.engine.classes)
        self.window.log_feed.log("Reset – Play-Button zum Neustart",
                                 valid=True)

    def on_refresh_data(self) -> None:
        """Refresh-Button: Lädt Renndaten aus derselben Quelle neu (§4).

        Nur verfügbar wenn kein Rennen läuft (Phase RESET).
        Aktualisiert Panels und Engine mit frischen Daten aus der
        gespeicherten Quelle.
        """
        if self.engine.phase != RacePhase.RESET:
            self.window.log_feed.log(
                "Refresh nicht möglich – Rennen läuft", valid=False)
            return

        if self._source_path is None or self._source_type == "test":
            self.window.log_feed.log(
                "Refresh nicht möglich – keine Datei-Quelle", valid=False)
            return

        try:
            if self._source_type == "json":
                self.scenario = self._load_from_json(self._source_path)
                self._data_source = f"JSON: {self._source_path.name}"
            elif self._source_type == "excel":
                self.scenario = self._load_from_excel(self._source_path)
                self._data_source = f"Excel: {self._source_path.name}"
            else:
                self.window.log_feed.log(
                    f"Refresh für Quelle '{self._source_type}' nicht unterstützt",
                    valid=False)
                return
        except Exception as exc:
            logger.error("Refresh fehlgeschlagen: {}", exc)
            self.window.log_feed.log(f"Refresh fehlgeschlagen: {exc}",
                                     valid=False)
            return

        # Panels aktualisieren
        self.window.header.set_source(self._data_source)
        self._setup_race_selector()
        self._load_race(self.scenario.selected_config)
        self.window.log_feed.log(
            f"Daten aktualisiert aus {self._data_source}", valid=True)

    def on_key_press(self, boot_key: str) -> None:
        """Hotkey-Klick (virtuelle Tastatur): Eingabe an die Engine weiterreichen.

        Die Engine prüft Sperrzeit (Q1) und Phase; gültige Passagen werden
        als Runde verbucht. Außerhalb des Rennens wird die Eingabe nur
        protokolliert (kein Engine-Aufruf).

        Args:
            boot_key: Boot-Key (A–Z).
        """
        self._process_boot_key(boot_key)

    def _process_boot_key(self, boot_key: str) -> None:
        """Verarbeitet eine Boot-Key-Eingabe (GUI-Klick oder System-Hotkey).

        Gültig nur in ACTIVE/FINISHING; der Ignore-Pfad protokolliert die
        Eingabe im Log-Feed (die Beweispflicht erfüllt bei echten
        Tastendrücken der InputHandler durch den sofortigen Rohdruck).

        Wichtig (Doppel-Logging-Fix 2026-08-14): Die Engine kann bei einem
        Aufruf MEHRERE Events anhängen (z. B. PASSAGE + FINISH in der
        Endphase). Deshalb werden alle seit Aufrufbeginn neu erzeugten
        Events angezeigt und `_last_event_count` erst DANACH synchronisiert
        – so holt der Tick nichts doppelt nach.

        Args:
            boot_key: Boot-Key (A–Z).
        """
        if self.engine.phase not in (RacePhase.ACTIVE, RacePhase.FINISHING):
            self.window.log_feed.log(
                f"Eingabe {boot_key} ignoriert – Rennen läuft nicht",
                timestamp=datetime.now(), valid=False)
            return
        start_index = len(self.engine.events)
        self.engine.handle_key_press(boot_key, datetime.now())
        for event in self.engine.events[start_index:]:
            self._show_event(event)
        self._last_event_count = len(self.engine.events)

    def on_manual_correction(self, boot_key: str) -> None:
        """Manuell +1 Runde über die Engine (Pflichtenheft §6, Q6 nur +1).

        Wie `_process_boot_key`: alle neuen Events anzeigen, Zähler danach
        synchronisieren (kein Doppel-Logging durch den Tick).

        Args:
            boot_key: Boot-Key für die Korrektur.
        """
        start_index = len(self.engine.events)
        self.engine.handle_manual_correction(boot_key, 1, datetime.now())
        for event in self.engine.events[start_index:]:
            self._show_event(event)
        self._last_event_count = len(self.engine.events)

    def on_finish_class(self, klasse: str) -> None:
        """'Beenden'-Button: beendet eine Klasse manuell (2026-09-03).

        Kundenentscheidung: Nach Ablauf der Renndauer ändert sich nichts
        automatisch. Der Bediener beendet jede Klasse manuell über den
        'Beenden'-Button im Rennende-Status. Beim Beenden werden alle Boote
        der Klasse als fertig markiert und das Ergebnis steht fest.

        Args:
            klasse: Klassenname der zu beendenden Klasse.
        """
        now = datetime.now()
        start_index = len(self.engine.events)
        finished = self.engine.finish_class(klasse, now)
        if not finished:
            self.window.log_feed.log(
                f"Klasse {klasse} konnte nicht beendet werden", valid=False)
            return
        for event in self.engine.events[start_index:]:
            self._show_event(event)
        self._last_event_count = len(self.engine.events)
        self.window.log_feed.log(
            f"Klasse {klasse} beendet – Ergebnis steht fest", valid=True)

    # ------------------------------------------------------------------
    # Ergebnis-Export (Pflichtenheft §7 „Excel-Log")
    # ------------------------------------------------------------------

    def _default_export_dir(self) -> Path:
        """Ermittelt den Standard-Exportordner.

        Gebaute .exe (PyInstaller): Ordner der .exe – der Bediener findet
        die Ergebnisse direkt neben dem Programm. Entwicklung: aktuelles
        Arbeitsverzeichnis (Projekt-Root).

        Returns:
            Der Zielordner für Exporte.
        """
        return get_runtime_dir()

    def on_export_results(self) -> None:
        """Exportiert ALLE fertigen Rennen als EINE JSON-Datei.

        Option 1 (2026-09-03): Der Export enthält alle bereits beendeten
        Rennen (aus `engine.finished_races`), gruppiert nach Rennen und
        Klasse. Das aktuelle Rennen wird einbezogen, wenn es bereits
        beendet (FINISHED) ist.

        Es wird IMMER eine neue Datei erzeugt (Zeitstempel im Namen) –
        Rohdaten (IMPORT.json, Blackbox) bleiben unangetastet.

        Erfolg/Fehler erscheinen im Log-Feed und im Status-Label des
        Hotkey-Panels (grün/rot).
        """
        # Alle fertigen Rennen sammeln (aus finished_races)
        exports: list[RaceResultExport] = []
        for race_number, saved in self.engine.finished_races.items():
            exports.append(RaceResultExport(
                event=self.scenario.event,
                config=saved["config"],
                results=saved["results"],
                log_entries=saved["events"],
            ))

        # Das aktuelle Rennen einbeziehen, wenn es bereits beendet ist
        # (FINISHED) und noch nicht in finished_races liegt.
        if (self.engine.phase == RacePhase.FINISHED
                and self.engine.config.race_number not in self.engine.finished_races):
            exports.append(RaceResultExport(
                event=self.scenario.event,
                config=self.engine.config,
                results=self.engine.get_placements(),
                log_entries=list(self.engine.events),
            ))

        filename = (f"RESULT_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        target = self._export_dir / filename
        try:
            written = JsonResultWriter().write_all_races(
                target, exports, event=self.scenario.event)
        except JsonWriteError as exc:
            logger.error(f"Ergebnis-Export fehlgeschlagen: {exc}")
            self.window.log_feed.log(f"Export FEHLGESCHLAGEN: {exc}",
                                     valid=False)
            self.window.header.set_export_status(str(exc), ok=False)
            return
        logger.info("Ergebnis-Export gespeichert: {}", written)
        if exports:
            race_nums = sorted({e.config.race_number for e in exports})
            self.window.log_feed.log(
                f"Ergebnis exportiert: {written.name} "
                f"(Rennen {', '.join(str(n) for n in race_nums)})", valid=True)
        else:
            # Noch kein Rennen beendet → nur Stammdaten (Event) exportiert
            self.window.log_feed.log(
                f"Export (nur Stammdaten): {written.name} – "
                f"noch kein beendetes Rennen", valid=True)
        self.window.header.set_export_status(f"Gespeichert: {written.name}",
                                             ok=True)

    # ------------------------------------------------------------------
    # Tick (after-Polling, ADR-007)
    # ------------------------------------------------------------------

    def _start_tick(self) -> None:
        """Startet den periodischen Refresh (POLL_INTERVAL_MS) über after().

        Kann über stop_tick() gestoppt werden – zwingend nötig damit
        Tests ohne Tick-Restarts laufen.
        """
        self._tick_running = True
        self._tick()
        if self._tick_running:
            self._tick_after_id = self.window.after(
                Cfg.POLL_INTERVAL_MS, self._start_tick)

    def stop_tick(self) -> None:
        """Stoppt das Tick-Loop sauber (verhindert after()-Restarts)."""
        self._tick_running = False
        if self._tick_after_id is not None:
            try:
                self.window.after_cancel(self._tick_after_id)
            except Exception:
                pass  # Window bereits geschlossen
            self._tick_after_id = None

    def _tick(self) -> None:
        """Ein Tick: Engine fortschreiben + Panels aktualisieren."""
        now = datetime.now()

        # --- System-Hotkeys der Queue entnehmen und verarbeiten ----------
        if self._input_queue is not None:
            while True:
                try:
                    boot_key = self._input_queue.get_nowait()
                except queue.Empty:
                    break
                self._process_boot_key(boot_key)

        self.engine.tick(now)

        # --- Countdown- bzw. Rennzeit-Anzeige ------------------------------
        config = self.scenario.selected_config
        if self.engine.phase == RacePhase.RESET:
            # Reset: Countdown steht still, Play-Button zeigt "Start"
            self.window.countdown.set_prestart(
                float(config.start_interval_s), float(config.start_interval_s))
            self.window.countdown.set_pause_enabled(False)
        elif self.engine.phase == RacePhase.PRESTART:
            remaining = max(
                self.engine.countdown_remaining(now).total_seconds(), 0.0)
            self.window.countdown.set_prestart(
                remaining, float(config.start_interval_s))
            self.window.countdown.set_pause_mode(self.engine.countdown_paused)
            self.window.countdown.set_pause_enabled(True)
        else:
            remaining = max(self.engine.race_remaining(now).total_seconds(), 0.0)
            self.window.countdown.set_race_remaining(
                remaining, self._race_total_seconds)
            self.window.countdown.set_pause_enabled(False)
            # Startreihen-Countdown (Variante A, 2026-09-03): Der Countdown
            # für die 2./x. Startreihe wird ANSTATT des Vorstart-Countdowns
            # in der VORSTART-Kachel angezeigt (nicht zusätzlich).
            next_line = self.engine.next_start_line(now)
            if next_line is not None:
                line_remaining = max(
                    self.engine.start_line_remaining(now).total_seconds(), 0.0)
                self.window.countdown.set_start_line(
                    next_line, line_remaining, float(config.grid_time_s))
            else:
                # Keine weitere Startreihe → VORSTART-Kachel leer/neutral
                self.window.countdown.set_prestart(0.0, 1.0)

        # --- Sperrzeit-Ablauf (Anzeige-Feld) aufräumen ----------------------
        for state in self.engine.boats.values():
            if state.lockout_until is not None and state.lockout_until <= now:
                state.lockout_until = None

        # --- Export-Button: immer aktiv (2026-09-03) -----------------------
        # Der Export enthält ALLE fertigen Rennen auf einmal – er ist damit
        # unabhängig vom aktuellen Rennen. Ist noch nichts beendet, werden
        # nur die Stammdaten (Event) exportiert.
        self.window.header.set_export_enabled(True)

        # --- Rennen-Selector: erlaubt in RESET oder wenn alle Boote fertig ----
        all_finished = (
            len(self.engine.boats) > 0
            and all(s.finished_at is not None
                    for s in self.engine.boats.values())
        )
        self.window.countdown.set_race_selector_enabled(
            self.engine.phase == RacePhase.RESET or all_finished)

        # --- Hotkeys: nur gestartete Boote aktiv (2026-09-03) --------------
        # Ein Hotkey ist nur aktiv (grün), wenn der jeweilige Starter
        # gestartet ist (seine Startreihe aktiv). Sonst grau und inaktiv.
        started_keys = {state.starter.boot_key
                        for state in self.engine.boats.values()
                        if state.start_time is not None
                        and state.start_time <= now}
        self.window.hotkeys.set_started_keys(started_keys)

        # --- Hotkeys: Boote beendeter (CLOSED) Klassen inaktiv (2026-09-03) --
        # Wenn eine Klasse beendet wird, werden die Hotkeys ihrer Boote
        # inaktiv (grau) – auch wenn sie gestartet waren.
        class_status = self.engine.get_class_finish_status()
        closed_classes = {k for k, v in class_status.items() if v == "CLOSED"}
        finished_keys = {state.starter.boot_key
                         for state in self.engine.boats.values()
                         if state.starter.klasse in closed_classes}
        self.window.hotkeys.set_finished_keys(finished_keys)

        # --- Live-Tabelle + Rennende-Status (Wertung aktuell halten) --------
        self.engine.get_placements()
        self.window.live_table.update_boats(self.engine.boats, now)
        # Beenden-Button erst aktiv, wenn die Rennzeit abgelaufen ist
        # (Phase FINISHING/FINISHED – Kundenanforderung 2026-09-03)
        race_over = self.engine.phase in (RacePhase.FINISHING, RacePhase.FINISHED)
        self.window.race_end_status.set_race_over(race_over)
        self.window.race_end_status.update_states(
            self.engine.get_class_finish_status())

        # --- Phasenwechsel + neue Engine-Events loggen ----------------------
        if self.engine.phase != self._last_phase:
            self._log_phase_change(self.engine.phase)
            self._last_phase = self.engine.phase
        for event in self.engine.events[self._last_event_count:]:
            self._show_event(event)
        self._last_event_count = len(self.engine.events)

        # --- Crash-Recovery: State bei Änderungen speichern -----------------
        # RaceStateManager drosselt unveränderte States (Heartbeat 30 s) und
        # schreibt atomar. Der Fingerprint verhindert die Wiederherstellung
        # eines States aus einer anderen Datenquelle.
        if self.engine.events and self.engine.phase != RacePhase.RESET:
            self._state_manager.save(
                self.engine.to_dict(),
                source_fingerprint=self._source_fingerprint(),
            )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_phase_change(self, phase: RacePhase) -> None:
        """Protokolliert einen Phasenwechsel im Log-Feed.

        Args:
            phase: neue Rennphase der Engine.
        """
        texts = {
            RacePhase.PRESTART: "Vorstart – Countdown läuft (Q8)",
            RacePhase.ACTIVE: "Rennen gestartet (automatisch nach Countdown)",
            RacePhase.FINISHING: "Renndauer abgelaufen – klassenweise Endphase",
            RacePhase.FINISHED: "Rennen beendet – alle Klassen abgeschlossen",
        }
        self.window.log_feed.log(texts.get(phase, str(phase)), valid=True)

    def _show_event(self, event: RaceEvent) -> None:
        """Schreibt ein Engine-Ereignis als Log-Feed-Eintrag.

        Args:
            event: RaceEvent aus engine.events.
        """
        texts = {
            EventType.START: "Rennen gestartet",
            EventType.STARTLINE: self._startline_text(event),
            EventType.PASSAGE: f"Boot {event.boot_key} Passage",
            EventType.FINISH: f"Boot {event.boot_key} Zieleinlauf",
            EventType.CORRECTION_PLUS: f"Boot {event.boot_key} +1 (manuell)",
            EventType.INVALID: f"Boot {event.boot_key} UNGÜLTIG (Sperrzeit)",
        }
        text = texts.get(event.event_type, str(event.event_type))
        self.window.log_feed.log(text, timestamp=event.timestamp, valid=event.valid)

        # Blackbox (Beweisfunktion): Verarbeitungsergebnis sofort sichern.
        # Der Rohdruck der echten Taste stammt vom InputHandler; hier wird
        # die Interpretation (START/PASSAGE/...) ergänzt.
        if self.blackbox is not None:
            status = "VALID" if event.valid else "INVALID"
            self.blackbox.write_key_event(
                event.timestamp,
                key=event.boot_key or None,
                event_type=event.event_type.value,
                status=status)

    def _startline_text(self, event: RaceEvent) -> str:
        """Ermittelt den Anzeigetext für ein STARTLINE-Ereignis.

        Die Startreihen-Nummer wird aus dem Event-Zeitstempel abgeleitet:
        das Boot, dessen individueller Startzeitpunkt dem Event-Zeitstempel
        entspricht, bestimmt die Startreihen-Nummer.

        Args:
            event: das STARTLINE-Ereignis.

        Returns:
            Anzeigetext, z. B. "Startreihe 2 gestartet".
        """
        for state in self.engine.boats.values():
            if (state.start_time is not None
                    and state.start_time == event.timestamp):
                return f"Startreihe {state.starter.startreihe} gestartet"
        return "Startreihe gestartet"


def run_app(enable_keyboard: bool | None = None,
            auto_close_seconds: float = 0.0,
            excel_path: str | Path | None = None,
            json_path: str | Path | None = None,
            is_admin: bool = False) -> None:
    """Startet die Anwendung (Standard-Einstiegspunkt für main.py/preview_gui.py).

    Die Blackbox (Beweis-Log) ist immer aktiv (blackbox.log im Projekt-Root).

    Lade-Kette (Manual.md):
        1. race_state.json → Crash-Recovery
        2. json_path (IMPORT.json) → direkt laden
        3. excel_path → laden
        4. Nichts davon → Fehlermeldung

    Args:
        enable_keyboard: True = systemweite Hotkeys aktivieren (keyboard-
            Library, benötigt Windows-Admin, AGENTS.md §10). None (Standard)
            → Wert aus app_settings.json (`enable_keyboard`) verwenden.
        auto_close_seconds: > 0 → Fenster nach N Sekunden automatisch
            schließen (Smoke-Tests/Screenshots; deterministische Position).
        excel_path: Pfad zur Excel-Datei (Named Ranges). None.
        json_path: Pfad zur IMPORT.json (vom VBA-Makro erzeugt). None.
        is_admin: True wenn die App mit Administrator-Rechten läuft
                  (für die Hotkey-Status-Anzeige, 2026-09-03).
    """
    if enable_keyboard is None:
        enable_keyboard = get_settings().enable_keyboard
    ctk.set_appearance_mode("dark")
    window = MainWindow()
    try:
        AppController(window, blackbox_path=str(get_runtime_dir() / "blackbox.log"),
                      enable_keyboard=enable_keyboard,
                      excel_path=excel_path,
                      json_path=json_path,
                      is_admin=is_admin)
    except Exception as exc:
        logger.error("Start fehlgeschlagen: {}", exc)
        import tkinter.messagebox as messagebox
        messagebox.showerror("Start fehlgeschlagen", str(exc))
        window.destroy()
        return
    if auto_close_seconds > 0:
        # Auto-Close-Modus (Smoke-Test): Fenster oben, feste Position
        window.geometry(f"{Cfg.WINDOW_WIDTH}x{Cfg.WINDOW_HEIGHT}+50+50")
        window.lift()
        window.attributes("-topmost", True)
        window.after(int(auto_close_seconds * 1000), window.destroy)
        logger.info("Auto-Close nach {}s aktiviert", auto_close_seconds)
    window.mainloop()
