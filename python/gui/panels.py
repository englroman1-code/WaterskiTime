"""GUI-Panels für das Zeitnehmungs-System (CustomTkinter).

Dieses Modul enthält die wiederverwendbaren Panel-Klassen des 4-Bereichs-Layouts
gemäß 05_a_GUI_Description.txt und 08_gui_implementation_guide.md:

    Bereich 1: HeaderPanel         (Titel + Branding)
    Bereich 2: RaceInfoPanel       (links) + CountdownPanel (rechts)
    Bereich 3: LiveTablePanel      (links) + HotkeyPanel (rechts)
    Bereich 4: LogFeedPanel        + RaceEndStatusPanel + ManualCorrectionPanel

Konventionen:
    - Klassen-/Methodennamen: Englisch
    - Docstrings & Kommentare: Deutsch
    - Farben aus python/config/app_config.py (AppConfig)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import customtkinter as ctk

from python.config.app_config import AppConfig as Cfg
from python.core.models import BoatState, Event, RaceClass, RaceConfig, Starter
from python.core.time_format import format_duration  # zentrale Zeitformatierung

# ---------------------------------------------------------------------------
# Hilfsfunktionen (Formatierung)
# ---------------------------------------------------------------------------

def format_countdown(seconds: float) -> str:
    """Formatiert Sekunden als HH:MM:SS (für die VORSTART-Anzeige).

    Args:
        seconds: Restzeit in Sekunden (kann negativ sein → 00:00:00).

    Returns:
        Zeitstring im Format HH:MM:SS.
    """
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02}"


def format_remaining(seconds: float) -> str:
    """Formatiert Sekunden als MM:SS (bzw. HH:MM:SS ab 1 Stunde).

    Args:
        seconds: Restzeit in Sekunden.

    Returns:
        Kompakter Zeitstring für die VERBLEIBENDE-ZEIT-Anzeige.
    """
    seconds = max(0, int(seconds))
    if seconds >= 3600:
        return format_countdown(seconds)
    m, s = divmod(seconds, 60)
    return f"{m:02}:{s:02}"


# ---------------------------------------------------------------------------
# Bereich 1: Kopfbereich
# ---------------------------------------------------------------------------

class HeaderPanel(ctk.CTkFrame):
    """Kopfbereich: großer Titel links, Firmen-Branding rechts (GUI-Description).

    Enthält zudem die Datenquellen-Anzeige, den Refresh-Button und den
    Export-Button (Pflichtenheft §4 + §7: Datenquelle anzeigen, Refresh
    nur ohne laufendes Rennen, Export nach Rennende).
    """

    def __init__(self, parent: ctk.CTkBaseClass, version: str = "") -> None:
        """HeaderPanel initialisieren.

        Args:
            parent: Eltern-Widget (MainWindow).
            version: Versionsstring für den Untertitel (z. B. "v0.1.0").
        """
        super().__init__(parent, fg_color=Cfg.COLOR_BG, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)

        # Obere Zeile: Titel links, Branding rechts
        top_row = ctk.CTkFrame(self, fg_color=Cfg.COLOR_BG)
        top_row.grid(row=0, column=0, sticky="ew", padx=0, pady=(10, 0))
        top_row.grid_columnconfigure(0, weight=1)

        title = f"Zeitnehmungs-System Wasserski-Racing"
        if version:
            title += f"  {version}"
        ctk.CTkLabel(top_row, text=title, font=("Segoe UI", 28, "bold"),
                     text_color=Cfg.COLOR_TEXT).grid(row=0, column=0,
                                                     sticky="w", padx=24)

        # Branding rechts (EDV Engl Roman) – Daten zentral in app_config.py
        branding = ctk.CTkFrame(top_row, fg_color=Cfg.COLOR_BG)
        branding.grid(row=0, column=1, sticky="e", padx=24)
        ctk.CTkLabel(branding, text=Cfg.BRANDING_NAME,
                     font=("Segoe UI", 14, "bold"),
                     text_color=Cfg.COLOR_TEXT).pack(anchor="e")
        ctk.CTkLabel(branding, text=Cfg.BRANDING_URL,
                     font=("Segoe UI", 11),
                     text_color=Cfg.COLOR_TEXT_SECONDARY).pack(anchor="e")

        # Untere Zeile: Datenquelle + Buttons (Refresh + Export)
        bottom_row = ctk.CTkFrame(self, fg_color=Cfg.COLOR_BG)
        bottom_row.grid(row=1, column=0, sticky="ew", padx=0, pady=(2, 10))
        bottom_row.grid_columnconfigure(1, weight=1)

        self._source_label = ctk.CTkLabel(
            bottom_row, text="Datenquelle: –",
            font=("Segoe UI", 12),
            text_color=Cfg.COLOR_TEXT_SECONDARY)
        self._source_label.grid(row=0, column=0, sticky="w", padx=24)

        # Buttons rechts: Refresh + Export ( nebeneinander)
        buttons_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, sticky="e", padx=24)

        self._refresh_button = ctk.CTkButton(
            buttons_frame, text="Daten aktualisieren",
            width=160, height=28,
            font=("Segoe UI", 11),
            fg_color=Cfg.COLOR_ACCENT,
            hover_color=Cfg.COLOR_ACCENT_HOVER,
            state="disabled",
            command=self._on_refresh_clicked)
        self._refresh_button.pack(side="left", padx=(0, 8))

        self._export_button = ctk.CTkButton(
            buttons_frame, text="Ergebnis exportieren",
            width=180, height=28,
            font=("Segoe UI", 11, "bold"),
            fg_color=Cfg.COLOR_PROGRESS, hover_color="#1A5FD6",
            state="disabled",
            command=self._on_export_clicked)
        self._export_button.pack(side="left", padx=(0, 8))

        self._export_status = ctk.CTkLabel(
            buttons_frame, text="",
            font=("Segoe UI", 10),
            text_color=Cfg.COLOR_TEXT_SECONDARY,
            anchor="w", justify="left")
        self._export_status.pack(side="left")

        # Callbacks (werden vom Controller gesetzt)
        self._refresh_callback = None
        self._export_callback = None

    def set_source(self, source_text: str) -> None:
        """Aktualisiert die angezeigte Datenquelle.

        Args:
            source_text: Beschreibung der aktuellen Datenquelle.
        """
        self._source_label.configure(text=f"Datenquelle: {source_text}")

    def set_refresh_enabled(self, enabled: bool) -> None:
        """Aktiviert/Deaktiviert den Refresh-Button.

        Args:
            enabled: True = Button aktiv (klickbar), False = deaktiviert.
        """
        self._refresh_button.configure(
            state="normal" if enabled else "disabled")

    def set_refresh_callback(self, callback) -> None:
        """Setzt den Callback für den Refresh-Button.

        Args:
            callback: Funktion die beim Klick aufgerufen wird.
        """
        self._refresh_callback = callback

    def _on_refresh_clicked(self) -> None:
        """Refresh-Button geklickt – ruft den Callback auf."""
        if self._refresh_callback is not None:
            self._refresh_callback()

    # ------------------------------------------------------------------
    # Ergebnis-Export (Pflichtenheft §7, vom Header aus bedienbar)
    # ------------------------------------------------------------------

    def set_export_callback(self, callback) -> None:
        """Setzt den Callback für den Export-Button.

        Args:
            callback: Funktion die beim Klick aufgerufen wird.
        """
        self._export_callback = callback

    def set_export_enabled(self, enabled: bool) -> None:
        """Aktiviert/Deaktiviert den Export-Button.

        Args:
            enabled: True = Button aktiv (klickbar), False = deaktiviert.
        """
        self._export_button.configure(
            state="normal" if enabled else "disabled")

    def set_export_status(self, text: str, ok: bool | None = None) -> None:
        """Zeigt das Ergebnis des letzten Exports im Status-Label an.

        Args:
            text: anzuzeigender Text (z. B. Dateiname oder Fehlermeldung).
            ok: None = neutral (Standardfarbe), True = grün (Erfolg),
                False = rot (Fehler).
        """
        if ok is True:
            color = Cfg.COLOR_ACTIVE
        elif ok is False:
            color = Cfg.COLOR_ERROR
        else:
            color = Cfg.COLOR_TEXT_SECONDARY
        self._export_status.configure(text=text, text_color=color)

    def _on_export_clicked(self) -> None:
        """Export-Button geklickt – ruft den Callback auf."""
        if self._export_callback is not None:
            self._export_callback()


# ---------------------------------------------------------------------------
# Bereich 2 links: Renninformationen
# ---------------------------------------------------------------------------

class RaceInfoPanel(ctk.CTkFrame):
    """Renninformationen: reine Anzeige in 2 Spalten (Event, Datum, Rennen, Streckenlängen).

    Dieses Panel zeigt nur Information – keine Buttons oder Dropdowns.
    Die Rennen-Auswahl befindet sich im CountdownPanel.
    """

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        """RaceInfoPanel initialisieren (2-Spalten-Layout)."""
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Renninformationen", font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).grid(row=0, column=0, columnspan=2,
                                                     sticky="w", padx=16, pady=(12, 6))

        self._values: dict[str, ctk.CTkLabel] = {}
        # Linke Spalte: Event, Datum, Rennen; Rechte Spalte: Länge R1, Länge R2+
        left_fields = [("Event", 1), ("Datum", 2), ("Rennen", 3)]
        right_fields = [("Länge R1", 1), ("Länge R2+", 2)]

        for key, row in left_fields:
            ctk.CTkLabel(self, text=f"{key}:", font=("Segoe UI", 13),
                         text_color=Cfg.COLOR_TEXT_SECONDARY).grid(
                row=row, column=0, sticky="w", padx=(16, 8), pady=2)
            value_label = ctk.CTkLabel(self, text="–", font=("Segoe UI", 13, "bold"),
                                       text_color=Cfg.COLOR_TEXT)
            value_label.grid(row=row, column=0, sticky="w", padx=(100, 8), pady=2)
            self._values[key] = value_label

        for key, row in right_fields:
            ctk.CTkLabel(self, text=f"{key}:", font=("Segoe UI", 13),
                         text_color=Cfg.COLOR_TEXT_SECONDARY).grid(
                row=row, column=1, sticky="w", padx=(16, 8), pady=2)
            value_label = ctk.CTkLabel(self, text="–", font=("Segoe UI", 13, "bold"),
                                       text_color=Cfg.COLOR_TEXT)
            value_label.grid(row=row, column=1, sticky="w", padx=(100, 16), pady=2)
            self._values[key] = value_label

    # ------------------------------------------------------------------
    def set_event(self, event: Event, config: RaceConfig,
                   starters: list[Starter] | None = None) -> None:
        """Zeigt Veranstaltungs- und Renninformationen an (reine Anzeige).

        Args:
            event: Veranstaltungsdaten (Event).
            config: das aktive Rennen (für Rennen-Nummer + Klassen).
            starters: alle Starter des Rennens (für Klassen-Ableitung).
        """
        self._values["Event"].configure(text=event.title or "–")
        self._values["Datum"].configure(text=event.date or "–")
        if starters:
            classes = ", ".join(sorted({s.klasse for s in starters})) or "–"
        else:
            classes = "–"
        self._values["Rennen"].configure(text=f"{config.race_number} ({classes})")
        self._values["Länge R1"].configure(
            text=f"{config.lap1_length_m} m" if config.lap1_length_m else "–")
        self._values["Länge R2+"].configure(
            text=f"{config.standard_lap_length_m} m" if config.standard_lap_length_m else "–")


# ---------------------------------------------------------------------------
# Bereich 2 rechts: Countdown-Anzeige
# ---------------------------------------------------------------------------

class CountdownPanel(ctk.CTkFrame):
    """Countdown-Anzeige: VORSTART (rot) + VERBLEIBENDE ZEIT (grün) + Buttons.

    Aufbau pro Kachel: Überschrift, großer Zeitwert, Fortschrittsbalken.
    Darunter: PLAY-Button (grün) zum Starten, PAUSE/WEITER (gelb) + NEUSTART (grün).

    Bedienung:
        - PLAY: Startet den Countdown (Vorlaufzeit beginnt).
        - PAUSE/WEITER: Countdown unterbrechen bzw. fortsetzen.
        - NEUSTART: Countdown von vorn (bzw. im Rennen: zurück zum Vorstart, Q4).
    """

    def __init__(self, parent: ctk.CTkBaseClass,
                 on_pause_toggle: callable | None = None,
                 on_reset: callable | None = None,
                 on_start_race: callable | None = None) -> None:
        """CountdownPanel initialisieren.

        Args:
            parent: Eltern-Widget.
            on_pause_toggle: Callback für den PAUSE/WEITER-Button.
            on_reset: Callback für den NEUSTART-Button.
            on_start_race: Callback für den PLAY-Button (Rennen starten).
        """
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Countdown-Anzeige", font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).grid(row=0, column=0, columnspan=2,
                                                     sticky="w", padx=16, pady=(12, 6))

        # --- Rennen-Auswahl (unter Überschrift) --------------------------------
        self._race_selector: ctk.CTkOptionMenu | None = None

        # --- linke Kachel: VORSTART / START REIHE N -----------------------------
        # Zeigt den Vorstart-Countdown (PRESTART) ODER – nach dem Rennstart –
        # den Countdown bis zum Start der nächsten Startreihe (Variante A,
        # Kundenentscheidung 2026-09-03: anstatt des Vorstart-Countdowns,
        # nicht zusätzlich).
        self._prestart_frame = ctk.CTkFrame(self, fg_color=Cfg.COLOR_BG, corner_radius=8)
        self._prestart_frame.grid(row=2, column=0, sticky="nsew", padx=(16, 8), pady=6)
        self._prestart_title = ctk.CTkLabel(self._prestart_frame, text="VORSTART:",
                                            font=("Segoe UI", 13),
                                            text_color=Cfg.COLOR_ERROR)
        self._prestart_title.pack(pady=(8, 0))
        self._prestart_value = ctk.CTkLabel(self._prestart_frame, text="00:00:00",
                                            font=("Segoe UI", 34, "bold"),
                                            text_color=Cfg.COLOR_ERROR)
        self._prestart_value.pack(pady=2)
        self._prestart_bar = ctk.CTkProgressBar(self._prestart_frame,
                                                progress_color=Cfg.COLOR_PROGRESS)
        self._prestart_bar.pack(fill="x", padx=12, pady=(2, 10))

        # --- rechte Kachel: VERBLEIBENDE ZEIT ----------------------------------------
        self._race_frame = ctk.CTkFrame(self, fg_color=Cfg.COLOR_BG, corner_radius=8)
        self._race_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 16), pady=6)
        ctk.CTkLabel(self._race_frame, text="VERBLEIBENDE ZEIT:", font=("Segoe UI", 13),
                     text_color=Cfg.COLOR_ACTIVE).pack(pady=(8, 0))
        self._race_value = ctk.CTkLabel(self._race_frame, text="00:00",
                                        font=("Segoe UI", 34, "bold"),
                                        text_color=Cfg.COLOR_ACTIVE)
        self._race_value.pack(pady=2)
        self._race_bar = ctk.CTkProgressBar(self._race_frame,
                                            progress_color=Cfg.COLOR_ACTIVE)
        self._race_bar.pack(fill="x", padx=12, pady=(2, 10))

        # --- Buttons ------------------------------------------------------------------
        # PLAY-Button: Rennen starten (Countdown beginnt)
        self._start_button = ctk.CTkButton(self, text="▶  START", command=on_start_race,
                                           font=("Segoe UI", 16, "bold"),
                                           fg_color=Cfg.COLOR_ACTIVE,
                                           hover_color="#00A844",
                                           text_color=Cfg.COLOR_TEXT, height=40)
        self._start_button.grid(row=3, column=0, columnspan=2,
                                sticky="ew", padx=16, pady=(4, 12))

        # PAUSE/WEITER + NEUSTART: erst sichtbar nach Start
        self._pause_button = ctk.CTkButton(self, text="PAUSE", command=on_pause_toggle,
                                           font=("Segoe UI", 16, "bold"),
                                           fg_color=Cfg.COLOR_WARNING,
                                           hover_color="#FFB300",
                                           text_color="#1A1A1A", height=40)
        self._pause_button.grid(row=4, column=0, sticky="ew", padx=(16, 8), pady=(4, 12))
        self._reset_button = ctk.CTkButton(self, text="NEUSTART", command=on_reset,
                                           font=("Segoe UI", 16, "bold"),
                                           fg_color=Cfg.COLOR_ACTIVE,
                                           hover_color="#00A844",
                                           text_color=Cfg.COLOR_TEXT, height=40)
        self._reset_button.grid(row=4, column=1, sticky="ew", padx=(8, 16), pady=(4, 12))

        # Anfangszustand: PLAY sichtbar, PAUSE/NEUSTART versteckt
        self._pause_button.grid_remove()
        self._reset_button.grid_remove()

    def set_callbacks(self, on_pause_toggle: callable,
                      on_reset: callable,
                      on_start_race: callable | None = None) -> None:
        """Verdrahtet die Button-Callbacks (vom AppController nach dem Bau).

        Args:
            on_pause_toggle: Callback für PAUSE/WEITER.
            on_reset: Callback für NEUSTART.
            on_start_race: Callback für PLAY/START.
        """
        self._pause_button.configure(command=on_pause_toggle)
        self._reset_button.configure(command=on_reset)
        if on_start_race is not None:
            self._start_button.configure(command=on_start_race)

    # ------------------------------------------------------------------
    # Button-Zustand
    # ------------------------------------------------------------------

    def show_start_button(self) -> None:
        """Zeigt den PLAY-Button (Rennen geladen, wartet auf Start)."""
        self._start_button.grid()
        self._pause_button.grid_remove()
        self._reset_button.grid_remove()

    def show_race_buttons(self) -> None:
        """Zeigt PAUSE/NEUSTART, versteckt PLAY (Countdown läuft)."""
        self._start_button.grid_remove()
        self._pause_button.grid()
        self._reset_button.grid()

    def set_start_enabled(self, enabled: bool) -> None:
        """Aktiviert/deaktiviert den PLAY-Button (2026-09-03).

        Bei einem bereits beendeten Rennen (Ergebnisse wiederhergestellt)
        ist der Start nicht mehr möglich – der Button wird grau und inaktiv.

        Args:
            enabled: True = Start möglich, False = Start gesperrt.
        """
        if enabled:
            self._start_button.configure(
                state="normal", fg_color=Cfg.COLOR_ACTIVE,
                hover_color="#00A844")
        else:
            self._start_button.configure(
                state="disabled", fg_color=Cfg.COLOR_DISABLED,
                hover_color=Cfg.COLOR_DISABLED)

    # ------------------------------------------------------------------
    def set_prestart(self, seconds: float, total: float) -> None:
        """Aktualisiert die VORSTART-Kachel.

        Args:
            seconds: verbleibende Vorstartzeit in Sekunden.
            total: Gesamtdauer des Countdowns (für den Fortschrittsbalken).
        """
        self._prestart_title.configure(text="VORSTART:", text_color=Cfg.COLOR_ERROR)
        self._prestart_value.configure(text=format_countdown(seconds),
                                       text_color=Cfg.COLOR_ERROR)
        self._prestart_bar.configure(progress_color=Cfg.COLOR_PROGRESS)
        if total > 0:
            self._prestart_bar.set(1.0 - max(0.0, min(1.0, seconds / total)))

    def set_race_remaining(self, seconds: float, total: float) -> None:
        """Aktualisiert die VERBLEIBENDE-ZEIT-Kachel.

        Args:
            seconds: verbleibende Renndauer in Sekunden.
            total: Gesamtdauer des Rennens (für den Fortschrittsbalken).
        """
        self._race_value.configure(text=format_remaining(seconds))
        if total > 0:
            self._race_bar.set(max(0.0, min(1.0, seconds / total)))

    def set_start_line(self, line_number: int, seconds: float, total: float) -> None:
        """Zeigt den Startreihen-Countdown in der VORSTART-Kachel.

        Kundenentscheidung (2026-09-03): Der Countdown für die 2./x. Startreihe
        wird ANSTATT des Vorstart-Countdowns angezeigt (nicht zusätzlich).
        Der Vorstart-Countdown wird zu diesem Zeitpunkt nicht mehr benötigt.

        Args:
            line_number: Nummer der nächsten Startreihe (z. B. 2).
            seconds: verbleibende Zeit bis zum Startreihen-Start in Sekunden.
            total: Grid Time (Gesamtdauer des Startreihen-Countdowns).
        """
        self._prestart_title.configure(text=f"START REIHE {line_number}:",
                                       text_color=Cfg.COLOR_WARNING)
        self._prestart_value.configure(text=format_countdown(seconds),
                                       text_color=Cfg.COLOR_WARNING)
        self._prestart_bar.configure(progress_color=Cfg.COLOR_WARNING)
        if total > 0:
            self._prestart_bar.set(1.0 - max(0.0, min(1.0, seconds / total)))

    def set_pause_mode(self, paused: bool) -> None:
        """Schaltet den PAUSE/WEITER-Button um (Anzeige-Zustand).

        Args:
            paused: True → Countdown pausiert, Button zeigt "WEITER";
                    False → Countdown läuft, Button zeigt "PAUSE".
        """
        self._pause_button.configure(text="WEITER" if paused else "PAUSE")

    def set_pause_enabled(self, enabled: bool) -> None:
        """Aktiviert/deaktiviert den PAUSE/WEITER-Button.

        Nur im Countdown (Vorstart) bedienbar – während des Rennens und nach
        Rennende ist das Unterbrechen des Countdowns nicht mehr möglich.

        Args:
            enabled: True → Button bedienbar.
        """
        self._pause_button.configure(state="normal" if enabled else "disabled")

    def add_race_selector(self, values: list[str], command) -> None:
        """Fügt ein Rennen-Auswahl-Dropdown unter der Überschrift ein.

        Das Dropdown erscheint zwischen der Überschrift „Countdown-Anzeige"
        und den Countdown-Kacheln.

        Args:
            values: Dropdown-Einträge (z. B. "Rennen 2 (U18 Open)").
            command: Callback bei Auswahl (erhält den gewählten Text).
        """
        if self._race_selector is not None:
            self._race_selector.destroy()
        self._race_selector = ctk.CTkOptionMenu(
            self, values=values, command=command,
            width=260, fg_color=Cfg.COLOR_BG, button_color=Cfg.COLOR_PROGRESS,
            button_hover_color=Cfg.COLOR_ACTIVE, text_color=Cfg.COLOR_TEXT)
        self._race_selector.grid(row=1, column=0, columnspan=2,
                                 sticky="w", padx=16, pady=(0, 4))

    def set_race_selector_enabled(self, enabled: bool) -> None:
        """Aktiviert/deaktiviert das Rennen-Auswahl-Dropdown.

        Während eines laufenden Rennens (nicht RESET) darf der Benutzer
        das Rennen nicht wechseln.

        Args:
            enabled: True → Dropdown bedienbar.
        """
        if self._race_selector is not None:
            state = "normal" if enabled else "disabled"
            self._race_selector.configure(state=state)


# ---------------------------------------------------------------------------
# Bereich 3 links: Live-Tabelle (Rangliste)
# ---------------------------------------------------------------------------

@dataclass
class _TableRow:
    """Zwischengespeicherte Tabellenzeile (Wiederverwendung statt Rebuild).

    Beim periodischen Refresh (Polling) werden die Widgets nicht mehr zerstört
    und neu erstellt (das verursachte das Blinken), sondern nur noch bei
    echten Änderungen neu beschrieben.

    Attribute:
        frame: Zeilen-Frame im Scrollbereich der Tabelle.
        labels: die 8 Zellen-Labels (Platz, Runner, Klasse, Boot, Reihe,
            Runden, Letzte Runde, Gesamtzeit).
        status_label: Status-Label (WARTET / SPERRZEIT / GESTARTET / FERTIG).
        rendered: Snapshot der zuletzt gesetzten Werte (Text/Font/Farbe je
            Zelle) – nur Abweichungen lösen ein Widget-Update aus.
    """
    frame: ctk.CTkFrame
    labels: list[ctk.CTkLabel]
    status_label: ctk.CTkLabel
    rendered: dict = field(default_factory=dict)


class LiveTablePanel(ctk.CTkFrame):
    """Live-Rangliste: #, Runner, Klasse, Boot, Runden, Letzte Runde, Gesamtzeit, Status.

    - Sortierung: Runden absteigend, Gesamtzeit aufsteigend (vorläufig hier;
      die offizielle Wertung übernimmt später der ResultCalculator der Engine).
    - Führender (Platz 1) wird grün hervorgehoben (GUI-Description).
    - Status-Zelle zeigt "SPERRZEIT" rot, solange die Sperrzeit läuft (Q1).
    - Seit 2026-08-14: Zeilen werden wiederverwendet (kein Neu-Aufbau je Tick),
      damit der 50-ms-Refresh nicht mehr flackert.
    """

    # Spaltenbreiten in Pixeln (Reihenfolge = Anzeige)
    COLUMNS = [("#", 44), ("Runner", 150), ("Klasse", 70), ("Boot", 60),
               ("Reihe", 50), ("Runden", 70), ("Letzte Runde", 110),
               ("Geschw.", 110), ("Gesamtzeit", 110), ("Status", 130)]

    # Maximale Zeichenlänge für den Runner-Namen (fixe Spaltenbreite,
    # zu lange Namen werden abgeschnitten – Kundenanforderung 2026-09-03)
    RUNNER_MAX_CHARS = 18

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        """LiveTablePanel initialisieren."""
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        ctk.CTkLabel(self, text="Live-Tabelle (Rangliste)", font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).pack(anchor="w", padx=16, pady=(12, 6))

        # Kopfzeile der Tabelle (fixiert)
        header = ctk.CTkFrame(self, fg_color=Cfg.COLOR_BG, corner_radius=0)
        header.pack(fill="x", padx=12, pady=(0, 2))
        for col, (label, width) in enumerate(self.COLUMNS):
            ctk.CTkLabel(header, text=label, font=("Segoe UI", 12, "bold"),
                         text_color=Cfg.COLOR_TEXT_SECONDARY, width=width,
                         anchor="w").grid(row=0, column=col, padx=2, pady=4)

        # Scrollbarer Tabellenbereich
        self._body = ctk.CTkScrollableFrame(self, fg_color=Cfg.COLOR_BG,
                                            corner_radius=6)
        self._body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        # Runner-Spalte: FIXE Breite (kein Dehnen) – zu lange Namen werden
        # abgeschnitten (Kundenanforderung 2026-09-03).
        self._body.grid_columnconfigure(1, weight=0)

        # Wiederverwendete Zeilen: boot_key → _TableRow (gegen Blinken)
        self._rows: dict[str, _TableRow] = {}

        # Streckenlängen des aktuellen Rennens (für die Geschw.-Berechnung)
        self._lap1_length_m: int = 0
        self._standard_lap_length_m: int = 0

    # ------------------------------------------------------------------
    def set_lap_lengths(self, lap1_length_m: int,
                        standard_lap_length_m: int) -> None:
        """Setzt die Streckenlängen des aktuellen Rennens (für Geschw.).

        Args:
            lap1_length_m: Streckenlänge der 1. Runde in Metern.
            standard_lap_length_m: Streckenlänge der Standardrunde in Metern.
        """
        self._lap1_length_m = lap1_length_m
        self._standard_lap_length_m = standard_lap_length_m

    def update_boats(self, boats: dict[str, BoatState], now: datetime) -> None:
        """Aktualisiert die Rangliste aus den aktuellen Boots-Zuständen.

        Vorhandene Zeilen werden wiederverwendet und nur bei echten
        Änderungen neu beschrieben – das verhindert das Blinken beim
        Polling-Refresh (kein destroy() + Neuaufbau mehr).

        Args:
            boats: boot_key → BoatState (alle Starter des Rennens).
            now: aktueller Zeitpunkt (für die Sperrzeit-Anzeige).
        """
        # Sortieren: 1. Rundenzahl absteigend, 2. Gesamtzeit aufsteigend
        ranked = sorted(boats.values(),
                        key=lambda b: (-b.laps_count, b.total_time))
        active_keys = {b.starter.boot_key for b in ranked}

        # Verwaiste Zeilen entfernen (Boot nicht mehr dabei, z. B. Rennen-Wechsel)
        for key in list(self._rows):
            if key not in active_keys:
                self._rows[key].frame.destroy()
                del self._rows[key]

        # Zeilen aktualisieren bzw. bei neuen Boots erstmalig anlegen
        for place, state in enumerate(ranked, start=1):
            row = self._rows.get(state.starter.boot_key)
            if row is None:
                row = self._add_row(state)
                self._rows[state.starter.boot_key] = row
            self._refresh_row(row, place, state, now)

    def _add_row(self, state: BoatState) -> _TableRow:
        """Legt eine Tabellenzeile für einen BoatState einmalig an.

        Args:
            state: Laufzeit-Zustand des Boots.

        Returns:
            Die neu angelegte, noch leere Zeile (Inhalte folgen im Refresh).
        """
        frame = ctk.CTkFrame(self._body, fg_color=Cfg.COLOR_PANEL, corner_radius=4)
        labels: list[ctk.CTkLabel] = []
        for col, (_, width) in enumerate(self.COLUMNS[:9]):
            label = ctk.CTkLabel(frame, text="", font=("Segoe UI", 13),
                                 width=width, anchor="w")
            label.grid(row=0, column=col, padx=2, pady=3)
            labels.append(label)

        status_label = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12, "bold"),
                                    width=self.COLUMNS[9][1], anchor="w")
        status_label.grid(row=0, column=9, padx=2, pady=3)

        return _TableRow(frame=frame, labels=labels, status_label=status_label)

    def _refresh_row(self, row: _TableRow, place: int, state: BoatState,
                     now: datetime) -> None:
        """Schreibt nur die tatsächlich geänderten Werte in eine Zeile.

        Args:
            row: die wiederzuverwendende Tabellenzeile.
            place: aktuelle Platzierung (1 = Führender, grün markiert).
            state: Laufzeit-Zustand des Boots.
            now: aktueller Zeitpunkt (Sperrzeit-Anzeige).
        """
        is_leader = place == 1 and state.laps_count > 0
        row_bg = "#123B21" if is_leader else Cfg.COLOR_PANEL

        # Zeilen-Hintergrund (Leader-Wechsel) nur bei Änderung setzen
        if row.rendered.get("bg") != row_bg:
            row.frame.configure(fg_color=row_bg)
            row.rendered["bg"] = row_bg

        # Zellen-Inhalte: nur bei Änderung von Text/Font/Farbe neu setzen
        runner = self._truncate_runner(state.starter.display_name)
        cells = [
            str(place),
            runner,
            state.starter.klasse,
            state.starter.boot_key,
            str(state.starter.startreihe) if state.starter.startreihe > 0 else "–",
            str(state.laps_count),
            format_duration(state.last_lap),
            self._format_speed(state),
            format_duration(state.total_time),
        ]
        for col, text in enumerate(cells):
            font = ("Segoe UI", 13, "bold") if col in (0, 8) else ("Segoe UI", 13)
            color = Cfg.COLOR_ACTIVE if is_leader else Cfg.COLOR_TEXT
            rendered = row.rendered.get(f"cell_{col}")
            if rendered != (text, font, color):
                row.labels[col].configure(text=text, font=font, text_color=color)
                row.rendered[f"cell_{col}"] = (text, font, color)

        # Status-Zelle: Startstatus + Sperrzeit + Rennende-Status
        status_text = ""
        status_color = Cfg.COLOR_TEXT
        # Variante A: Boot noch nicht gestartet (Startreihe noch nicht dran)
        if state.start_time is not None and now < state.start_time:
            status_text = "WARTET"
            status_color = Cfg.COLOR_WARNING
        elif state.lockout_until is not None and state.lockout_until > now:
            remaining_s = (state.lockout_until - now).total_seconds()
            status_text = f"SPERRZEIT ({remaining_s:.0f}s)"
            status_color = Cfg.COLOR_ERROR
        elif state.finished_at is not None:
            status_text = "FERTIG"
            status_color = Cfg.COLOR_ACTIVE
        elif state.laps_count > 0:
            status_text = "GESTARTET"
            status_color = Cfg.COLOR_ACTIVE

        if row.rendered.get("status") != (status_text, status_color):
            row.status_label.configure(text=status_text, text_color=status_color)
            row.rendered["status"] = (status_text, status_color)

        # Position im Raster neu setzen (Sortierung) – Layout-Operation, kein Rebuild
        row.frame.grid(row=place - 1, column=0, sticky="ew", pady=1)

    def _truncate_runner(self, name: str) -> str:
        """Kürzt einen Runner-Namen auf RUNNER_MAX_CHARS (mit '…').

        Kundenanforderung (2026-09-03): Die Runner-Spalte hat eine fixe
        Breite; zu lange Namen werden abgeschnitten.

        Args:
            name: vollständiger Runner-Name.

        Returns:
            Gekürzter Name (max. RUNNER_MAX_CHARS Zeichen) oder der
            unveränderte Name, wenn er kurz genug ist.
        """
        if len(name) > self.RUNNER_MAX_CHARS:
            return name[:self.RUNNER_MAX_CHARS - 1] + "…"
        return name

    def _format_speed(self, state: BoatState) -> str:
        """Formatiert die Geschw.-Zelle: 'km/h letzte Runde / km/h gesamt'.

        Kundenanforderung (2026-09-03): Die Zelle zeigt zwei Werte getrennt
        durch "/":
            a) km/h der letzten Runde (Strecke letzter Runde / Rundenzeit)
            b) km/h gesamt (Gesamtstrecke / Zeit bis zum letzten Passieren)

        Fehlt ein Wert (noch keine Runde), wird "–" angezeigt.

        Args:
            state: Laufzeit-Zustand des Boots.

        Returns:
            Formatierter String, z. B. "58.3/56.1" oder "–/–".
        """
        last = state.speed_last_lap(self._lap1_length_m,
                                    self._standard_lap_length_m)
        total = state.speed_total(self._lap1_length_m,
                                  self._standard_lap_length_m)
        a = f"{last:.1f}" if last is not None else "–"
        b = f"{total:.1f}" if total is not None else "–"
        return f"{a}/{b}"


# ---------------------------------------------------------------------------
# Bereich 3 rechts: Hotkey-Panel (virtuelle Tastatur)
# ---------------------------------------------------------------------------

class HotkeyPanel(ctk.CTkFrame):
    """Tastaturbedienung: virtuelle Tastatur A–Z (26 Buchstaben).

    Aktive Boot-Keys (aus der Starterliste) werden grün dargestellt und
    lösen beim Klick den Hotkey-Callback aus – als Bediener-Simulation
    solange die echte keyboard-Erfassung (InputHandler) noch fehlt.

    Hinweis: Der Ergebnis-Export ist im HeaderPanel (neben "Daten
    aktualisieren") – nicht mehr hier.
    """

    def __init__(self, parent: ctk.CTkBaseClass,
                 on_key: callable | None = None) -> None:
        """HotkeyPanel initialisieren.

        Args:
            parent: Eltern-Widget.
            on_key: Callback(boot_key) bei Klick auf einen aktiven Key.
        """
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        self._on_key = on_key
        self._active_keys: set[str] = set()
        self._started_keys: set[str] = set()
        self._finished_keys: set[str] = set()   # Boot-Keys beendeter Klassen
        self._buttons: dict[str, ctk.CTkButton] = {}

        # Überschrift mit Hotkey-Status (Admin-Rechte, 2026-09-03)
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(title_row, text="Tastaturbedienung (Hotkeys)",
                     font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).pack(side="left")
        self._status_label = ctk.CTkLabel(title_row, text="",
                                          font=("Segoe UI", 11, "bold"),
                                          text_color=Cfg.COLOR_TEXT_SECONDARY)
        self._status_label.pack(side="left", padx=10)

        # Tastenraster A–Z in 3 Reihen (9 / 9 / 8 – wie im GUI-Design)
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(padx=16, pady=(0, 12))
        letters = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
        for idx, letter in enumerate(letters):
            row, col = divmod(idx, 9)
            self._buttons[letter] = ctk.CTkButton(
                grid_frame, text=letter, width=40, height=36, corner_radius=6,
                font=("Segoe UI", 13, "bold"),
                fg_color=Cfg.COLOR_BG, hover_color=Cfg.COLOR_BG,
                text_color=Cfg.COLOR_TEXT_SECONDARY,
                command=lambda k=letter: self._press(k))
            self._buttons[letter].grid(row=row, column=col, padx=2, pady=2)

    # ------------------------------------------------------------------
    def set_starters(self, starters: list[Starter]) -> None:
        """Markiert die aktiven Boot-Keys (aus der Starterliste).

        Zuerst sind alle Keys inaktiv (grau) – sie werden erst aktiv (grün),
        wenn der jeweilige Starter gestartet ist (set_started_keys).

        Args:
            starters: aktive Starter des gewählten Rennens.
        """
        self._active_keys = {s.boot_key for s in starters}
        self._started_keys: set[str] = set()
        self._finished_keys: set[str] = set()
        self._refresh_buttons()

    def set_started_keys(self, started_keys: set[str]) -> None:
        """Aktiviert Hotkeys für Boote, die bereits gestartet sind.

        Kundenentscheidung (2026-09-03): Ein Hotkey ist nur aktiv (grün),
        wenn der jeweilige Starter gestartet ist (seine Startreihe aktiv).
        Nicht gestartete Boote sind grau und inaktiv.

        Args:
            started_keys: Menge der Boot-Keys, deren Startreihe gestartet ist.
        """
        if started_keys == self._started_keys:
            return  # kein Change → kein UI-Update
        self._started_keys = started_keys
        self._refresh_buttons()

    def set_finished_keys(self, finished_keys: set[str]) -> None:
        """Deaktiviert Hotkeys für Boote beendeter (CLOSED) Klassen.

        Kundenanforderung (2026-09-03): Wenn eine Klasse beendet wird, werden
        die Hotkeys der Boote dieser Klasse inaktiv (grau) – auch wenn sie
        gestartet waren.

        Args:
            finished_keys: Menge der Boot-Keys, deren Klasse beendet ist.
        """
        if finished_keys == self._finished_keys:
            return  # kein Change → kein UI-Update
        self._finished_keys = finished_keys
        self._refresh_buttons()

    def set_hotkey_status(self, text: str, active: bool) -> None:
        """Zeigt den Hotkey-Status (Admin-Rechte) neben der Überschrift.

        Args:
            text: Statustext (z. B. "Hotkeys aktiv" / "Hotkeys inaktiv").
            active: True → grün, False → grau/rot.
        """
        color = Cfg.COLOR_ACTIVE if active else Cfg.COLOR_TEXT_SECONDARY
        self._status_label.configure(text=text, text_color=color)

    def _refresh_buttons(self) -> None:
        """Aktualisiert Button-Zustände basierend auf active/started/finished Keys."""
        for key, button in self._buttons.items():
            if key in self._finished_keys:
                # Klasse beendet (CLOSED): inaktiv (grau), auch wenn gestartet
                button.configure(fg_color="#3A3A3A",
                                 hover_color="#3A3A3A",
                                 text_color="#666666",
                                 state="disabled")
            elif key in self._started_keys:
                # Gestartet: grün aktiv
                button.configure(fg_color=Cfg.COLOR_ACTIVE,
                                 hover_color="#00A844",
                                 text_color=Cfg.COLOR_TEXT,
                                 state="normal")
            elif key in self._active_keys:
                # Starter vorhanden, aber noch nicht gestartet: grau inaktiv
                button.configure(fg_color="#3A3A3A",
                                 hover_color="#3A3A3A",
                                 text_color="#666666",
                                 state="disabled")
            else:
                # Kein Starter: dunkelgrau
                button.configure(fg_color=Cfg.COLOR_BG,
                                 hover_color=Cfg.COLOR_BG,
                                 text_color=Cfg.COLOR_TEXT_SECONDARY,
                                 state="normal")

    def set_on_key(self, on_key: callable | None) -> None:
        """Setzt den Callback für Tastendrücke (wird vom Controller verdrahtet).

        Args:
            on_key: Callback(boot_key) bei aktivem Key.
        """
        self._on_key = on_key

    def _press(self, key: str) -> None:
        """Interner Klick-Handler: ruft den Callback nur bei gestarteten Keys auf.

        Args:
            key: gedrückter Buchstabe.
        """
        if key in self._started_keys and self._on_key is not None:
            self._on_key(key)


# ---------------------------------------------------------------------------
# Bereich 4 links: Ereignis-Feed (Logs)
# ---------------------------------------------------------------------------

class LogFeedPanel(ctk.CTkFrame):
    """Ereignis-Feed: chronologischer, scrollbarer Log-Bereich.

    Format: HH:MM:SS Beschreibung (Monospace-Optik). Ungültige Ereignisse
    (Sperrzeit) werden rot hervorgehoben (Pflichtenheft §5.2).

    Die Höhe wird über `visible_lines` gesteuert (Standard: 7 Zeilen).
    """

    def __init__(self, parent: ctk.CTkBaseClass,
                 visible_lines: int = 7) -> None:
        """LogFeedPanel initialisieren.

        Args:
            parent: Eltern-Widget.
            visible_lines: Anzahl der sichtbaren Zeilen (danach Scrollen).
        """
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        ctk.CTkLabel(self, text="Ereignis-Feed (Logs)", font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).pack(anchor="w", padx=16, pady=(12, 6))

        # Höhe berechnen: visible_lines × Zeilenhohe (~18px) + Innen-Padding
        line_height = 18
        textbox_height = visible_lines * line_height + 20

        self._textbox = ctk.CTkTextbox(self, fg_color=Cfg.COLOR_BG,
                                       text_color=Cfg.COLOR_TEXT,
                                       font=("Consolas", 12), wrap="none",
                                       state="disabled", height=textbox_height)
        self._textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        # Tag für ungültige Ereignisse (Sperrzeit) – rot
        self._textbox.tag_config("invalid", foreground=Cfg.COLOR_ERROR)

    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Leert den gesamten Feed."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")

    def log(self, message: str, timestamp: datetime | None = None,
            valid: bool = True) -> None:
        """Fügt einen Log-Eintrag hinzu (HH:MM:SS Beschreibung).

        Args:
            message: Beschreibung des Ereignisses.
            timestamp: Ereigniszeitpunkt (None → jetzt).
            valid: False → Eintrag rot (ungültige Eingabe).
        """
        if timestamp is None:
            timestamp = datetime.now()
        line = f"{timestamp.strftime('%H:%M:%S')} {message}\n"
        tag = None if valid else "invalid"
        self._textbox.configure(state="normal")
        self._textbox.insert("end", line, tag)
        self._textbox.see("end")
        self._textbox.configure(state="disabled")


# ---------------------------------------------------------------------------
# Bereich 4 rechts oben: Rennende-Status
# ---------------------------------------------------------------------------

class RaceEndStatusPanel(ctk.CTkFrame):
    """Rennende-Status: eine Statuszeile pro Klasse (WARTEND / FERTIG).

    Zustände kommen aus RaceClass.finish_state (ClassFinishTracker der Engine).
    Farben: WAITING = gelb, CLOSED = grün.

    Jede Klasse hat einen "Beenden"-Button (Kundenentscheidung 2026-09-03):
    Der Bediener beendet eine Klasse manuell, wenn die Renndauer abgelaufen
    ist. Beim Beenden werden alle Boote der Klasse als fertig markiert.
    """

    # Zustand → Anzeigetext + Farbe
    STATE_STYLE = {
        "WAITING": ("WARTEND", Cfg.COLOR_WARNING),
        "CLOSED": ("FERTIG", Cfg.COLOR_ACTIVE),
    }

    def __init__(self, parent: ctk.CTkBaseClass) -> None:
        """RaceEndStatusPanel initialisieren."""
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        ctk.CTkLabel(self, text="Rennende-Status", font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).pack(anchor="w", padx=16, pady=(12, 6))

        self._rows: dict[str, ctk.CTkLabel] = {}   # Klassenname → Wert-Label
        self._row_frames: list[ctk.CTkFrame] = []   # Zeilen-Frames (für korrektes Zerstören)
        self._finish_buttons: dict[str, ctk.CTkButton] = {}  # Klassenname → Beenden-Button
        self._on_finish_class: callable | None = None
        self._race_over: bool = False   # Rennzeit abgelaufen → Beenden aktivierbar
        self._info = ctk.CTkLabel(self, text="Keine Klassen geladen",
                                  font=("Segoe UI", 12),
                                  text_color=Cfg.COLOR_TEXT_SECONDARY)
        self._info.pack(anchor="w", padx=16, pady=2)

    # ------------------------------------------------------------------
    def set_race_over(self, race_over: bool) -> None:
        """Aktiviert/deaktiviert die 'Beenden'-Buttons (Rennzeit abgelaufen).

        Kundenanforderung (2026-09-03): Der "Beenden"-Button ist erst aktiv,
        wenn die Rennzeit abgelaufen ist (Phase FINISHING). Vorher ist er
        sichtbar, aber inaktiv (grau).

        Args:
            race_over: True, wenn die Rennzeit abgelaufen ist.
        """
        if race_over == self._race_over:
            return
        self._race_over = race_over
        # Buttons je Klasse aktualisieren (nur wenn Klassen geladen sind)
        for klasse, button in self._finish_buttons.items():
            self._apply_finish_button_state(klasse, button)

    # ------------------------------------------------------------------
    def set_on_finish_class(self, on_finish_class: callable | None) -> None:
        """Setzt den Callback für die 'Beenden'-Buttons.

        Args:
            on_finish_class: Callback(klasse) beim Klick auf "Beenden".
        """
        self._on_finish_class = on_finish_class

    def update_classes(self, classes: dict[str, RaceClass]) -> None:
        """Baut die Statuszeilen für alle Klassen komplett neu auf.

        WICHTIG: Zerstört alle alten Row-Frames (nicht nur die Labels),
        damit beim Rennen-Wechsel keine verwaisten Klassen-Zeilen
        im Panel verbleiben (Bugfix: akkumulierende Klassen).

        Args:
            classes: Klassenname → RaceClass (mit finish_state).
        """
        # Alle alten Zeilen-Frames zerstört (inkl. Kinder-Labels)
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames = []
        self._rows = {}
        self._finish_buttons = {}

        self._info.destroy()
        self._info = ctk.CTkLabel(self, text="Keine Klassen geladen",
                                  font=("Segoe UI", 12),
                                  text_color=Cfg.COLOR_TEXT_SECONDARY)
        # Nur packen, wenn keine Klassen vorhanden sind – sonst entsteht eine
        # unnötige Leerzeile unter der Überschrift (Kundenanforderung 2026-09-03).
        if not classes:
            self._info.pack(anchor="w", padx=16, pady=2)

        for klasse in sorted(classes):
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=1)
            ctk.CTkLabel(row, text=f"Klasse {klasse}:", font=("Segoe UI", 13),
                         text_color=Cfg.COLOR_TEXT_SECONDARY).pack(side="left")
            value_label = ctk.CTkLabel(row, text="WARTEND", font=("Segoe UI", 13, "bold"),
                                       text_color=Cfg.COLOR_WARNING)
            value_label.pack(side="left", padx=8)
            # Beenden-Button (manuelle Klassen-Beendigung, 2026-09-03)
            finish_button = ctk.CTkButton(
                row, text="Beenden", width=80, height=24, corner_radius=6,
                font=("Segoe UI", 11, "bold"),
                fg_color=Cfg.COLOR_WARNING, hover_color="#FFB300",
                text_color="#1A1A1A",
                command=lambda k=klasse: self._press_finish(k))
            finish_button.pack(side="right", padx=4)
            self._row_frames.append(row)
            self._rows[klasse] = value_label
            self._finish_buttons[klasse] = finish_button
        self._refresh(classes)

    def _press_finish(self, klasse: str) -> None:
        """Interner Klick-Handler für den 'Beenden'-Button.

        Args:
            klasse: Klassenname der zu beendenden Klasse.
        """
        if self._on_finish_class is not None:
            self._on_finish_class(klasse)

    def _apply_finish_button_state(self, klasse: str,
                                   button: ctk.CTkButton) -> None:
        """Setzt den Zustand eines 'Beenden'-Buttons.

        Kundenanforderung (2026-09-03): Der Button ist erst aktiv, wenn die
        Rennzeit abgelaufen ist (`_race_over`) UND die Klasse noch nicht
        CLOSED ist. Sonst ist er sichtbar, aber inaktiv (grau).

        Args:
            klasse: Klassenname (für den CLOSED-Zustand).
            button: der zu aktualisierende Button.
        """
        if self._race_over:
            # Aktiv nur, wenn die Klasse noch nicht CLOSED ist
            if self._is_closed(klasse):
                button.configure(state="disabled",
                                 fg_color="#3A3A3A", text_color="#666666")
            else:
                button.configure(state="normal",
                                 fg_color=Cfg.COLOR_WARNING,
                                 text_color="#1A1A1A")
        else:
            button.configure(state="disabled",
                             fg_color="#3A3A3A", text_color="#666666")

    def _is_closed(self, klasse: str) -> bool:
        """True, wenn die Klasse CLOSED ist (über das aktuelle Label).

        Args:
            klasse: Klassenname.

        Returns:
            True, wenn die Klasse beendet (CLOSED) ist.
        """
        label = self._rows.get(klasse)
        if label is None:
            return False
        return label.cget("text") == "FERTIG"

    def _refresh(self, classes: dict[str, RaceClass]) -> None:
        """Aktualisiert die Farben/ Texte der Statuszeilen.

        Args:
            classes: aktuelle Klassen-Zustände.
        """
        for klasse, state in classes.items():
            label = self._rows.get(klasse)
            if label is None:
                continue
            text, color = self.STATE_STYLE.get(state.finish_state,
                                               ("WARTEND", Cfg.COLOR_WARNING))
            label.configure(text=text, text_color=color)
            # Beenden-Button: aktiv nur wenn Rennzeit abgelaufen + nicht CLOSED
            button = self._finish_buttons.get(klasse)
            if button is not None:
                self._apply_finish_button_state(klasse, button)

    def set_finish_states(self, finish_states: dict[str, str]) -> None:
        """Setzt die Zustände direkt über ein Dict (Klasse → Zustand).

        Args:
            finish_states: z. B. {"U18": "WAITING", "DAMEN": "CLOSED"}.
        """
        classes = {name: RaceClass(name=name, finish_state=state)
                   for name, state in finish_states.items()}
        self.update_classes(classes)

    def update_states(self, finish_states: dict[str, str]) -> None:
        """Schlankes Tick-Update: nur Text/Farbe der bestehenden Zeilen ändern.

        Baut die Widgets NICHT neu (für den 50-ms-Takt). Zeilen für unbekannte
        Klassen bleiben unverändert.

        Args:
            finish_states: Klasse → Zustand ("WAITING"/"CLOSED").
        """
        for klasse, state in finish_states.items():
            label = self._rows.get(klasse)
            if label is None:
                continue
            text, color = self.STATE_STYLE.get(state,
                                               ("WARTEND", Cfg.COLOR_WARNING))
            label.configure(text=text, text_color=color)
            button = self._finish_buttons.get(klasse)
            if button is not None:
                self._apply_finish_button_state(klasse, button)


# ---------------------------------------------------------------------------
# Bereich 4 rechts unten: Manuelle Rundenkorrektur
# ---------------------------------------------------------------------------

class ManualCorrectionPanel(ctk.CTkFrame):
    """Manuelle Rundenkorrektur: Boot-Auswahl + Button „+1 Runde“.

    Nur „+1“ ist im MVP vorgesehen (Pflichtenheft §6); −1 bleibt offen (Q6).
    """

    def __init__(self, parent: ctk.CTkBaseClass,
                 on_correct: callable | None = None) -> None:
        """ManualCorrectionPanel initialisieren.

        Args:
            parent: Eltern-Widget.
            on_correct: Callback(boot_key) für die Korrektur.
        """
        super().__init__(parent, fg_color=Cfg.COLOR_PANEL, corner_radius=10)
        self._on_correct = on_correct

        ctk.CTkLabel(self, text="Manuell +1 Runde", font=("Segoe UI", 16, "bold"),
                     text_color=Cfg.COLOR_TEXT).pack(anchor="w", padx=16, pady=(12, 6))

        self._menu = ctk.CTkOptionMenu(self, values=["Kein Boot gewählt"],
                                       fg_color=Cfg.COLOR_BG,
                                       button_color=Cfg.COLOR_PROGRESS,
                                       button_hover_color=Cfg.COLOR_ACTIVE,
                                       text_color=Cfg.COLOR_TEXT)
        self._menu.pack(fill="x", padx=16, pady=(0, 6))

        self._button = ctk.CTkButton(self, text="+1 RUNDE", font=("Segoe UI", 14, "bold"),
                                     fg_color=Cfg.COLOR_PROGRESS,
                                     hover_color="#1B5FC0",
                                     text_color=Cfg.COLOR_TEXT, height=36,
                                     command=self._do_correct)
        self._button.pack(fill="x", padx=16, pady=(0, 12))

    # ------------------------------------------------------------------
    def set_boats(self, boats: dict[str, BoatState]) -> None:
        """Befüllt das Dropdown mit den Boots (Key + Name).

        Args:
            boats: boot_key → BoatState.
        """
        values = [f"{s.starter.boot_key} – {s.starter.display_name}"
                  for s in boats.values()]
        self._menu.configure(values=values)
        if values:
            self._menu.set(values[0])

    def set_on_correct(self, on_correct: callable | None) -> None:
        """Setzt den Korrektur-Callback (wird vom Controller verdrahtet).

        Args:
            on_correct: Callback(boot_key) für die +1-Korrektur.
        """
        self._on_correct = on_correct

    def _do_correct(self) -> None:
        """Interner Button-Handler: Callback mit Boot-Key aufrufen."""
        choice = self._menu.get()
        boot_key = choice.split(" – ")[0].strip() if " – " in choice else ""
        if boot_key and self._on_correct is not None:
            self._on_correct(boot_key)
