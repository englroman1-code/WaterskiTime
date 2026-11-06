# RELEASE_LOG.md – Release-Protokoll

> **Vorgehen (verbindlich, siehe AGENTS.md Regel 5):**
> 1. Versionsnummer in `python/config/version.py` erhöhen
>    (danach `python scripts/bump_version.py X.Y.Z` für die `VERSION`-Datei)
> 2. Inhalt von `ACTIVE_CHANGES.md` **mit Versionsnummer + Datum** hierher
>    übernehmen (neuester Release **zuoberst**)
> 3. `ACTIVE_CHANGES.md` danach leeren (nur Kopfzeile behalten)
> 4. `PROJECT_LOG.md` → Release-Protokoll

---

## v0.3.0 – 2026-11-06 (Release-Kandidat)

**Status:** Release-Kandidat. Der direkte Excel-Start aus der App ist noch
nicht freigegeben (offener Punkt 1: Python ruft `mdlEngl` auf, die aktuelle
Vorlage nutzt `mdl_Engl_Export`). Bis zur Korrektur `IMPORT.json` in Excel
manuell über `ExportExpRangesToJSON` erzeugen und neben die `.exe` legen.

### Neuerungen / Änderungen

## JsonRaceStore: Fuzzy-Matching entfernt, direkte FLD_/CODE-Key-Matches

**Datei:** `python/excel/json_race_store.py`
**Änderung:** Kompletter Umbau der Feld-Erkennung in JsonRaceStore.

**Vorher:** Fuzzy-Matching mit `_normalize_key()` (Newlines, Umlaute,
Klammern, trailing Spaces entfernen) + Substring-Matching für INFO-Sektion.

**Nachher:** Direkte Key-Matches mit den neuen IT-amerikanischen Feldnamen:
- INFO: `CODE`-Spalte (`PAR_EVENT`, `PAR_DATE`, `PAR_ORG`)
- Races: `FLD_RACE`, `FLD_RACEDUR`, `FLD_STARTINT`, `FLD_GRIDTIME`, `FLD_ROUND`, `FLD_ROUND1`, `FLD_STARTTIME`
- Starter: `FLD_BOATNR`, `FLD_CLASS`, `FLD_TEAM`, `FLD_SKIER`, `FLD_DRIVER`, `FLD_OBSERVER`, `FLC_CLUB`, `FLD_FED`, `FLD_HOTKEY`, `FLD_RACE`, `FLD_LINE`

Entfernt: `_normalize_key()`, `_find_key()`, `_get_int/float/str()` mit
fuzzy-Matching. Neue `_get_int/float/str()` sind statische Direkt-Lookups.

**Tests:** 198/198 grün. Test-Fixtures auf neue Feldnamen umgestellt.
`test_fuzzy_key_matching` → `test_direct_key_matching` umbenannt.

## Ergebnis-Export: Dateinamenformat geändert

**Datei:** `python/gui/main_window.py`
**Änderung:** Export-Dateiname von `Ergebnis_AlleRennen_YYYYMMDD_HHMMSS.json`
auf `RESULT_YYYYMMDD_HHMMSS.json` geändert.

**Tests:** 198/198 grün. Test-Referenzen in `test_gui_smoke.py` aktualisiert.

## Crash-Recovery gehärtet (2026-11-06)

**Dateien:** `python/core/race_state_manager.py`, `python/core/race_engine.py`,
`python/gui/main_window.py`, `python/config/app_config.py`

**Änderung:**
- `race_state.json` enthält jetzt `_version = 2`, `_saved_at` (mit Zeitzone)
  und `_source_fingerprint` (Pfad + Größe + mtime der Datenquelle).
- Beim Laden werden States verworfen, die älter als 12 Stunden sind, eine
  andere Rennnummer haben oder zu einer anderen Datenquelle gehören.
- Vollständige Runden (Start/Ende) werden persistiert und exakt
  wiederhergestellt. Keine synthetische Mittelung von Rundenzeiten mehr.
- Schreiben erfolgt atomar (Temp-Datei + `os.replace`); unveränderte States
  werden nur alle 30 s (Heartbeat) erneut geschrieben.
- Laufzeitdateien (`race_state.json`, `blackbox.log`, `gui_startup.log`,
  Exporte) liegen neben der `.exe` (Entwicklung: Projekt-Root).

**Tests:** 217/217 grün (neue Tests für Schema, Alter, Rennnummer,
Fingerprint, Lap-Details, Save-Drosselung).

## Robustheit / Datenqualität (2026-11-06)

**Dateien:** `python/excel/json_race_store.py`, `python/core/data_validator.py`,
`python/logger/blackbox.py`, `python/excel/json_result_writer.py`,
`python/core/models.py`, `python/main.py`, `requirements.txt`

**Änderung:**
- Altes `IMPORT.json`-Format (ohne `FLD_`/`CODE`) wird mit klarer Meldung
  abgelehnt, statt still 0 Rennen/0 Starter zu laden.
- `DataValidator` prüft `startreihe > 0`.
- Blackbox ruft nach jedem Eintrag `fsync()` auf (Beweisfunktion auch bei
  Stromausfall).
- `START`/`STARTLINE`-Events tragen `Race`/`Line` im Renn-Log; der
  Ergebnis-Writer nutzt dieses Detail.
- `openpyxl==3.1.2` in `requirements.txt` ergänzt (Analyse-Skripte).

**Tests:** 217/217 grün.

## Doku aktualisiert (2026-11-06)

**Dateien:** `Manual.md`, `BEDIENUNGSANLEITUNG.md`,
`python/excel/vba_macro_caller.py`, `python/excel/json_result_writer.py`

**Änderung:**
- `Manual.md`: Dateikonvention (`RESULT_*` statt `Ergebnis_AlleRennen_*`),
  Crash-Recovery-Details, Event-Types, Laufzeitdateien, offene Punkte.
- Neue `BEDIENUNGSANLEITUNG.md` (Kurzfassung für den Kunden).
- Docstrings: `MainJsonImport` statt `ImportResultsToExcel`; VBOM-Trust ist
  nicht nötig, Makro-Ausführung schon. Hinweis auf offenen Modulnamen
  `mdl_Engl_Export` vs. `mdlEngl`.

**Verifikation:** 217/217 Tests grün (11.10s). .exe-Build siehe
`dist/Wasserski-Zeitnehmung.exe`.

---

## v0.2.0 – 2026-09-04

**Erstes offizielles Release.** Übernahme des gesamten Entwicklungsstands seit
Projektstart (2026-08-12) aus `ACTIVE_CHANGES.md`. Die App umfasst: Excel/JSON
Datenhaltung, RaceEngine (Zustandsmaschine), GUI (CustomTkinter), Blackbox-Log,
systemweite Hotkeys, Ergebnis-Export, Platzierung pro Klasse und PyInstaller-Build.

### Neuerungen / Änderungen

## 2026-09-04 – Platzierung pro Klasse (Bugfix: jede Klasse hat einen Ersten)

### Hintergrund
Kunden-Feedback (2026-09-04): Im Export wurde die Platzierung **global über
alle Boote** vergeben. Dadurch war z. B. Boot 172 (Klasse Herren) mit Platz 2
markiert, obwohl es in seiner Klasse der Erste ist. **In jeder Klasse gibt es
einen Ersten, Zweiten, …**

### Fix
`ResultCalculator.compute_results()` vergibt die Platzierung jetzt **pro
Klasse**: Die Sortierung (Runden absteigend, Gesamtzeit aufsteigend) bleibt
innerhalb jeder Klasse gleich, aber die Platznummern starten in jeder Klasse
wieder bei 1.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/result_calculator.py` | `compute_results()`: Platzierung pro Klasse (Gruppierung nach `starter.klasse`, Platznummern je Klasse ab 1) |
| `tests/test_result_calculator.py` | **+1 Test** `test_compute_results_places_per_class` (jede Klasse hat einen Ersten; zwei Boote derselben Klasse → 1./2.) |
| `tests/test_race_engine.py` | `test_get_placements_ranks_correctly` angepasst: C (DAMEN) ist jetzt Platz 1 seiner Klasse statt global Platz 3 |

**Verifikation:** 197/197 Tests grün (9.99s).

---

## 2026-09-04 – Build_Dist.cmd: .exe-Build per Doppelklick

### Änderung
Neue `Build_Dist.cmd` im Projekt-Root, die den PyInstaller-Build
(`scripts/build_exe.py`) per Doppelklick ausführt. Sie:
- prüft die `.venv` (mit Einrichtungs-Hinweis)
- bereinigt vor dem Build den alten `build\`-Ordner und die `.spec`-Datei
  (verhindert "Zugriff verweigert"-Fehler)
- ruft `scripts/build_exe.py` auf und zeigt das Ergebnis (`dist\Wasserski-Zeitnehmung.exe`)

Zusätzlich: `SyntaxWarning` in `scripts/build_exe.py` (Docstring `\W`) behoben
(`dist\` → `dist/`).

### Änderungen

| Datei | Änderung |
|---|---|
| `Build_Dist.cmd` | **Neu** – Build der .exe per Doppelklick (UTF-8, .venv-Prüfung, build/-Bereinigung) |
| `scripts/build_exe.py` | Docstring `\W`-Escape behoben (SyntaxWarning) |

**Verifikation:** `Build_Dist.cmd` erfolgreich getestet → `dist\Wasserski-Zeitnehmung.exe` (13.6 MB).

---

## 2026-09-03 – Export-Button immer aktiv + Start-Button bei beendetem Rennen deaktiviert (Kunden-Feedback)

### Hintergrund
Kunden-Feedback (2026-09-03) nach der Ergebnis-Persistenz:
1. **Start-Button wird beim Zurückwechseln zu einem beendeten Rennen angezeigt**
   – obwohl das Rennen schon fertig ist. Der Start soll dort nicht möglich sein.
2. **Keine Export-Möglichkeit beim beendeten Rennen** – obwohl die Daten da sind.

### Lösung
- **Export-Button immer aktiv:** Der Export enthält ALLE fertigen Rennen auf
  einmal – er ist damit unabhängig vom aktuellen Rennen. Ist noch nichts
  beendet, wird eine Datei mit nur den Stammdaten (Event) und leerer
  `races`-Liste erzeugt (keine Fehlermeldung mehr).
- **Start-Button bei beendetem Rennen deaktiviert:** Beim Laden eines bereits
  beendeten Rennens (liegt in `finished_races`) wird der START-Button grau und
  inaktiv gesetzt.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | `_tick()`: Export-Button immer aktiv (`set_export_enabled(True)`); `on_export_results()`: erzeugt auch ohne beendetes Rennen eine Datei (nur Stammdaten, Log-Meldung "nur Stammdaten"); `_load_race()`: `set_start_enabled(False)` wenn Rennen in `finished_races` liegt (Start gesperrt), sonst `True` |
| `python/gui/panels.py` | **CountdownPanel:** neue `set_start_enabled(enabled)` (START-Button grau/inaktiv bei beendetem Rennen) |
| `python/config/app_config.py` | Neue Konstante `COLOR_DISABLED` (Grau für deaktivierte Buttons) |
| `python/excel/json_result_writer.py` | `write_all_races()`: neuer optionaler Parameter `event` – wird verwendet, wenn `exports` leer ist (nur Stammdaten-Export) |
| `tests/test_gui_smoke.py` | **+3 Tests:** `test_export_button_always_enabled` (Button aktiv ohne beendetes Rennen), `test_export_without_finished_race_writes_stammdaten` (Datei mit nur Stammdaten), `test_start_button_disabled_for_finished_race` (START deaktiviert bei beendetem Rennen, aktiv bei nicht beendetem); `fake_write`-Mock akzeptiert `event`-Keyword |

**Verifikation:** 196/196 Tests grün (12.62s).

---

## 2026-09-03 – Ergebnis-Persistenz beim Rennwechsel + Export aller fertigen Rennen (Kundenanforderung)

### Hintergrund
Kundenanforderung (2026-09-03): Die Ergebnisse eines **beendeten** Rennens
sollen beim Rennwechsel **in-memory erhalten** bleiben (Option 1). Beim
Zurückwechseln zu einem bereits beendeten Rennen sind die Ergebnisse
(Runden, Platzierung, Klassen-Status, Renn-Log) wieder da.

Zusätzlich: Der Export enthält **ALLE fertigen Rennen** in EINER Datei,
gruppiert nach Rennen und Klasse (Kundenwunsch: "Rennen 1 Klasse Herren:
erster, zweiter, … / Rennen 2 Klasse Junioren: …").

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/race_engine.py` | **Option 1:** neues Feld `finished_races: dict[int, dict]`; neue `_store_finished_race()` (speichert config, results, events, classes, boats bei FINISHED); `finish_class()` ruft `_store_finished_race()` wenn `all_closed()`; neue `_restore_finished_race()` (spielt laps/finished_at/place/events/Klassen-Status in neue BoatStates bei `load_race` zurück) |
| `python/excel/json_result_writer.py` | **Neu:** `write_all_races(path, exports)` – gruppiert Ergebnisse nach Klasse, `races[]`-Struktur, sortiert nach race_number |
| `python/gui/main_window.py` | `on_export_results()` exportiert jetzt alle fertigen Rennen aus `engine.finished_races` + aktuelles Rennen wenn FINISHED; Dateiname `Ergebnis_AlleRennen_<zeitstempel>.json`; nutzt `write_all_races`; Log-Meldung mit Rennnummern-Liste |
| `tests/test_race_engine.py` | **+2 Tests:** `test_finished_race_results_persist_across_race_switch` (Ergebnisse/Runden/Klassen-Status beim Zurückwechseln wiederhergestellt), `test_export_collects_all_finished_races` (finished_races enthält alle beendeten Rennen) |
| `tests/test_gui_smoke.py` | Export-Tests auf `_start_race` + `finish_class` umgestellt (erwarten `Ergebnis_AlleRennen_*.json`); **+1 Test** `test_write_all_races_groups_by_race_and_class` (Sortierung nach Rennnummer + Klassen-Gruppierung) |

**Verifikation:** 193/193 Tests grün (7.64s).

---

## 2026-09-03 – Hotkey-Zeile entfernt + Leerzeile eliminiert + Hotkeys beendeter Klassen inaktiv (3 Kundenanforderungen)

### Hintergrund
Drei Kundenanforderungen (2026-09-03):
1. **"Aktiv: ..."-Hotkey-Zeile entfernen:** Die zweite Zeile unter der
   Überschrift "Tastaturbedienung (Hotkeys)" (die Liste der aktiven Boot-Keys)
   entfällt, um Platz zu sparen. Der Admin-Status (aktiv/inaktiv) in der
   Überschrift bleibt unverändert.
2. **Leerzeile unter "Rennende-Status" eliminieren:** Das Info-Label
   ("Keine Klassen geladen") wird nur noch gepackt, wenn wirklich keine
   Klassen vorhanden sind – sonst entsteht eine unnötige Leerzeile.
3. **Hotkeys einer beendeten Klasse inaktiv machen:** Sobald eine Klasse
   beendet (CLOSED/FERTIG) ist, werden die Hotkeys ihrer Boote grau/inaktiv –
   auch wenn sie gestartet waren.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/gui/panels.py` | **HotkeyPanel:** `_info`-Label + Pack entfernt (Anforderung 1); neues Feld `_finished_keys`; neue `set_finished_keys()` (Anforderung 3); `_refresh_buttons()` berücksichtigt `_finished_keys` (beendete Keys immer grau/disabled, auch wenn gestartet); `set_starters()` setzt `_finished_keys` zurück. **RaceEndStatusPanel:** `update_classes()` packt `_info` nur noch bei leerer Klassenliste (Anforderung 2) |
| `python/gui/main_window.py` | `_tick()`: ermittelt die Boot-Keys der CLOSED-Klassen aus `get_class_finish_status()` + `starter.klasse` und ruft `hotkeys.set_finished_keys()` auf (Anforderung 3) |
| `tests/test_gui_smoke.py` | `test_hotkey_status_and_started_keys` erweitert (set_finished_keys: beendeter gestarteter Key → disabled/grau, nicht beendeter → aktiv/grün); **+1 Test** `test_race_end_status_no_empty_line_when_classes_loaded` (Info-Label nur ohne Klassen gepackt); `app`-Fixture + 3 Export-Tests rufen jetzt `stop_tick()` auf (verhindert Datei-Lock auf `race_state.json` durch weiterlaufenden after()-Tick) |
| `tests/conftest.py` | `_clean_race_state`-Fixture: Löschen von `race_state.json` mit Retry (5 Versuche, 50 ms) – ein weiterlaufender after()-Tick kann die Datei kurz offen halten (PermissionError) |

**Verifikation:** 190/190 Tests grün (6× stabil, ~8s).

---

## 2026-09-03 – Runner-Spalte fix + Beenden-Button erst nach Rennende + Geschw.-Spalte (3 Kundenanforderungen)

### Hintergrund
Drei Kundenanforderungen (2026-09-03):
1. **Runner-Spalte mit fixer Breite:** Zu lange Namen werden abgeschnitten
   (mit "…"), die Spalte dehnt sich nicht.
2. **"Beenden"-Button erst aktiv wenn Rennzeit abgelaufen:** Vorher sichtbar
   aber inaktiv (grau). Erst in Phase FINISHING/FINISHED aktiv (gelb), wieder
   inaktiv sobald die Klasse CLOSED ist.
3. **Neue Spalte "Geschw." in der Live-Tabelle:** Zwei Werte getrennt durch
   "/": a) km/h letzte Runde (Strecke letzter Runde / Rundenzeit; 1. Runde
   nutzt `lap1_length_m`), b) km/h gesamt (Gesamtstrecke / Zeit bis zum
   letzten Passieren der Startlinie). Fehlender Wert → "–".

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/models.py` | **BoatState:** neue Methoden `speed_last_lap(lap1_length_m, standard_lap_length_m)` (km/h letzte Runde; 1. Runde nutzt `lap1_length_m`) und `speed_total(...)` (km/h gesamt; Distanz = 1. Runde + (Runden-1)×Standardrunde, Zeit = individueller Start bis letzte Passage) |
| `python/gui/panels.py` | **LiveTablePanel:** `COLUMNS` auf 10 Spalten erweitert (neue "Geschw." 110px zwischen "Letzte Runde" und "Gesamtzeit"); `RUNNER_MAX_CHARS = 18`; Runner-Spalte fix via `grid_columnconfigure(1, weight=0)`; neue `set_lap_lengths()`; neue `_truncate_runner()` (Kürzung mit "…"); neue `_format_speed()` ("a/b" oder "–/–"); **RaceEndStatusPanel:** neues Feld `_race_over`; neue `set_race_over()`; neue `_apply_finish_button_state()` (aktiv nur wenn `_race_over` + Klasse nicht CLOSED); neue `_is_closed()`; `_refresh`/`update_states` nutzen die zentrale Button-Logik |
| `python/gui/main_window.py` | `_load_race()`: `live_table.set_lap_lengths(config.lap1_length_m, config.standard_lap_length_m)`; `_tick()`: `race_over = engine.phase in (FINISHING, FINISHED)` → `race_end_status.set_race_over(race_over)` |
| `tests/conftest.py` | `_clean_race_state`-Fixture von session- auf **function-scope** umgestellt (löscht `race_state.json` vor und nach jedem Test) – behebt Test-Isolation: ein früherer Test erzeugte `race_state.json`, das der nächste Test über Crash-Recovery statt der Demo-Daten lud |
| `tests/test_gui_smoke.py` | `app`-Fixture löscht `race_state.json` vor dem Controller-Aufbau; **+5 Tests:** `test_live_table_format_speed`, `test_live_table_truncates_runner_name`, `test_finish_button_disabled_before_race_over`, `test_finish_button_enabled_after_race_over`, `test_finish_button_disabled_again_when_class_closed` |
| `tests/test_models_demo.py` | **+5 Tests:** `speed_last_lap` (1. Runde nutzt lap1, Folge-Runde nutzt Standard, ohne Runden → None), `speed_total` (mit Startzeit+letzter Passage, ohne Runden → None) |

**Verifikation:** 189/189 Tests grün (7.73s).

---

## 2026-09-03 – Manuelle Ziellogik + Hotkey-Status + Startreihen-Countdown (4 Kundenanforderungen)

### Hintergrund
Vier Kundenanforderungen (2026-09-03):
1. **Manuelle Ziellogik:** Nach Ablauf der Renndauer passiert NICHTS automatisch.
   Jede Klasse bekommt im Rennende-Status einen "Beenden"-Button. Beim Drücken
   werden alle Boote der Klasse fertig (Ergebnis fest: meiste Runden in
   kürzester Zeit). Die ganze "Letzte Runde"-Logik (finish_mode, TRIGGERED)
   wurde entfernt. Status nur noch: Warten → Gestartet → Fertig.
2. **Hotkeys nur bei gestarteten Startern aktiv:** Grün/aktiv nur wenn die
   Startreihe des Boots gestartet ist, sonst grau und inaktiv.
3. **Startreihen-Countdown ANSTATT Vorstart-Countdown:** Die VORSTART-Kachel
   zeigt den Startreihen-Countdown ("START REIHE N:"), wenn das Rennen läuft
   und eine nächste Reihe startet. Keine separate Kachel mehr.
4. **Admin-Rechte-Status:** Bei der Überschrift "Tastaturbedienung (Hotkeys)"
   informativ anzeigen, ob die systemweiten Hotkeys aktiv (grün) oder inaktiv
   (grau) sind.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/models.py` | `BoatState.finish_mode` entfernt; `RaceClass.finish_state` nur noch WAITING/CLOSED; `RacePhase`-Docstrings (FINISHING/FINISHED = manuell beendet); `FINISH`-EventType-Docstring manuell |
| `python/core/class_finish_tracker.py` | **Komplett neu geschrieben:** nur WAITING/CLOSED; neue `finish_class(klasse, now)` markiert alle Boote der Klasse fertig; `on_passage`/`close_class`/TRIGGERED entfernt |
| `python/core/race_engine.py` | `_process_finishing()` entfernt; neue `finish_class()` (beendet Klasse manuell, FINISH-Events, → FINISHED wenn alle CLOSED); `handle_key_press()`: fertige Boote → INVALID; `tick()`-FINISHING: pass; Serialisierung ohne `finish_mode` |
| `python/gui/panels.py` | **RaceEndStatusPanel:** "Beenden"-Button je Klasse + `set_on_finish_class()`; **HotkeyPanel:** `set_started_keys()` (grün nur gestartet), `set_hotkey_status()` (Admin-Status neben Überschrift), Titel "Tastaturbedienung (Hotkeys)"; **CountdownPanel:** Startreihen-Countdown in VORSTART-Kachel (`set_start_line`), separate Kachel entfernt; **LiveTablePanel:** Status ohne "LETZTE RUNDE" |
| `python/gui/main_window.py` | `_tick()`: Startreihen-Countdown in VORSTART-Kachel; `set_started_keys()`; neue `on_finish_class()`; `set_on_finish_class()` verdrahtet; `AppController`/`run_app` + `is_admin`-Parameter; Hotkey-Status-Anzeige |
| `python/main.py` | `is_admin` an `run_app` übergeben (Admin-Status-Anzeige) |
| `scripts/preview_gui.py` | `is_admin` an `AppController` übergeben |
| `tests/test_class_finish_tracker.py` | **Komplett neu geschrieben** (neue `finish_class`/`all_closed`/`status` API) |
| `tests/test_race_engine.py` | Rennende-Tests auf manuelle Ziellogik umgestellt (+ `finish_class`-Tests, fertige Boote → INVALID) |
| `tests/test_gui_smoke.py` | FINISHED-Erreichen über `finish_class` statt Passagen; **+1 Test** `test_hotkey_status_and_started_keys` |

**Verifikation:** 179/179 Tests grün (8.58s), GUI-Smoke 23/23 grün.

---

## 2026-09-03 – Startreihen-Funktionalität (Variante A: zeitversetzte Starts)

### Hintergrund
Kundenentscheidung (2026-09-02): **Variante A** – jedes Boot startet seine
Zeitmessung erst, wenn seine Startreihe startet. Reihe 1 bei T=0, Reihe 2 bei
+Grid Time, Reihe 3 bei +2×Grid Time. Gesamtzeit/Platzierung ab individuellem
Start. Grid Time (`config.grid_time_s`) kommt ausschließlich aus Excel/IMPORT.json
(Pflichtfeld, keine hartcodierten Fallbacks).

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/models.py` | `BoatState.start_time: datetime \| None` (individueller Startzeitpunkt, Variante A); `EventType.STARTLINE = "STARTLINE"` |
| `python/core/race_engine.py` | `start_race()`: setzt je Boot `start_time = now + (startreihe-1) × grid_time_s`; `handle_key_press()`: Passage vor individuellem Start → INVALID; neue Methoden `start_line_remaining()`/`next_start_line()` (Countdown-Anzeige); `_check_start_lines()` protokolliert STARTLINE-Events; `_started_lines`-Feld; Serialisierung + Crash-Recovery von `start_time`/`started_lines` |
| `python/core/result_calculator.py` | `add_lap()`: erste Runde ab `state.start_time or race_start` (Fallback globaler Rennstart) |
| `python/gui/panels.py` | **LiveTablePanel:** neue Spalte "Reihe" (9 Spalten); Status zeigt "WARTET" (vor Start) / "GESTARTET"; **CountdownPanel:** neue Startreihen-Kachel "START REIHE N" mit Countdown + Fortschrittsbalken; Buttons auf row 4/5 verschoben |
| `python/gui/main_window.py` | `_tick()`: Startreihen-Kachel steuern (`show_start_line`/`set_start_line`/`hide_start_line`); `_show_event()`: STARTLINE im Log-Feed; neue `_startline_text()`-Hilfsmethode |
| `tests/test_race_engine.py` | **+6 Tests:** individuelle Startzeiten, Passage vor Start → INVALID, Passage nach Start gültig, STARTLINE-Events, `start_line_remaining`/`next_start_line`, Crash-Recovery von `start_time`/`started_lines` |
| `tests/test_gui_smoke.py` | `test_blackbox_records_engine_events` angepasst (zusätzliches STARTLINE-Event) |

**Verifikation:** 176/176 Tests grün (7.49s).

---

## 2026-09-02 – Bugfix: Starter ohne RundenTaste wurden still verworfen (Kunden-IMPORT.json)

### Bug (User-Report)
Die Kunden-IMPORT.json (5 Rennen, echte Starter) zeigte **keine Starter** an,
obwohl sie fast identisch zur funktionierenden IMPORT1.json aussah.

### Ursache
In der Kunden-IMPORT.json ist bei **allen** Startern `"RundenTaste": null`
(die Excel-Spalte wurde nicht befüllt). `JsonRaceStore._parse_starter_item()`
verwarf jeden Starter ohne RundenTaste **still** (`return None`) → 0 Starter.

### Fix (Feature: automatische Key-Vergabe)
Starter ohne RundenTaste werden **nicht mehr verworfen**, sondern bleiben
sichtbar und bekommen **automatisch** den nächsten freien Boot-Key (A, B, C…
pro Rennen) zugewiesen. Das ist das gewünschte Feature (Entscheidung
2026-09-02): Ob ein oder alle Starter keinen Hotkey haben – die Logik ist
dieselbe, jeder Starter bekommt einen Key. Die Validierung meldet "Boot ohne
Key" daher **nicht mehr als Fehler** (die automatische Vergabe löst es).
Komplett leere Platzhalter-Einträge (ohne Bootnummer UND Fahrer) werden
weiterhin verworfen.

**Wichtig – Excel-Hotkeys haben VORRANG:** Die automatische Vergabe
berücksichtigt ALLE Excel-Keys des Rennens (auch die, die erst später in der
Liste stehen). Ein automatisch vergebener Key überschreibt nie einen
Excel-Key. Dazu werden die Excel-Keys in einem ersten Durchgang gesammelt
und der automatischen Vergabe als `reserved` übergeben.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/excel/json_race_store.py` | `_parse_starter_item()`: fehlende RundenTaste → leerer Key statt `return None`; `_parse_starters()`: Zwei-Pass-Logik – erst Excel-Keys pro Rennen sammeln, dann fehlende Keys automatisch vergeben (Excel-Keys haben Vorrang) + Log-Hinweis; leere Einträge (ohne BoatNr UND Skier) verworfen |
| `python/core/starter_utils.py` | `next_free_key_for(race_number, reserved=None)` – berücksichtigt zusätzlich reservierte Excel-Keys, damit kein Excel-Key überschrieben wird |
| `python/core/data_validator.py` | "Boot ohne Key" ist **kein Fehler** mehr (automatische Vergabe löst es); Docstring aktualisiert |
| `tests/test_data_validator.py` | `test_starter_without_boot_key_fails` → `test_starter_without_boot_key_ok`; `test_multiple_errors_collected` angepasst |
| `tests/test_json_race_store.py` | `test_empty_starter_filtered` angepasst (leerer Eintrag ohne BoatNr/Skier wird verworfen); **neu** `test_excel_key_has_priority_over_auto` (Regression: Excel-Key wird nie überschrieben) |

**Verifikation:** 170/170 Tests grün (6.78s). Kunden-IMPORT.json: 5 Rennen, 25 Starter, 0 Validierungsfehler (vorher 0 Starter). .exe neu gebaut (13.6 MB).

---

## 2026-09-02 – Bugfix: Rennwechsel nach beendetem Rennen (Vorstartzeit 0, Start-Button tot)

### Bug (User-Report)
Nach einem beendeten Rennen (Zieleinlauf, Phase FINISHED) blieb beim Wechsel
zu Rennen 2 die Vorstartzeit auf **0** und der PLAY-Button tat **nichts**.

### Ursache
`RaceEngine.load_race()` setzte die Phase **nicht** auf `RESET` zurück. Die
Engine startete zwar mit `phase = RESET` (deshalb funktionierte Rennen 1),
aber nach Rennen 1 blieb die Phase `FINISHED` stehen:
- Tick zeigte `race_remaining()` (race_end = None → 0) statt des neuen Startintervalls
- `on_start_race()` prüft `phase != RESET` → `return` → Start wirkungslos

### Fix
`load_race()` setzt jetzt Phase + Zeitstempel zurück (RESET, race_start/race_end/
countdown_end = None, countdown_paused = False) – ein frisch geladenes Rennen
steht immer auf RESET, bereit für den PLAY-Button.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/race_engine.py` | `load_race()`: Phase auf `RESET` + Zeitstempel zurücksetzen (Bugfix-Kommentar) |
| `tests/test_race_engine.py` | **+1 Test** `test_load_race_after_finished_race_resets_phase`: Rennen 1 bis FINISHED → Rennen 2 laden → RESET + neues Startintervall (7 s) + Countdown startet |
| `tests/test_gui_smoke.py` | **+1 Test** `test_race_switch_after_finished_race_resets_countdown`: kompletter User-Flow (Rennen 1 durchspielen → Wechsel zu Rennen 2 → RESET → PLAY funktioniert) |

**Verifikation:** 169/169 Tests grün (6.22s).

---

## 2026-09-02 – Rennparameter: Startintervall + Grid Time als Pflichtfelder (keine Hardcodierungen)

### Hintergrund
Kundenentscheidung (2026-09-02): **Keine hartcodierten Fallbacks** für Rennparameter.
- **Startintervall** = Vorlaufzeit bis zum wirklichen Start (Countdown) – kommt aus der Excel/IMPORT.json, ist **Pflichtfeld**, kann pro Rennen unterschiedlich sein.
- **Grid Time** = Zeit zwischen den Startreihen – kommt aus der Excel, ist **Pflichtfeld**.
- Beide Werte in **Sekunden** (keine Mischeinheiten).
- Der feste `startreihe_offset_s` aus der App-Config kann **weg** (wird durch Grid Time ersetzt).

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/models.py` | `prestart_seconds` **entfernt**; `start_interval_s` = Startintervall (Vorlaufzeit, Pflicht); `grid_time_s` = Grid Time (Zeit zwischen Startreihen, Pflicht); Begriffsklärung aktualisiert |
| `python/excel/json_race_store.py` | Prestart-Fallback `or 60` **entfernt**; `start_interval_s`/`grid_time_s` ohne hartcodierten Default (fehlt der Wert → 0 → Validierungsfehler) |
| `python/core/race_engine.py` | `load_race()`: Parameter `startreihe_offset_seconds=15` **entfernt** → Startreihen-Offsets aus `config.grid_time_s`; Countdown nutzt `config.start_interval_s` statt `prestart_seconds`; TODO Startlinien-Offsets erledigt |
| `python/config/app_config.py` | `AppSettings.startreihe_offset_s` **entfernt** (Hinweis-Kommentar ergänzt) |
| `python/config/app_settings.json` | `startreihe_offset_s` **entfernt** |
| `python/gui/main_window.py` | `startreihe_offset_seconds=`-Argument entfernt; `prestart_seconds` → `start_interval_s` (Countdown-Anzeige) |
| `python/core/data_validator.py` | Neue Pflichtfeld-Prüfungen: `start_interval_s > 0` („Startintervall (Vorlaufzeit)…") und `grid_time_s > 0` („Grid Time (Zeit zwischen Startreihen)…") |
| `tests/demo_data.py` | `prestart_seconds` entfernt; `start_interval_s` = Vorlaufzeit (15/20/15 s) |
| `tests/test_data_validator.py` | `test_zero_prestart_fails` → `test_zero_start_interval_fails` + neuer `test_zero_grid_time_fails` |
| `tests/test_race_engine.py` | `prestart_seconds=20` → `start_interval_s=20` + `grid_time_s=15` |
| `architecture_and_roadmap/09_parameterliste.md` | **Neu** – vollständige Parameterliste (Pflicht/Optional/Nicht nötig) + Befüllungs-Kette |
| `Manual.md` | Abschnitt 3a „Rennparameter (Pflichtfelder)"; `_EXP_RACES`-Inhalt; Offene Punkte aktualisiert |

**Verifikation:** 167/167 Tests grün (6.54s).

---

## 2026-09-02 – Demo-Daten vollständig entfernt (App lädt NUR echte Daten)

### Hintergrund
Die Demo-Daten waren entgegen der Absprache (2026-08-25) noch im Code:
`python/core/demo_data.py` existierte, `AppController` hatte einen Demo-Fallback
in der Lade-Kette (Schritt 4), und die GUI zeigte "Datenquelle: Demo-Daten".
Jetzt: **Keine Demo-Daten in der App** – ohne Datenquelle erscheint die
Fehlermeldung "Keine Renndaten gefunden".

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/race_data.py` | **Neu** – neutraler Container `RaceData` (event, race_configs, starters, selected_config); ersetzt `DemoScenario` |
| `python/core/demo_data.py` | **Entfernt** – nach `tests/demo_data.py` verschoben (Test-Fixture) |
| `tests/demo_data.py` | **Neu** – Test-Fixture mit fiktiven Daten (build_event, build_starters, build_race_configs, build_boat_states_for_race2, build_demo_events, create_demo_scenario → RaceData) |
| `python/core/data_validator.py` | `DemoScenario` → `RaceData` (Import + Docstrings) |
| `python/gui/main_window.py` | `DemoScenario`/`create_demo_scenario`-Import entfernt; `scenario=`-Parameter → `data=`; Lade-Kette Schritt 4 (Demo-Fallback) entfernt → nur noch Testdaten-Parameter; `_source_type` "demo" → "test"; Footer-Default "Datenquelle: –"; `_load_from_json/_load_from_excel` → `RaceData` |
| `python/main.py` | Docstring: Demo-Daten-Hinweis entfernt |
| `scripts/preview_gui.py` | Docstring + argparse-Description: Demo-Hinweis entfernt |
| `scripts/build_exe.py` | Docstring: "Demo-Modus" → "ohne systemweite Hotkeys" |
| `python/core/race_engine.py` | Docstring: Demo-Daten-Hinweis entfernt |
| `Start_Zeitnehmung.cmd` | "(Demo-Daten)" aus Echo entfernt |
| `Start_Zeitnehmung_Admin.cmd` | "(Demo-Daten)" aus Echo entfernt |
| `tests/test_data_validator.py` | Import: `python.core.demo_data` → `tests.demo_data` |
| `tests/test_gui_smoke.py` | Import + `scenario=` → `data=` (5 Stellen) |
| `tests/test_hotkey_activation.py` | Import + `scenario=` → `data=` (3 Stellen) |
| `tests/test_models_demo.py` | Import auf `tests.demo_data`; `scenario.boat_states`/`scenario.events` → direkte Builder-Aufrufe |
| `Manual.md` | Startlogik: "Demo-Daten" → "Testdaten"; Offene Punkte: Demo-Entfernung abgehakt |

**Verifikation:** 166/166 Tests grün (6.67s).

---

## 2026-09-01 – JSON-first: Ergebnis-Export als JSON (JsonResultWriter)

### Hintergrund
Das System soll komplett JSON-first sein: Lesen via VBA → IMPORT.json, Schreiben via JsonResultWriter → JSON → VBA. Kein direkter Excel-Zugriff mehr (weder lesen noch schreiben).

### Änderungen

| Datei | Änderung |
|---|---|
| `python/excel/json_result_writer.py` | **Neu** – `JsonResultWriter` schreibt Ergebnisse + Renn-Log als JSON; `RaceResultExport` (frozen dataclass) mit `log_entries`; `JsonWriteError` Exception |
| `python/gui/main_window.py` | **AppController:** `on_export_results()` nutzt jetzt `JsonResultWriter` statt `ExcelResultWriter`; Export-Datei `.json` statt `.xlsx`; `log_entries` aus Engine-Events |
| `python/excel/excel_result_writer.py` | **Entfernt** – Excel-Schreiber nicht mehr nötig |
| `tests/test_excel_result_writer.py` | **Entfernt** – Tests für nicht mehr vorhandenen Code |
| `tests/test_gui_smoke.py` | Export-Tests auf JSON umgestellt (`.json` Prüfung, `JsonWriteError` Mock) |
| `python/core/time_format.py` | Docstring aktualisiert (JSON-Export statt Excel-Export) |
| `requirements.txt` | `openpyxl` entfernt (nicht mehr nötig) |
| `Manual.md` | Datenfluss, Dateikonvention, Offene Punkte aktualisiert |

**Verifikation:** 166/166 Tests grün (5.56s).

---

## 2026-09-01 – VBA-Makro-Aufruf via COM (ADR-009)

### Hintergrund
ADR-009: JSON statt direktem Excel-Zugriff als primärer Datenpfad. Der direkte Excel-Leser (`ExcelRaceReaderV2` via openpyxl) ist im Rennbetrieb gefährlich (Locks). Das VBA-Makro `mdlEngl.ExportExpRangesToJSON` erzeugt `IMPORT.json` aus den `_EXP_`-Ranges. Python soll das Makro via COM automatisch aufrufen.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/excel/vba_macro_caller.py` | **Neu** – `VbaMacroCaller` Klasse: öffnet Excel via `win32com.client`, ruft `mdlEngl.ExportExpRangesToJSON` auf, warten auf IMPORT.json, Excel schließen; `VbaMacroError` Exception; `check_macro_available()` Prüfmethode |
| `python/gui/main_window.py` | **AppController:** `_load_from_excel()` ruft jetzt `VbaMacroCaller` auf → IMPORT.json → `JsonRaceStore`; Error-Handling für `VbaMacroError`; Docstring aktualisiert (ADR-009 Lade-Kette) |
| `python/excel/excel_reader_v2.py` | **Entfernt** – direkter Excel-Leser via openpyxl nicht mehr nötig |
| `python/excel/excel_reader.py` | **Entfernt** – V1 Legacy-Reader nicht mehr nötig |
| `tests/test_excel_reader_v2.py` | **Entfernt** – Tests für nicht mehr vorhandenen Code |
| `tests/test_excel_reader.py` | **Entfernt** – Tests für nicht mehr vorhandenen Code |
| `scripts/debug_races.py` | **Entfernt** – Debug-Script nutzte entfernten ExcelRaceReaderV2 |
| `requirements.txt` | `pywin32==312` ergänzt (COM-Automation) |
| `Manual.md` | Datenfluss aktualisiert: Python ruft VBA-Makro via COM auf; Startlogik aktualisiert; Offene Punkte: ExportExpRangesToJSON + JsonRaceStore abgehakt |

**Verifikation:** 174/174 Tests grün (5.60s).

---

## 2026-08-25 – UI-Sicherheitsfixes: Neustart-Bestätigung, Crash-Recovery, Rennwechsel-Blockade

### 1. Neustart: Bestätigungsdialog
**Vorher:** NEUSTART-Button setzte sofort alles zurück – kein Schutz vor Versehen.
**Jetzt:** `messagebox.askyesno` fragt "Sind Sie sicher, dass Sie das Rennen neu starten möchten? Alle bisherigen Ereignisse und Runden gehen verloren." Erst nach Bestätigung wird zurückgesetzt.

### 2. Crash-Recovery: race_state.json sofort laden, NICHT nachfragen
**Vorher:** Bei Absturz + Neustart fragte die App zuerst, ob IMPORT.json verwendet werden soll – obwohl `race_state.json` vorhanden war.
**Jetzt:** Wenn `race_state.json` existiert, wird es sofort geladen (IMPORT.json wird OHNE Bestätigungsdialog gesucht). Kein Dialog, kein Zögern.

### 3. Rennwechsel während laufendem Rennen blockieren
**Vorher:** Das Rennen-Auswahl-Dropdown war jederzeit bedienbar – auch mitten im laufenden Rennen.
**Jetzt:** Race-Selector ist nur in Phase RESET aktiv (deaktiviert in PRESTART/ACTIVE/FINISHING/FINISHED).

### Änderungen

| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | `on_reset()`: Bestätigungsdialog vor Reset; `_load_data()`: Crash-Recovery-Pfad ohne Nachfrage; `_tick()`: Race-Selector-Deaktivierung |
| `python/gui/panels.py` | `CountdownPanel.set_race_selector_enabled()`: neue Methode für Dropdown-Deaktivierung |
| `tests/conftest.py` | `_mock_messagebox` autouse-Fixture (unittest.mock.patch statt monkeypatch für session-kompatibles Mocking) |

**Verifikation:** 210/210 Tests grün (62.99s).

---

## 2026-08-25 – ExcelReaderV2: _EXP_ Prefix für Named Ranges (ADR-009)

### Hintergrund
Die Excel-Datei nutzt jetzt `_EXP_`-Prefix für Named Ranges (`_EXP_INFO`, `_EXP_RACES`, `_EXP_STARTER`) statt der ursprünglichen Namen (`INFO`, `RACES`, `STARTER`). Der ExcelReaderV2 fand die Ranges nicht mehr → alle 7 Reader-Tests schlugen fehl.

**Fix:** `_resolve_range_name()` prüft beide Namen (base i `_EXP_`), fallback auf `_EXP_`-Variante. `__init__` der Klasse enthält beide Konstanten. Backwards-compatible: alte Excel-Dateien ohne Prefix funktionieren weiterhin.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/excel/excel_reader_v2.py` | **Neu:** `_resolve_range_name(base, exp)` mit Fallback-Logik; `RANGE_INFO_EXP`, `RANGE_RACES_EXP`, `RANGE_STARTER_EXP` Konstanten; `_read_info/races/starters()` nutzen `_resolve_range_name()` statt direktem `RANGE_*` |
| `tests/test_excel_reader_v2.py` | Pfad angepasst: `Excel/` → Root |

**Verifikation:** 210/210 Tests grün (5.68s) – inklusive aller Excel-Reader-Tests.

---

## 2026-08-25 – Bugfix: RaceEndStatusPanel akkumuliert Klassen bei Rennen-Wechsel

### Bug 1: Rennende-Status zeigt immer mehr Klassen
**Symptom:** Beim Wechsel zwischen Rennen sammelten sich Klassen im Rennende-Status-Panel. Alte Klassen vom vorherigen Rennen blieben sichtbar.

**Ursache:** `RaceEndStatusPanel.update_classes()` zerstörte nur die Value-Labels (`self._rows`), aber **nicht die übergeordneten Row-Frames** (`ctk.CTkFrame`). Die Frames blieben im Panel gepackt – neue Klassen kamen dazu, alte blieben.

**Fix:** Neue `_row_frames: list[ctk.CTkFrame]` speichert alle Zeilen-Frames. `update_classes()` zerstört zuerst ALLE alten Frames (inkl. Kinder-Labels), dann baut komplett neu auf.

### Bug 2: Anzeige zeigt Boot nicht nach Rennen-Wechsel
**Symptom:** Kollisions-Warnung beim Start war korrekt (Boot war im Rennen), aber das Boot wurde in der GUI nicht angezeigt.

**Ursache:** Dasselbe Problem wie Bug 1 – verwaiste Klassen-Frames vom vorherigen Rennen überdeckten die korrekte Anzeige des aktuellen Rennens.

## 2026-08-25 – Bugfix: Doppelte Boot-Keys – StarterList mit automatischer Key-Prüfung

### Bug: Starter mit gleichem Hotkey verschwinden
**Symptom:** Bei 9 Startern in der IMPORT.json wurden nur 8 in der App angezeigt. Zwei Starter hatten denselben Boot-Key (z.B. beide "A") – das Dict-Comprehension in `RaceEngine.load_race()` überschrieb den ersten mit dem zweiten.

**Fix:** Zentrale `StarterList`-Klasse in `python/core/starter_utils.py` mit `add()`-Methode:
- Beim Hinzufügen wird automatisch geprüft ob der Key im selben Rennen schon belegt ist
- Bei Doppelung → nächster freier Buchstabe (A–Z) + Log-Warnung
- Gleicher Key in verschiedenen Rennen ist erlaubt

Beide Reader (JsonRaceStore + ExcelReaderV2) nutzen `StarterList` statt `list.append()`.

### Änderungen

| Datei | Änderung |
|---|---|
| `python/core/starter_utils.py` | **Neu:** `StarterList` Klasse mit `add()`, `as_list()`, Key-Eindeutigkeit pro Rennen |
| `python/excel/json_race_store.py` | `_parse_starters()` nutzt `StarterList.add()` statt `list.append()`; `_resolve_duplicate_keys()` + `_next_free_key()` entfernt |
| `python/excel/excel_reader_v2.py` | `_read_starters()` nutzt `StarterList.add()` statt `list.append()` |
| `python/gui/panels.py` | **RaceEndStatusPanel:** `_row_frames` + `update_classes()` zerstört alle Frames |
| `tests/test_json_race_store.py` | **+4 Tests:** doppelte Keys im selben Rennen, gleicher Key in verschiedenen Rennen, mehrfache Duplikate, keine Duplikate |
| `tests/test_excel_reader_v2.py` | Pfad angepasst: `Excel/` → Root |

**Verifikation:** 174/174 Tests grün (4.55s). ExcelReaderV2-Fix separat dokumentiert.

---

## 2026-08-25 – Responsives Layout + Export-Button in Header

### Hintergrund
GUI-Design für verschiedene Auflösungen überarbeitet (1280–2560px). Neue Prinzipien:
- Links: RaceInfo (kompakt) → EventFeed (7 Zeilen fix) → LiveTable (REST, scroll)
- Rechts: Countdown (fix) → Hotkeys (fix, KOMPAKT) → RaceEnd + Manual (je weight=1)
- Export-Button: von HotkeyPanel → HeaderPanel (neben "Daten aktualisieren")

### Änderungen

| Datei | Änderung |
|---|---|
| `python/gui/panels.py` | **HotkeyPanel:** Export-Bereich (Button + Status-Label + Callbacks) komplett entfernt; `on_export`-Parameter aus `__init__` entfernt; `set_on_export()`, `set_export_status()`, `_press_export()` Methoden entfernt |
| `python/gui/panels.py` | **HeaderPanel:** Export-Button (blau, `set_export_callback()`, `set_export_enabled()`, `set_export_status()`) im `bottom_row` neben Refresh-Button; `_on_export_clicked()` Handler |
| `python/gui/panels.py` | **LogFeedPanel:** `visible_lines`-Parameter (Default=7) für konfigurierbare Höhe; TextBox-Höhe = `visible_lines × 18px + 20px` |
| `python/gui/main_window.py` | **Layout-Neubau:** Äußeres Grid 5:2 (vorher 3:1); Linke Spalte: 3 Zeilen (RaceInfo fix, LogFeed fix 7 Zeilen, LiveTable weight=1); Rechte Spalte: 4 Zeilen (Countdown fix, Hotkeys fix, RaceEnd weight=1, Manual weight=1); LogFeed von Zeile 2 (volle Breite) in linke Spalte Zeile 1 |
| `python/gui/main_window.py` | **AppController:** Export-Callbacks auf Header umgeleitet (`header.set_export_callback`, `header.set_export_status`); `_tick()` aktiviert Export-Button bei Phase FINISHED |
| `tests/test_gui_smoke.py` | 5 Export-Tests angepasst: `window.hotkeys` → `window.header` für Export-Status + Callback |

**Verifikation:** 18/18 GUI-Smoke-Tests grün (3 Fehler vorher: OneDrive-Sperre auf race_state.json, nicht relevant).

## 2026-08-21 – GUI Tuning + Boot-Key-Validierung (pro Rennen)

### Bugfix: Boot-Key-Validierung
**Hintergrund:** `validate_scenario()` prüfte doppelte Boot-Keys global über alle Rennen. In der Praxis haben verschiedene Rennen dieselben Keys (z.B. Boot "A" in Rennen 1 UND Rennen 2). Keys müssen nur INNERHALB eines Rennens eindeutig sein.

| Datei | Änderung |
|---|---|
| `python/core/data_validator.py` | `seen_keys` → `keys_per_race` (dict pro Rennen); Doppelte Keys nur innerhalb desselben Rennens gemeldet |
| `tests/test_data_validator.py` | `test_duplicate_boot_keys_fails`: explizit gleiche race_number; `test_same_key_different_races_ok`: neuer Test |

### GUI Tuning
| Datei | Änderung |
|---|---|
| `python/gui/panels.py` | **RaceInfoPanel:** 2-Spalten-Layout, reine Anzeige; `add_race_selector()` entfernt |
| `python/gui/panels.py` | **CountdownPanel:** `add_race_selector()` unter Überschrift |
| `python/gui/panels.py` | **LogFeedPanel:** `height=120` |
| `python/gui/panels.py` | **HotkeyPanel:** Zahlenblock entfernt |
| `python/gui/main_window.py` | `_left_col`/`_right_col` Frames; LogFeed als eigene Zeile (colspan=2) |

**Verifikation:** **169/169 Tests grün** (12.2s).

---

## 2026-08-21 – Reset-Phase Fix (PLAY-Button sinnvoll) + Tick-Loop Stop + Test-Stabilität

**Hintergrund:** `RaceEngine.reset()` startete den Countdown automatisch (PRESTART), was den PLAY-Button nutzlos machte (on_start_race() prüft phase==RESET). Zudem fehlte ein Stopp-Mechanismus für Tick-Loops in Tests.

### Architektur-Entscheidung
- **NEUSTART → RESET** (nicht mehr automatisch PRESTART)
- **PLAY-Button startet Countdown** explizit (§6: "Durch einen Play-Button ausgelöst")
- Flow: RESET → PLAY → PRESTART → Countdown → ACTIVE

### Änderungen
| Datei | Änderung |
|---|---|
| `python/core/race_engine.py` | `reset()`: ruft `start_countdown()` NICHT mehr auf; setzt `phase=RESET`, `race_start=None`, `race_end=None`, `countdown_end=None`, `countdown_paused=False` |
| `python/gui/main_window.py` | `_tick()`: neue Phase RESET → zeigt Prestart-Vollzeit (Countdown steht still); `AppController`: `_tick_running`/`_tick_after_id` für sauberes Tick-Stop; `stop_tick()` Methode neu; `on_reset()` Docstring aktualisiert |
| `tests/test_gui_smoke.py` | 4 Tests angepasst: `on_start_race()` explizit vor PRESTART-Assertions; `on_reset()` endet in RESET; `on_reset()` in `test_input_queue_drains_to_engine` ergänzt; `stop_tick()` in Export-Tests für 2. Controller; MessageBox-Mock in Validation-Test; `conftest.py` `_clean_race_state` autouse fixture |
| `tests/test_race_engine.py` | `test_reset_clears_state_and_enters_reset_phase`: prüft RESET + `countdown_end is None`; nach `start_countdown()` → PRESTART |

**Verifikation:** **192/192 Tests grün** (11.57s, inkl. Excel-Reader-V2-Skipps).

---

## 2026-08-20 – Begriffsklärung: Startintervall/Grid Time + Umbenennung

**Hintergrund:** Kunde klärt Begriffe:
- **Grid Time** = Zeit zwischen den Startreihen (10/15s)
- **Startintervall** = Vorlaufzeit bis zum wirklichen Start
- **StartTimer** = brauchen wir nicht

### Änderungen
| Datei | Änderung |
|---|---|
| `python/core/models.py` | `start_interval_min` → `start_interval_s` (Sekunden); Comments für Grid Time/Startintervall aktualisiert |
| `python/excel/excel_reader_v2.py` | Mapping + Aufruf aktualisiert |
| `python/excel/json_race_store.py` | Mapping aktualisiert |
| `python/core/demo_data.py` | Demo-Werte angepasst |
| `tests/test_excel_reader_v2.py` | Assertions aktualisiert |

**Verifikation:** **148/148 Tests grün**.

---

## 2026-08-20 – EXPORT.json → IMPORT.json Umbenennung + Reihenfolge-Fix

**Hintergrund:** Kunde klärt Namenskonvention aus Sicht der App:
- **IMPORT.json** = Daten die reinkommen (VBA schreibt, App liest)
- **EXPORT.json** = Daten die rausgehen (App schreibt, VBA/Excel liest)

### Änderungen
| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | Alle `EXPORT.json` → `IMPORT.json`; Reihenfolge korrigiert: Scenario VOR Auto-Suche (Bugfix: Tests wurden durch Auto-Suche überschrieben) |
| `python/excel/json_race_store.py` | Alle `EXPORT.json` → `IMPORT.json` |
| `python/main.py` | Alle `EXPORT.json` → `IMPORT.json` |
| `scripts/preview_gui.py` | Alle `EXPORT.json` → `IMPORT.json` |
| `python/core/race_state_manager.py` | Kommentar korrigiert |
| `tests/test_json_race_store.py` | Alle `EXPORT.json` → `IMPORT.json` |
| `Manual.md` | Dateikonvention + Reihenfolge korrigiert |
| `PROJECT_LOG.md` | Dateikonvention korrigiert |
| `AGENTS.md` | Dateikonvention korrigiert |

**Verifikation:** **148/148 Tests grün**.

---

## 2026-08-20 – Auto-Suche nach Renndaten + Fehlerdialog

**Hintergrund:** Ohne `--excel`/`--json` crasht App still. Kunde will: Dateien im gleichen Ordner wie .exe → automatisch finden.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | `_load_data()`: Auto-Suche in Schritt 4 – sucht IMPORT.json, dann *.xlsm, dann *.xlsx im EXE-Ordner/CWD; `_get_search_dir()`: PyInstaller → .exe-Ordner, Dev → Projekt-Root; Fehlermeldung zeigt Suchordner |
| `python/gui/main_window.py` | `run_app()`: try/except FileNotFoundError → GUI-Fehlerdialog statt Crash |
| `scripts/preview_gui.py` | try/except FileNotFoundError → GUI-Fehlerdialog statt Crash |

**Verifikation:** **148/148 Tests grün**.

---

## 2026-08-20 – AppController: Lade-Kette + Crash-Recovery + JSON-Pfad

**Hintergrund:** AppController muss die vollständige Lade-Kette (Manual.md) implementieren: race_state.json → IMPORT.json → Excel → Fehler. Zudem `--json` CLI-Argument für beide Entry-Points.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | **AppController:** vollständige Lade-Kette in `_load_data()` – Crash-Recovery (race_state.json), JSON (`json_path`), Excel (`excel_path`), Scenario (Fallback für Tests), Fehler wenn nichts gefunden; `_load_from_json()` Methode; `_state_manager.clear()` bei Reset; State wird bei jedem Tick/Event gespeichert; `run_app()` akzeptiert `json_path` |
| `python/main.py` | `--json` CLI-Argument ergänzt; Docstring aktualisiert |
| `scripts/preview_gui.py` | `--json` CLI-Argument ergänzt; Docstring aktualisiert |
| `tests/test_gui_smoke.py` | 5 Tests angepasst: Explizites `scenario=create_demo_scenario()` statt implizitem Fallback (AppController lädt keine Fallback-Daten mehr) |
| `tests/test_hotkey_activation.py` | 3 Tests angepasst: Explizites `scenario=create_demo_scenario()` |
| `Manual.md` | Lade-Kette dokumentiert (race_state.json → JSON → Excel → Fehler) |
| `AGENTS.md` | Manual.md Referenz in Projektstruktur, Kein-Demo-Fallback Regel |
| `PROJECT_LOG.md` | ADR-009 (JSON-Architektur), Dateikonvention, Event-Types |

**Verifikation:** **148/148 Tests grün** (36 Excel-Skipps wenn .xlsm geöffnet).

## 2026-08-20 – Excel Named Ranges + Datenmodell-Refactoring (Startreihen-Hierarchie)

**Hintergrund:** Kunde hat neue Excel-Struktur mit Named Ranges (INFO, RACES, STARTER) und festem Startreihen-Offset (10/15s) geliefert. Rundenlängen sind pro Rennen (nicht global). Klassen nur für Auswertung.

### Datenmodell (models.py)
| Änderung | Details |
|---|---|
| `Event` | `event_title` → `title`; `lap1_length_m`/`standard_lap_length_m` entfernt (gehören pro Rennen) |
| `Starter` | `boot_name` entfernt; neue Felder: `boat_number`, `skier`, `team`, `driver`, `observer`, `club`, `federation`, `race_number`, `startreihe`; `display_name` Property |
| `RaceConfig` | `start_lines`/`class_mapping` entfernt; neue Felder: `lap1_length_m`, `standard_lap_length_m`, `grid_time_s`, `start_interval_min` |
| `StartLine` | `name` entfernt; `number` (int) statt String |
| `RaceClass` | `start_line` entfernt (Klassen nur für Auswertung) |

### ExcelReader V2 (Named Ranges)
| Datei | Änderung |
|---|---|
| `python/excel/excel_reader_v2.py` | **Neu** – Reader basiert auf Named Ranges (INFO/RACES/STARTER), kein Fuzzy-Matching mehr; parse_range, km→m Konvertierung, Sheet-Namen mit trailing Spaces, Bracket-Stripping in Header-Normalisierung |
| `tests/test_excel_reader_v2.py` | **Neu** – 13 Tests (read, fields, display_name, race_distribution, startreihen, lap_length, cell_parsing) |

### Anpassungen bestehender Code
| Datei | Änderung |
|---|---|
| `python/core/demo_data.py` | An neue Models angepasst (race_number/startreihe bei Startern, Rundenlängen pro RaceConfig) |
| `python/core/race_engine.py` | Klassen werden aus Startern abgeleitet (statt class_mapping); Startreihen aus Startreihe-Feldern |
| `python/gui/panels.py` | `event.title`, `starter.display_name`, Klassen aus Startern abgeleitet |
| `python/gui/main_window.py` | Race-Selector aus Startern abgeleitet, Klassen-Filterung über race_number |
| `python/excel/excel_result_writer.py` | `event.title`, `starter.skier`, Klassen aus Results abgeleitet |
| `tests/test_models_demo.py` | Angepasst an neue Models |
| `tests/test_result_calculator.py` | `boot_name` → `skier` |
| `tests/test_class_finish_tracker.py` | `start_line=` entfernt aus RaceClass-Konstruktor |
| `tests/test_race_engine.py` | Angepasst an neue Models |

**Verifikation:** **155/155 Tests grün** (7.5s).

## 2026-08-20 – startreihe_offset_s konfigurierbar + ExcelReader V2 in Main-App

| Datei | Änderung |
|---|---|
| `python/config/app_settings.json` | `startreihe_offset_s: 15` ergänzt (Konfiguration des Startreihen-Offsets) |
| `python/config/app_config.py` | `AppSettings.startreihe_offset_s: int = 15` als persistenter Parameter |
| `python/gui/main_window.py` | **AppController** akzeptiert `excel_path` – lädt Daten über ExcelRaceReaderV2 (Named Ranges), Fallback auf Demo-Daten; Offset wird aus Settings an `engine.load_race()` übergeben; Fußzeile zeigt Datenquelle |
| `python/main.py` | `--excel` CLI-Argument für Excel-Pfad; wird an `run_app()` weitergeleitet |
| `scripts/preview_gui.py` | `--excel` CLI-Argument ergänzt; wird an `AppController` weitergeleitet |

**Verifikation:** **155/155 Tests grün** (8.1s).

---

## 2026-08-15 – Export-Button in der GUI + PyInstaller-Build (.exe) + Stdlib-Konflikt behoben

| Datei | Änderung |
|---|---|
| `python/gui/panels.py` | **HotkeyPanel:** neuer Bereich „Ergebnis-Export" mit Button „Ergebnis exportieren (.xlsx)" + Status-Label; `set_on_export()` / `set_export_status(text, ok)` (grün/rot/neutral) |
| `python/gui/main_window.py` | **AppController:** `export_dir`-Parameter + `on_export_results()` – baut `RaceResultExport` (Event + RaceConfig + `get_placements()`), schreibt per `ExcelResultWriter` als `Ergebnis_Rennen{N}_<Zeitstempel>.xlsx` (immer neue Datei, Rohdaten unangetastet); Fehler → Log-Feed + rotes Status-Label; `_load_race` setzt Status zurück. **run_app:** + `auto_close_seconds` (Auto-Close mit deterministischer Fensterposition) |
| `python/main.py` | **Neu** – Produktions-Einstieg für die .exe: `parse_args()` (Sekunden + `--hotkeys`), `setup_logging`, `run_app(...)`; **FATAL-Handler** schreibt unbehandelte Exceptions in `gui_startup.log` (Diagnose ohne Konsole) |
| `scripts/build_exe.py` | **Neu** – PyInstaller-Build: `--onefile --noconsole`, `--add-data "app_settings.json;config"`, **`--hidden-import keyboard`** (wird lazy importiert → sonst fehlt die Library!), `--collect-all customtkinter` → `dist/Wasserski-Zeitnehmung.exe` |
| `python/config/app_config.py` | **Neu: `resolve_settings_path()`** – bundle-fähig: gebaute .exe nutzt `app_settings.json` NEBEN der .exe (editierbar), beim ersten Start einmalig aus `sys._MEIPASS/config/` kopiert; Entwicklung unverändert (python/config/) |
| `python/logger/` | **UMBENANNT aus `python/logging/`** (alle Imports `python.logging` → `python.logger`) – **Stdlib-Konflikt:** beim Start aus `python\main.py` (und im Bundle) wurde `import logging` fälschlich auf unser Paket aufgelöst → `AttributeError: module 'logging' has no attribute 'getLogger'` (Skript-Verzeichnis `python/` im sys.path). preview_gui aus `scripts/` war nie betroffen – die .exe aber crashte! |
| `python/logger/app_logger.py` | **stderr-Fix:** `sys.stderr` ist bei PyInstaller `--noconsole` `None` → Konsolen-Sink wird übersprungen (loguru.add(None) hätte die .exe crashen lassen, „Unhandled exception in script") |
| `python/config/app_settings.json` | Erst-Start-Kopie der .exe verifiziert (liegt jetzt neben der .exe, editierbar) |
| `tests/conftest.py` | **Neu** – Session-weites Tk-Fenster (`tk_window`-Fixture): beseitigt Flakiness (sporadische `TclError` bei mehreren Tk-Fenstern pro Prozess); alle GUI-Module nutzen es |
| `tests/test_gui_smoke.py` | **+5 Export-Tests** (im Modul-Fenster): Button-Callback, .xlsx-Meta-Daten (Rennen 2), Status-Label grün, Fehlerfall rot (monkeypatch `ExcelWriteError`), Renn-Wechsel-Reset |
| `tests/test_hotkey_activation.py` | Nutzt jetzt das Session-Fenster aus conftest.py (kein eigenes Tk mehr) |
| `tests/test_models_demo.py` | **+4 Tests** `TestBundleSettingsPath` (Dev-Pfad, neben .exe, einmalige Kopie, Fallback bei Kopierfehler) |
| `tests/test_main_entry.py` | **Neu** – 3 Tests `main.py parse_args` (Default, Sekunden+Hotkeys, negative Sekunden) |
| `tests/test_app_logger.py` | **Neu** – 2 Tests (Regression: `sys.stderr=None` crasht nicht mehr; Konsole+Datei) |
| `AGENTS.md` | Strukturliste: `python/logging/` → **`python/logger/`** (Hinweis „NICHT logging – kollidiert mit Stdlib!") |

**Verifikation:** **146/146 Tests grün** (stabil, 2 Läufe). `python python/main.py 5` läuft sauber. **.exe-Smoke-Test:** Start (alle Panels, Rennen 2), Auto-Close nach 5 s, Exit-Code 0; `app_settings.json` neben der .exe kopiert, `gui_startup.log` + `blackbox.log` erzeugt. Debug-Zwischenstand (WSK-DEBUG.exe) entfernt.

## 2026-08-15 – Excel-Export (Baustein 1) + Hotkey-Aktivierung (Baustein 2) + zentrale Version

| Datei | Änderung |
|---|---|
| `AGENTS.md` | **Regel 5 (Activity-Log):** verbindliches Release-Vorgehen ACTIVE_CHANGES ↔ RELEASE_LOG (Version bumptr → nach RELEASE_LOG übernehmen → ACTIVE_CHANGES leeren → PROJECT_LOG). **Regel 7 (Version):** `python/config/version.py` ist Single Source of Truth; `scripts/bump_version.py X.Y.Z` synchronisiert zusätzlich die Root-`VERSION`-Datei; GUI-Header zeigt `v{VERSION}` |
| `RELEASE_LOG.md` | **Neu** – Release-Protokoll (Struktur + Format-Vorlage, noch keine Releases) |
| `python/core/time_format.py` | **Neu** – zentrale `format_duration()` (MM:SS.t) + `NO_TIME_PLACEHOLDER`; GUI und Excel-Export nutzen dieselbe Funktion |
| `python/gui/panels.py` | Umgestellt auf `time_format.format_duration`; lokale Duplikat-Funktion + `timedelta`-Import entfernt |
| `python/excel/excel_result_writer.py` | **Neu** – `ExcelResultWriter` (openpyxl): Meta-Zeilen 1–6, Tabellenkopf Zeile 8, Daten ab Zeile 9, Sieger-Zeile grün `E2EFDA`, Boote ohne Runde → „–“, Spaltenbreiten, Tab „Ergebnisse“; `_ensure_writable()` prüft Windows-Excel-Lock VOR dem Schreiben; `ExcelWriteError`; `RaceResultExport` (frozen dataclass) |
| `tests/test_excel_result_writer.py` | **Neu** – 8 Tests (u. a. End-to-End RaceEngine→Excel, Sperrdatei → ExcelWriteError via ctypes, Platzierungs-Sortierung) |
| `python/config/app_config.py` | `AppSettings.enable_keyboard: bool = False` (systemweite Hotkeys per Konfiguration schaltbar; Admin nötig, AGENTS.md §10) |
| `python/config/app_settings.json` | `enable_keyboard: false` |
| `python/gui/main_window.py` | `run_app(enable_keyboard=None)` – None → Wert aus app_settings.json; Blackbox bleibt immer aktiv |
| `scripts/preview_gui.py` | **Neu** – `parse_args()` + `--hotkeys`-Flag (testbar); Aktivierung: Flag gewinnt, sonst Settings; Admin-Warnung im Log |
| `Start_Zeitnehmung_Admin.cmd` | **Neu** – Start mit systemweiten Hotkeys: Selbst-Elevation per UAC (`net session`-Check → PowerShell `RunAs`), dann `preview_gui.py --hotkeys`; UTF-8/CRLF |
| `tests/test_hotkey_activation.py` | **Neu** – 8 Tests (Config-Roundtrip, Controller-Verdrahtung mit Fake-keyboard, Hotkeys ohne Blackbox → ValueError, CLI-Parsing) |
| `scripts/bump_version.py` | **Neu** – Versions-Skript: validiert X.Y.Z, schreibt `version.py` + Root-`VERSION` synchron, `--check` nur Anzeige |
| `tests/test_bump_version.py` | **Neu** – 5 Tests (isoliert via tmp_path); deckte Regex-Fix auf: `^`/`$` brauchten `re.MULTILINE` für Zeilenanker |

**Verifikation:** **132/132 Tests grün**; `bump_version.py --check` + Sync live getestet (version.py + VERSION = 0.1.0); GUI-Smoke-Test `preview_gui.py 5` sauber (Rennen 2 geladen, Auto-Close, Hotkey-Hinweis im Log).

## 2026-08-14 – Header-Branding korrigiert + Doppel-Logging behoben

| Datei | Änderung |
|---|---|
| `python/config/app_config.py` | **Branding-Konstanten zentralisiert:** `BRANDING_NAME`, `BRANDING_URL` (`www.engl.biz`), `BRANDING_EMAIL` (`edv@engl.biz`) – Header und Footer nutzen jetzt dieselbe Quelle (kein Sync-Fehler mehr) |
| `python/gui/panels.py` | HeaderPanel: falsche Homepage `www.EDVEnglRoman.de` → `Cfg.BRANDING_URL` |
| `python/gui/main_window.py` | Footer nutzt zentrale Branding-Konstanten; **Doppel-Logging-Fix:** `_process_boot_key`/`on_manual_correction` zeigen jetzt ALLE neu erzeugten Engine-Events und synchronisieren `_last_event_count` erst danach (vorher: Event sofort angezeigt + vom Tick doppelt nachgeholt; in Endphase PASSAGE+FINISH sogar 3 Meldungen) |
| `tests/test_gui_smoke.py` | **Neu:** `test_key_press_logs_exactly_once` – Regressionstest: 1 Hotkey-Klick = genau 1 Log-Eintrag |

**Verifikation:** **111/111 Tests grün**; GUI-Smoke-Test ohne Fehler.

## 2026-08-14 – Live-Tabelle: Blinken behoben + Footer-Kontaktdaten

| Datei | Änderung |
|---|---|
| `python/gui/panels.py` | **LiveTablePanel umgebaut:** Zeilen werden wiederverwendet statt bei jedem 50-ms-Tick zerstört und neu aufgebaut (Ursache des Flackerns). Neue Hilfsklasse `_TableRow` (Snapshot `rendered`) – nur echte Änderungen lösen `configure()` aus; `_add_row` legt einmalig an, `_refresh_row` aktualisiert gezielt |
| `python/gui/main_window.py` | Footer-Kontakt: `info@EDVEnglRoman.de` → **`www.engl.biz | edv@engl.biz`** (aktuelle Kundendaten) |

**Verifikation:** 110/110 Tests grün; GUI-Smoke-Test ohne Fehler.

## 2026-08-14 – Start-CMD für normalen Programmstart

| Datei | Änderung |
|---|---|
| `Start_Zeitnehmung.cmd` | **Neu** – per Doppelklick startbar: nutzt `.venv` (mit Fehlerhinweis falls fehlt), ruft `scripts/preview_gui.py` auf, reicht optionale Sekunden-Argumente durch (Auto-Close), `pause` nach Beenden; UTF-8 + CRLF |

**Verifikation:** Smoke-Test `Start_Zeitnehmung.cmd 5` → GUI startet, schließt nach 5 s, Log in `gui_startup.log`.

## 2026-08-14 – Blackbox (Beweis-Log) + systemweite Hotkey-Erfassung

| Datei | Änderung |
|---|---|
| `AGENTS.md` | Kommentar-Konvention auf **Deutsch** umgestellt (Kundenwunsch, Entscheidung 2026-08-13); Blackbox-Regel (sofortiger append-only Druck) ergänzt; Fortschrittsstand aktualisiert |
| `python/logging/blackbox.py` | **Neu** – `BlackboxWriter` (append-only TXT, flush nach jedem Eintrag, threading.Lock, Rotation bei 10 MB mit Zeitstempel-Suffix, replay() für Renn-Rekonstruktion) + `format_timestamp` (Mikro→ms) |
| `python/core/input_handler.py` | **Neu** – `HotkeyMapping` (Boot-Key→"a".."z" + Zahlenblock-Alias 1–0 für erste 10 Starter, ADR-008) + `InputHandler` (keyboard.on_press, sofortiger Blackbox-Rohdruck `TASTE: '<taste>'`, input_queue, update_mapping) |
| `python/gui/main_window.py` | AppController: **Blackbox + InputHandler integriert** – `blackbox_path`/`enable_keyboard`-Parameter, `_process_boot_key` (gemeinsamer Pfad GUI-Klick + System-Hotkey), `_show_event` schreibt Blackbox-Eintrag (EVENT+STATUS), Tick drainnt input_queue, `run_app` aktiviert Blackbox (`blackbox.log`) |
| `tests/test_blackbox.py` | **Neu** – 12 Tests (append-only, flush, Format, Rotation, Thread-Sicherheit 20 Threads, replay, format_timestamp) |
| `tests/test_input_handler.py` | **Neu** – 9 Tests (Mapping letters/numpad/key_to_boot, on_event mit FakeKeyEvent, blackbox-Rohdruck, stop-safe) |
| `tests/test_gui_smoke.py` | +2 Integrationstests: Blackbox protokolliert START+PASSAGE; Queue-Drain → Runde |

**Verifikation:** Gesamt **110/110 Tests grün** (~12 s). Smoke-Test: App startet mit Blackbox, `blackbox.log` enthält `[ts] TASTE: 'A' EVENT: PASSAGE STATUS: VALID` und `[ts] EVENT: START STATUS: VALID`.

**Hinweis:** systemweite Hotkeys benötigen Windows-Admin (keyboard-Library) – `run_app()` startet sie deshalb bewusst NICHT automatisch; Aktivierung später per Konfiguration.

## 2026-08-14

| Datei | Änderung |
|---|---|
| `python/logging/app_logger.py` | **Neu** – zentrale Logging-Klasse (loguru: Konsole + TXT-Datei, setup_logging, log_progress für Start-Diagnose) |
| `scripts/preview_gui.py` | Start-Sequenz mit 5-Schritt-Logging (`gui_startup.log`); MainWindow-Diagnose |
| `python/gui/main_window.py` | Schritt-Logging in MainWindow/AppController; `report_callback_exception` → Fehler landen im Log; **Workaround** `CTk._deactivate_windows_window_header_manipulation=True` |
| `scripts/diagnose_gui.py` | **Neu** – Isolationstest T1 (tkinter) / T2 (CustomTkinter) / T3 (MainWindow), je mit Auto-Close |
| `requirements.txt` | customtkinter 5.2.1 → **6.0.0** |
| `_BOTBRAIN/gui_fixed.png` + `.txt` | Screenshot-Verifikation nach Fix (GUI vollständig gerendert) |
| `PROJECT_LOG.md` | GUI-Bug-Analyse dokumentiert (CustomTkinter-Titelbar-Bug), Fix + Verifikation |
| `python/gui/panels.py` | CountdownPanel: RENNSTART entfällt → **PAUSE/WEITER** (gelb) + NEUSTART; neue Methoden set_callbacks/set_pause_mode/set_pause_enabled |
| `python/gui/main_window.py` | **Q8 implementiert:** Countdown startet Rennen automatisch (kein Startsignal), PAUSE/WEITER unterbricht/führt fort, NEUSTART = Countdown neu bzw. zurück zum Vorstart (Q4); PHASE_COUNTDOWN entfernt |
| `tests/test_gui_smoke.py` | 4 neue Tests: auto_start, pause/resume, pause blockiert Start, reset |
| `_BOTBRAIN/object_model_plan.md` | Q6 beantwortet (nur +1 im MVP), Q8 beantwortet (Countdown startet automatisch, pausierbar/neustartbar) |
| `_BOTBRAIN/gui_q8.png` + `.txt` | Screenshot-Verifikation: PAUSE/NEUSTART sichtbar, Countdown läuft (00:00:19) |

**Entscheidungen (2026-08-14):** Q6 = nur +1 im MVP (keine −1-Korrektur); Q8 = der Countdown startet das Rennen automatisch, kein eigenes Startsignal, aber unterbrechbar (PAUSE/WEITER) und neu startbar (NEUSTART).

**🐛 GUI-Bug behoben (schwarzes Fenster):** CustomTkinter `_windows_set_titlebar_color()` enthält zwei logische Fehler (Tautologie Zeile 282, `or True` Zeile 316) → Fenster blieb `withdrawn` und mainloop crashte mit „application has been destroyed“. Fix: offizieller Deaktivierungs-Schalter. Verifikation: Screenshot + KI-Analyse bestätigen vollständiges Rendering.

## 2026-08-14 – RaceEngine + GUI-Anbindung (Meilenstein)

| Datei | Änderung |
|---|---|
| `python/core/lockout_manager.py` | **Neu** – Sperrzeit je Boot (§5.2): is_allowed/register/remaining/reset |
| `python/core/result_calculator.py` | **Neu** – add_lap (erste Runde ab Rennstart) + compute_results (Runden primär, Gesamtzeit sekundär) |
| `python/core/class_finish_tracker.py` | **Neu** – klassenweise Rennende-Logik (§5.3): WAITING → TRIGGERED → CLOSED |
| `python/core/race_engine.py` | **Neu** – RaceEngine: Phasen PRESTART→ACTIVE→FINISHING→FINISHED, Countdown-Pause (Q8), handle_key_press (Sperrzeit/Runde/FINISH-Logik Q2), handle_manual_correction nur +1 (Q6), tick/reset/placements/class-status; injizierbare `now`-Zeitquelle; lockout_until als Anzeige-Feld |
| `tests/test_lockout_manager.py` | **Neu** – 6 Tests |
| `tests/test_result_calculator.py` | **Neu** – 6 Tests |
| `tests/test_class_finish_tracker.py` | **Neu** – 5 Tests |
| `tests/test_race_engine.py` | **Neu** – 16 Tests |
| `python/gui/main_window.py` | **AppController auf RaceEngine umgestellt** (keine Demo-Phasen-Simulation mehr): _load_race → engine.load_race, Tick treibt engine.tick + Anzeige, Hotkeys/Korrektur/Pause/Reset → Engine, Engine-Events → Log-Feed; PHASE_*-Konstanten entfernt |
| `python/gui/panels.py` | `RaceEndStatusPanel.update_states()` (schlankes Tick-Update), `HotkeyPanel.set_on_key()`, `ManualCorrectionPanel.set_on_correct()` |
| `python/core/race_engine.py` | lockout_until nach gültiger Passage gesetzt (SPERRZEIT-Zelle der Tabelle) |
| `tests/test_gui_smoke.py` | Auf RaceEngine umgestellt; **Modul-Fixture mit EINEM Fenster** (Tk-Stabilität unter Windows); 8 Tests |
| `_BOTBRAIN/gui_engine.png` + `.txt` | Screenshot-Verifikation der Engine-Anbindung; Pixel-Analyse bestätigt UI-Farben |
| `PROJECT_LOG.md` | RaceEngine-Meilenstein + GUI-Anbindung dokumentiert |

**Tk-Stabilität:** Mehrfaches `Tk()`/`destroy()` im selben Prozess crasht unter Windows mit „Can't find a usable tk.tcl“ → GUI-Smoke-Tests nutzen ein Modul-Fenster.

**Verifikation:** Gesamt **83/83 Tests grün** (~11 s). Screenshot: Countdown läuft (rot), PAUSE gelb, NEUSTART grün, Hotkeys grün, Live-Tabelle gefüllt (Pixel-Farbzählung).

## 2026-08-13

| Datei | Änderung |
|---|---|
| `_BOTBRAIN/object_model_plan.md` | **Neu** – Objektplan: Domänenmodelle, RaceEngine, LockoutManager, ResultCalculator, ClassFinishTracker, GUI-Klassen, Threading, 8 offene Fragen |
| `_BOTBRAIN/object_model_plan.md` | Q1–Q8 beantwortet (Sperrzeit=App-Parameter JSON, ZIEL automatisch, Strafanzeige entfällt, Reset=nächstes Rennen, Dropdown-Auswahl ja); neues Kapitel 4.11 AppSettings |
| `python/core/models.py` | **Neu** – Domänenmodelle (Event, Starter, StartLine, RaceConfig, RaceEvent frozen, Lap, BoatState + Properties, BoatResult, RaceClass, Enums) |
| `python/config/app_config.py` | **Neu** – AppConfig-Konstanten, AppSettings (lockout_seconds), ConfigManager (JSON) |
| `python/config/app_settings.json` | **Neu** – App-Parameter (Sperrzeit 2.0s) |
| `python/core/demo_data.py` | **Neu** – fiktive Demo-Daten (ÖM Ybbs 2026, 3 Rennen, 9 Starter, Rennen 2 U18 Open mit simulierten Runden, deterministisch) |
| `tests/test_models_demo.py` | **Neu** – 11 Tests (Modelle, Demo, ConfigManager) |
| `PROJECT_LOG.md` | Objektplan dokumentiert; Konvention „Code Englisch + Kommentare Deutsch“ (Kundenwunsch, AGENTS.md noch anzupassen); UI-Start freigegeben |
| `AGENTS.md` | ⚠️ Noch offen: „Kommentare in Englisch“ → Deutsch (wartet auf Freigabe) |

## 2026-08-12

| Datei | Änderung |
|---|---|
| `AGENTS.md` | Komplett neu geschrieben – von Laravel/Gastro auf Waterski/Python umgestellt |
| `PROJECT_LOG.md` | Initialisiert mit Projektstand, 8 ADRs, Setup-Protokoll |
| `ACTIVE_CHANGES.md` | Diese Datei – initialisiert |
| `.gitignore` | Neu erstellt (Python, Excel, Logs, Build-Artefakte) |
| `requirements.txt` | Neu erstellt (customtkinter, openpyxl, keyboard, pyinstaller, loguru, pytest) |
| `python/core/__init__.py` | Neues Package |
| `python/gui/__init__.py` | Neues Package |
| `python/excel/__init__.py` | Neues Package |
| `python/logging/__init__.py` | Neues Package |
| `python/config/__init__.py` | Neues Package |
| `python/config/version.py` | Neu – Version 0.1.0 |
| `tests/__init__.py` | Neues Package |
| `VERSION` | Neu – 0.1.0 |
| `architecture_and_roadmap/01_system_setup.txt` | src/ → python/ korrigiert |
| `requirements.txt` | PyInstaller 6.2.0 → 6.22.0 (Python 3.14 Kompatibilität) |
| `python/logging/logging_util.py` | Verschoben von python/, Buffer-Konflikt behoben, input() testbar gemacht |
| `scripts/test_logging.py` | Import-Pfad aktualisiert, recovery_handler für Tests |
| `tests/test_logging.py` | Kopie des Tests im tests/-Ordner |
| `python/excel/excel_reader.py` | **Neu** – Excel-Reader mit 3 Sheets (Renndaten, Starter, Rennkonfiguration), fuzzy column matching, Umlaut-Support, Validierung |
| `tests/test_excel_reader.py` | **Neu** – 23 Tests (valid/invalid/missing/edge cases) |
| `Gemini_Generated_Image_jl5z2njl5z2njl5z.png` | GUI-Screenshot via AnalyzeImage.ps1 analysiert → `_BOTBRAIN/` |
| `_BOTBRAIN/Gemini_Generated_Image_jl5z2njl5z2njl5z.txt` | KI-Analyse des GUI-Screenshots |
| `PROJECT_LOG.md` | Session-Ende-Dokumentation: Status, Blockade (neue Excel-Version), nächste Schritte |

---

## ⏸️ SESSION-ENDE 2026-08-12
**Blockade:** Warten auf neue Excel-Version vom Kunden.
**Nächste Session:** PROJECT_LOG.md lesen → neue Excel analysieren → Rennlogik bauen.

### Verifikation
- Tests: 197/197 grün (Stand 2026-09-04, letzter Stand)
- Smoke-Test: .exe-Build via `Build_Dist.cmd` → `dist\Wasserski-Zeitnehmung.exe` (13.6 MB)

---

## Format für neue Releases

```markdown
## vX.Y.Z – JJJJ-MM-TT

### Neuerungen / Änderungen
| Datei | Änderung |
|---|---|
| ... | ... |

### Verifikation
- Tests: N/N grün
- Smoke-Test: ...
```
