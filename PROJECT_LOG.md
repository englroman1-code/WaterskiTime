# PROJECT_LOG.md – Ewiges Protokoll

## 2026-11-10 – Release v0.5.0

**Version:** 0.5.0 (Bump von 0.4.0 via `scripts/bump_version.py 0.5.0`)

**Inhalt:** Rennende-Ampel in der Live-Tabelle (grün/rot Punkt neben dem
Statustext) und klickbare Hotkey-Taste im Panel Tastaturbedienung (rot bei
offenem Boot, weiß bei Zielpassage); Runner-Spalte ohne Klasse; Doku
(`Manual.md`) aktualisiert.

**Vorgehen (AGENTS.md §5):**
1. Version auf 0.5.0 gebumpt (`python/config/version.py` + `VERSION`)
2. `ACTIVE_CHANGES.md` → `RELEASE_LOG.md` übernommen (v0.5.0, 2026-11-10)
3. `ACTIVE_CHANGES.md` geleert (nur Kopfzeile)
4. Dieses Release-Protokoll

**Verifikation:** 235 Tests grün.

---

## 2026-11-09 – Release v0.4.0

**Version:** 0.4.0 (Bump von 0.3.0 via `scripts/bump_version.py 0.4.0`)

**Inhalt:** Renndauer-Uhr nach dem Start aller Startreihen, Reset-Bugfix der
rechten Uhr, Ergebnis-Export um `distance`, `avg_speed` und `race_time`
erweitert, `penalties`/`points` als Platzhalter, PyInstaller-Build gegen
laufende `.exe` abgesichert, LF/CRLF-Fehler in `Build_Dist.cmd` behoben,
Auto-Close-Smoke-Test beendet mainloop und Fenster sauber, Handbuch und
Bedienungsanleitung auf Version 0.4.0 aktualisiert.

**Wichtig:** Der direkte Excel-Start aus der App ist weiterhin nicht
freigegeben (offener Punkt 1: `mdlEngl` vs. `mdl_Engl_Export`). `IMPORT.json`
weiterhin manuell in Excel über `ExportExpRangesToJSON` erzeugen.

**Vorgehen (AGENTS.md §5):**
1. Version auf 0.4.0 gebumpt (`python/config/version.py` + `VERSION`)
2. `ACTIVE_CHANGES.md` → `RELEASE_LOG.md` übernommen (v0.4.0, 2026-11-09)
3. `ACTIVE_CHANGES.md` geleert (nur Kopfzeile)
4. Dieses Release-Protokoll

**Verifikation:** 227/227 Tests grün; Build über `Build_Dist.cmd`
erfolgreich; `dist\Wasserski-Zeitnehmung.exe` 14,6 MB; Smoke-Test mit
`Wasserski-Zeitnehmung.exe 5 --json dist\IMPORT.json` → Exit-Code 0.

---

## 2026-11-09 – Build_Dist.cmd: LF-Zeilenenden repariert

**Symptom:** `.\Build_Dist.cmd` brach mit wirren Meldungen ab
(„Der Befehl "asserski-Zeitnehmung" ist entweder falsch geschrieben …“)
und meldete anschließend fälschlich, `.venv` fehle.

**Ursache:** Die Datei hatte ausschließlich LF-Zeilenenden. `cmd.exe`
benötigt bei Batchdateien CRLF; bei LF zerlegt es Zeilen an falschen
Stellen.

**Fix:** `Build_Dist.cmd` auf CRLF normalisiert. Zusätzlich `.gitattributes`
angelegt (`*.cmd`/`*.bat` → `text eol=crlf`), damit Git die Dateien bei
jedem Checkout wieder mit CRLF auscheckt.

**Verifikation:** Kompletter Build über `Build_Dist.cmd` erfolgreich
(14,6 MB), Start der .exe mit Auto-Close-Parameter `5` ohne Fehler.

---

## 2026-11-09 – Ergebnis-Export: Distance, avg_speed, Race_time, Penalties, Points

**Kontext:** Die Ergebnis-JSON hatte bisher nur Platz, Boot, Klasse, Fahrer,
Team, Club, Rennnummer, Runden, Gesamtzeit und beste Runde. Der Kunde
braucht zusätzlich die Auswertungsspalten aus `Zeitnehmung.xlsm`
(„results Herren“).

**Umgesetzt:**
- `distance` (km): `Länge R1 + (Runden − 1) × Länge R2+`; interne
  Rundenlängen in Metern werden durch 1000 geteilt. Entspricht der
  Excel-Formel `=Q2+((H2-1)*R2)` („Calc Strecke“).
- `avg_speed` (km/h): `distance ÷ total_time`; 1 Nachkommastelle.
- `race_time`: `eigene Zeit ÷ eigene Distanz × beste Distanz der Klasse`;
  Ausgabe als `MM:SS.t`-String (bei fehlender Distanz `–`).
- `penalties` und `points`: `null` als Platzhalter, da Strafen/Punkte
  weiterhin außerhalb der App gepflegt werden.

**Wichtig:** Die Referenz für `race_time` ist die **weiteste Distanz
innerhalb derselben Klasse im selben Rennen** (in der Wertung entspricht
das dem Sieger, weil primär nach Rundenzahl sortiert wird).

**Verifikation:** `tests/test_json_result_writer.py` neu (3 Tests, u. a.
mit den Zahlen aus der Kunden-Excel: 26,5 km / 23,0 km, 662,5 / 487,1 km/h,
Rennzeit 03:15.8). Gesamt **227/227 Tests grün**.

**Hinweis:** Kein Release, keine Versionserhöhung.

---

## 2026-11-09 – Build-Fix: laufende .exe sperrte den PyInstaller-Build

**Kontext:** `Build_Dist.cmd` schlug fehl mit
`PermissionError: [WinError 5] Zugriff verweigert` auf
`dist\Wasserski-Zeitnehmung.exe`.

**Ursache:** Die alte `.exe` war noch geöffnet (Bootloader- und
Kindprozess). PyInstaller entfernt die Zieldatei im EXE-Schritt und darf
das nicht, solange Windows sie als laufendes Image sperrt.

**Fix:**
- `Build_Dist.cmd` erkennt laufende `Wasserski-Zeitnehmung.exe`, warnt,
  fragt per `choice` nach dem Beenden und führt bei Zustimmung `taskkill`
  mit kurzer Wartezeit aus.
- `scripts/build_exe.py` prüft vor dem Build den Schreib-Lock der
  Zieldatei und meldet verständlich, dass die Anwendung geschlossen werden
  muss.

**Build:** Erfolgreich neu gebaut, `dist\Wasserski-Zeitnehmung.exe`
(14,6 MB, 09.11.2026 15:14). Smoke-Test `...exe 5` → Exit-Code 0,
Startprotokoll sauber (5 Rennen, 25 Starter geladen).

**Hinweis:** Kein Release, keine Versionserhöhung.

---

## 2026-11-09 – Uhren: Reset-Bugfix + Renndauer nach allen Startreihen

**Kontext:** Zwei Kundenrückmeldungen zu den Uhren im Countdown-Panel.

**Bugfix:** Nach **NEUSTART** blieb die rechte Uhr („VERBLEIBENDE ZEIT“) auf
dem letzten Wert stehen, weil der `RESET`-Tick nur die linke Kachel
aktualisierte. Jetzt setzt der Tick die verbleibende Zeit in `RESET`
explizit auf `00:00` (Balken 0). Damit ist der Reset-Zustand vollständig
sauber und unabhängig von vorherigen Anzeigewerten.

**Feature:** Nach dem Start aller Startreihen ist der Startreihen-Countdown
bedeutungslos. Die linke Kachel zeigt ab dann **„RENNDAUER:“** – die Zeit
seit dem ersten Start (`race_start`). Neue Engine-Methode
`RaceEngine.race_elapsed(now)`; in `FINISHED` friert sie auf den letzten
Zieleinlauf ein. Der Fortschrittsbalken zeigt `Renndauer / geplante Dauer`.

**Geänderte Dateien:**
- `python/core/race_engine.py` – `race_elapsed()`
- `python/gui/panels.py` – `CountdownPanel.set_race_elapsed()`
- `python/gui/main_window.py` – RESET setzt rechte Uhr zurück; linke Uhr
  zeigt nach allen Reihen die Renndauer
- `tests/test_race_engine.py`, `tests/test_gui_smoke.py` – 3 neue Tests
- `Manual.md` – Abschnitte 5.3, 7.5, 8.1, 8.3 aktualisiert

**Verifikation:** **224/224 Tests grün** (~21 s).

**Hinweis:** Kein Release, keine Versionserhöhung.

---

## 2026-11-08 – Manual.md als vollständiges Benutzerhandbuch neu geschrieben

**Kontext:** Das bisherige `Manual.md` war eine knappe technische Beschreibung
und für den Kunden am Renntag nicht ausreichend. Vorgabe: ausführliches
deutschsprachiges Handbuch, abgeglichen mit `Pflichtenheft_V1.md` und dem
tatsächlichen Python-Code, mit Bildplatzhaltern.

**Ergebnis:**
- `Manual.md` komplett neu: 20 Abschnitte von Systemvoraussetzungen über
  Bedienung, Excel-Vorbereitung, Rennablauf, Sperrzeit, Crash-Recovery,
  Export, Datenfluss, technische Referenz, Ereignis-Log und Fehlerbehebung
  bis zu Glossar und Dokumenthistorie.
- Abweichungen zum Pflichtenheft sind in Abschnitt 16 dokumentiert
  (u. a. manuelles Klassenende statt automatischer Ziellogik,
  Startreihen-Offset, km-Angaben in Excel, eingeschränkter Excel-Direktstart).
- 14 Bildplatzhalter B1–B14 mit Dateinamen unter `bilder/`; neuer Ordner
  `bilder/` inkl. `README.md` mit Screenshot-Liste und Vorgaben.
- `BEDIENUNGSANLEITUNG.md` verweist jetzt auf das vollständige Handbuch.

**Hinweis:** Kein Laufzeitcode geändert, keine Versionserhöhung.

---

## 2026-11-06 – Release v0.3.0 (Release-Kandidat)

**Version:** 0.3.0 (bump von 0.2.0 via `scripts/bump_version.py 0.3.0`)

**Inhalt:** Crash-Recovery gehärtet (vollständige Runden, 12h-Altersprüfung,
Rennnummer + Quell-Fingerprint, atomares Schreiben, Save-Drosselung),
altes `IMPORT.json`-Format wird klar abgelehnt, Blackbox mit `fsync`,
Laufzeitdateien neben der `.exe`, `START`/`STARTLINE`-Details im Renn-Log,
`DataValidator` prüft Startreihe, Doku/Manual/Bedienungsanleitung aktualisiert.

**Wichtig:** Release-Kandidat – der direkte Excel-Start aus der App ist noch
nicht freigegeben (offener Punkt 1: `mdlEngl` vs. `mdl_Engl_Export`). Bis zur
Korrektur `IMPORT.json` manuell in Excel erzeugen.

**Vorgehen (AGENTS.md §5):**
1. ✅ Version auf 0.3.0 gebumpt (`version.py` + `VERSION`)
2. ✅ `ACTIVE_CHANGES.md` → `RELEASE_LOG.md` übernommen (v0.3.0, 2026-11-06)
3. ✅ `ACTIVE_CHANGES.md` geleert (nur Kopfzeile)
4. ✅ Dieses Release-Protokoll

**Verifikation:** 217/217 Tests grün (11.10s); .exe-Build via
`scripts/build_exe.py` → `dist/Wasserski-Zeitnehmung.exe`.

---

## 2026-09-04 – JsonRaceStore: Fuzzy-Matching entfernt

**Kontext:** Kundengespräch – neue IT-amerikanische Feldnamen in der Excel
(CODE-Spalte für Parameter, `FLD_`/`FLC_`-Präfixe für Races/Starter).

**Änderung:** `json_race_store.py` komplett umgebaut. Weg von fuzzy
deutschen Keys (`"Renndauer\n[min]"`, `"Skier "`) hin zu direkten
Matches (`FLD_RACEDUR`, `FLD_SKIER`). `re`-Import und `_normalize_key()`
entfernt.

**Vorher/Nachher:**
- INFO: substring `"veranstaltung" in key` → `CODE == "PAR_EVENT"`
- Races: `_get_int(item, "renndauer")` → `_get_int(item, "FLD_RACEDUR")`
- Starter: `_get_str(item, "skier")` → `_get_str(item, "FLD_SKIER")`
- `FLC_CLUB` (nicht `FLD_CLUB` – Sonderfall im VBA)

**Verifikation:** 198/198 Tests grün.

---

## 2026-09-04 – Release v0.2.0 (erstes offizielles Release)

**Version:** 0.2.0 (bump von 0.1.0 via `scripts/bump_version.py 0.2.0`)

**Inhalt:** Erstes offizielles Release. Der gesamte Entwicklungsstand seit
Projektstart (2026-08-12) wurde aus `ACTIVE_CHANGES.md` in `RELEASE_LOG.md`
übernommen. Die App umfasst: Excel/JSON-Datenhaltung (IMPORT.json via VBA-Makro),
RaceEngine (Zustandsmaschine), GUI (CustomTkinter), Blackbox-Log, systemweite
Hotkeys, Ergebnis-Export (JSON), Platzierung pro Klasse und PyInstaller-Build.

**Vorgehen (AGENTS.md §5):**
1. ✅ Version auf 0.2.0 gebumpt (`version.py` + `VERSION`)
2. ✅ `ACTIVE_CHANGES.md` → `RELEASE_LOG.md` übernommen (v0.2.0, 2026-09-04)
3. ✅ `ACTIVE_CHANGES.md` geleert (nur Kopfzeile)
4. ✅ Dieses Release-Protokoll

**Verifikation:** 197/197 Tests grün (Stand 2026-09-04); .exe-Build via
`Build_Dist.cmd` → `dist\Wasserski-Zeitnehmung.exe` (13.6 MB).

---

## 2026-09-04 – Platzierung pro Klasse (Bugfix)

### Kunden-Feedback (2026-09-04)
Im Export wurde die Platzierung **global über alle Boote** vergeben. Dadurch
war z. B. Boot 172 (Klasse Herren) mit Platz 2 markiert, obwohl es in seiner
Klasse der Erste ist. **In jeder Klasse gibt es einen Ersten, Zweiten, …**

### Fix
`ResultCalculator.compute_results()` vergibt die Platzierung jetzt **pro
Klasse**: Die Sortierung (Runden absteigend, Gesamtzeit aufsteigend) bleibt
innerhalb jeder Klasse gleich, aber die Platznummern starten in jeder Klasse
wieder bei 1.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/core/result_calculator.py` | `compute_results()`: Platzierung pro Klasse |
| Tests | `test_result_calculator.py` +1, `test_race_engine.py` angepasst |

**Verifikation:** 197/197 Tests grün (9.99s).

---

## 2026-09-03 – Export-Button immer aktiv + Start-Button bei beendetem Rennen deaktiviert

### Kunden-Feedback (2026-09-03)
Nach der Ergebnis-Persistenz (Option 1):
1. **Start-Button wird beim Zurückwechseln zu einem beendeten Rennen angezeigt**
   – obwohl das Rennen schon fertig ist. Der Start soll dort nicht möglich sein.
2. **Keine Export-Möglichkeit beim beendeten Rennen** – obwohl die Daten da sind.

### Lösung
- **Export-Button immer aktiv:** Der Export enthält ALLE fertigen Rennen auf
  einmal – unabhängig vom aktuellen Rennen. Ohne beendetes Rennen wird eine
  Datei mit nur den Stammdaten (Event) und leerer `races`-Liste erzeugt.
- **Start-Button bei beendetem Rennen deaktiviert:** Beim Laden eines bereits
  beendeten Rennens (liegt in `finished_races`) wird der START-Button grau und
  inaktiv gesetzt.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | Export-Button immer aktiv; `on_export_results()` erzeugt auch ohne beendetes Rennen eine Datei; `_load_race()` deaktiviert START bei beendetem Rennen |
| `python/gui/panels.py` | `CountdownPanel.set_start_enabled()` |
| `python/config/app_config.py` | `COLOR_DISABLED` |
| `python/excel/json_result_writer.py` | `write_all_races()` optionaler `event`-Parameter (Stammdaten-Export) |
| Tests | `test_gui_smoke.py` +3 |

**Verifikation:** 196/196 Tests grün (12.62s).

---

## 2026-09-03 – Ergebnis-Persistenz beim Rennwechsel + Export aller fertigen Rennen

### Kundenentscheidung (2026-09-03)
Die Ergebnisse eines **beendeten** Rennens sollen beim Rennwechsel **in-memory
erhalten** bleiben (Option 1). Beim Zurückwechseln zu einem bereits beendeten
Rennen sind die Ergebnisse (Runden, Platzierung, Klassen-Status, Renn-Log)
wieder da.

Zusätzlich: Der Export enthält **ALLE fertigen Rennen** in EINER Datei,
gruppiert nach Rennen und Klasse (Kundenwunsch: "Rennen 1 Klasse Herren:
erster, zweiter, … / Rennen 2 Klasse Junioren: …").

### Architektur-Entscheidung (ADR-012)
**Status:** Akzeptiert
**Hintergrund:** Bisher erzeugte `load_race()` komplett neue leere
`BoatState`-Objekte und leerte `events` → Ergebnisse gingen beim Rennwechsel
verloren.

**Entscheidung:**
- `RaceEngine` hält `finished_races: dict[int, dict]` (keyed by `race_number`).
- Bei `FINISHED` speichert `_store_finished_race()` config, results, events,
  classes, boats.
- `load_race()` ruft am Ende `_restore_finished_race()` auf – spielt
  laps/finished_at/place/events/Klassen-Status in die neuen BoatStates zurück.
- Der Export nutzt `JsonResultWriter.write_all_races()` → eine Datei
  `Ergebnis_AlleRennen_<Zeitstempel>.json`, `races[]` sortiert nach
  Rennnummer, Ergebnisse nach Klasse gruppiert.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/core/race_engine.py` | `finished_races`, `_store_finished_race()`, `_restore_finished_race()`, `finish_class()` (speichert bei FINISHED) |
| `python/excel/json_result_writer.py` | `write_all_races()` (Klassen-Gruppierung, Sortierung nach race_number) |
| `python/gui/main_window.py` | `on_export_results()` exportiert alle fertigen Rennen via `write_all_races` |
| Tests | `test_race_engine.py` +2, `test_gui_smoke.py` +1 |

**Verifikation:** 193/193 Tests grün (7.64s).

---

## 2026-09-03 – 3 Kundenanforderungen umgesetzt (Runner-Spalte fix, Beenden-Button, Geschw.-Spalte)

### Kundenentscheidungen (2026-09-03)
1. **Runner-Spalte mit fixer Breite:** Zu lange Namen werden abgeschnitten
   (mit "…"), die Spalte dehnt sich nicht.
2. **"Beenden"-Button erst aktiv wenn Rennzeit abgelaufen:** Vorher sichtbar
   aber inaktiv (grau). Erst in Phase FINISHING/FINISHED aktiv (gelb), wieder
   inaktiv sobald die Klasse CLOSED ist.
3. **Neue Spalte "Geschw." in der Live-Tabelle:** Zwei Werte getrennt durch
   "/": a) km/h letzte Runde (Strecke letzter Runde / Rundenzeit; 1. Runde
   nutzt `lap1_length_m`), b) km/h gesamt (Gesamtstrecke / Zeit bis zum
   letzten Passieren der Startlinie). Fehlender Wert → "–".

### Architektur-Entscheidung (ADR-011)
**Status:** Akzeptiert
**Hintergrund:** Die Geschwindigkeitsberechnung soll sowohl in der Live-Tabelle
als auch später im Export nutzbar sein.

**Entscheidung:**
- Die km/h-Berechnung liegt in `BoatState` (`speed_last_lap`/`speed_total`)
  mit den Streckenlängen als Parameter – nicht im GUI.
- Die Streckenlängen kommen aus der IMPORT.json (`lap1_length_m`,
  `standard_lap_length_m`) und werden per `set_lap_lengths()` an das Panel
  übergeben.
- Der Beenden-Button-Zustand wird zentral in
  `_apply_finish_button_state()` gesteuert (aktiv nur wenn Rennzeit abgelaufen
  + Klasse nicht CLOSED).

### Änderungen
| Datei | Änderung |
|---|---|
| `python/core/models.py` | `BoatState.speed_last_lap()`/`speed_total()` (km/h) |
| `python/gui/panels.py` | LiveTablePanel: Geschw.-Spalte, Runner-Abschneidung, `set_lap_lengths`, `_truncate_runner`, `_format_speed`; RaceEndStatusPanel: `set_race_over`, `_apply_finish_button_state`, `_is_closed` |
| `python/gui/main_window.py` | `_load_race` (set_lap_lengths), `_tick` (set_race_over) |
| `tests/conftest.py` | `_clean_race_state` function-scope (Test-Isolation) |
| Tests | `test_models_demo.py` +5, `test_gui_smoke.py` +5 |

**Verifikation:** 189/189 Tests grün (7.73s).

---

## 2026-09-03 – 4 Kundenanforderungen umgesetzt (manuelle Ziellogik, Hotkeys, Startreihen-Countdown, Admin-Status)

### Kundenentscheidungen (2026-09-03)
1. **Manuelle Ziellogik:** Nach Ablauf der Renndauer passiert NICHTS automatisch.
   Jede Klasse bekommt im Rennende-Status einen "Beenden"-Button. Beim Drücken
   werden alle Boote der Klasse fertig (Ergebnis fest: meiste Runden in
   kürzester Zeit). Die "Letzte Runde"-Logik (finish_mode, TRIGGERED) wurde
   komplett entfernt. Klassen-Status nur noch: WARTEND → FERTIG.
2. **Hotkeys nur bei gestarteten Startern aktiv:** Grün/aktiv nur wenn die
   Startreihe des Boots gestartet ist, sonst grau und inaktiv.
3. **Startreihen-Countdown ANSTATT Vorstart-Countdown:** Die VORSTART-Kachel
   zeigt den Startreihen-Countdown ("START REIHE N:"), wenn das Rennen läuft
   und eine nächste Reihe startet. Keine separate Kachel mehr.
4. **Admin-Rechte-Status:** Bei der Überschrift "Tastaturbedienung (Hotkeys)"
   informativ anzeigen, ob die systemweiten Hotkeys aktiv (grün) oder inaktiv
   (grau) sind.

### Architektur-Entscheidung (ADR-010)
**Status:** Akzeptiert
**Hintergrund:** Die automatische Letzte-Runde-Logik war für den Bediener
schwer kontrollierbar. Der Kunde will die Ziellogik manuell steuern.

**Entscheidung:**
- `ClassFinishTracker` vereinfacht auf WAITING/CLOSED; neue `finish_class()`.
- `RaceEngine.finish_class()` beendet eine Klasse manuell (FINISH-Events je Boot,
  → FINISHED wenn alle Klassen CLOSED).
- `RacePhase.FINISHING` erreicht die Engine weiterhin nach Renndauer-Ablauf,
  aber es passiert nichts automatisch mehr.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/core/models.py` | `finish_mode` entfernt; `RaceClass.finish_state` nur WAITING/CLOSED |
| `python/core/class_finish_tracker.py` | Komplett neu (manuelle `finish_class`) |
| `python/core/race_engine.py` | `_process_finishing` entfernt; `finish_class()` neu; fertige Boote → INVALID |
| `python/gui/panels.py` | RaceEndStatusPanel (Beenden-Button), HotkeyPanel (`set_started_keys`, `set_hotkey_status`), CountdownPanel (Startreihen-Countdown in VORSTART-Kachel), LiveTablePanel |
| `python/gui/main_window.py` | `on_finish_class`, `set_started_keys`, Startreihen-Countdown, `is_admin`-Parameter, Hotkey-Status |
| `python/main.py` / `scripts/preview_gui.py` | `is_admin` an `run_app`/`AppController` |
| Tests | `test_class_finish_tracker.py` neu; `test_race_engine.py`/`test_gui_smoke.py` auf manuelle Ziellogik umgestellt |

**Verifikation:** 179/179 Tests grün (8.58s), GUI-Smoke 23/23 grün.

---

## 2026-08-20 – JSON-Architektur: Excel entkoppelt via VBA + IMPORT/IMPORT.json

### Kunden-Entscheidung: Begriffsklärung (2026-08-20)

| Begriff | Bedeutung |
|---|---|
| **Grid Time** | Zeit zwischen den Startreihen (z.B. 10s oder 15s) |
| **Startintervall** | Vorlaufzeit bis zum wirklichen Start |
| **StartTimer** | Brauchen wir nicht |

**Konsequenz:** `start_interval_min` → `start_interval_s` (Sekunden statt Minuten), Comment aktualisiert.

### Architektur-Entscheidung (ADR-009)
**Status:** Akzeptiert
**Hintergrund:** openpyxl-Locks im Rennbetrieb gefährlich. Kunde schlägt VBA-Makro als Zwischenschicht vor.

**Entscheidung:**
- **JSON statt direktem Excel-Zugriff** als primärer Datenpfad
- VBA-Makro `ExportExpRangesToJSON` erzeugt `IMPORT.json` aus `_EXP_`-Ranges
- Python App liest `IMPORT.json` (zentrale Logik, kein openpyxl)
- Python App schreibt `IMPORT.json` (`_IMP_LOG`, `_IMP_RESULTS`)
- **Kein Demo-Daten-Fallback** → Fehlermeldung "Keine Renndaten gefunden"

**Named Range Prefix-Konvention:**
- `_EXP_` = Export (Excel → JSON, App liest)
- `_IMP_` = Import (App → JSON, Excel liest)

**Dateikonvention:**
- `IMPORT.json` – Event, Starter, Rennen (VBA schreibt)
- `IMPORT.json` – Ergebnisse, Renn-Log (App schreibt)
- `race_state.json` – Crash-Recovery (persistent)
- `blackbox.log` – append-only Beweisprotokoll

**Startlogik (Crash-Recovery):**
1. race_state.json vorhanden → SOFORT weiter (keine Nachfrage!)
2. IMPORT.json vorhanden → daraus laden
3. Excel vorhanden → VBA-Makro aufrufen → IMPORT.json erzeugen → laden
4. Nichts davon → Fehlermeldung

### Event-Types für _IMP_LOG (finalisiert)
Alle UPPERCASE:

| Event | Daten-Format |
|-------|-------------|
| `STARTRACE` | `Race={Nr}` |
| `STARTLINE` | `Race={Nr};Line={Nr}` |
| `ROUND` | `Race={Nr};Boat={Nr}` |
| `FINISH` | `Race={Nr};Boat={Nr}` |
| `CORRECTION` | `AddRound;1;Race={Nr};Boat={Nr}` |
| `INVALID` | `Race={Nr};Boat={Nr}` |
| `PAUSE` | `Race={Nr}` |
| `RESUME` | `Race={Nr}` |

### Neue Dateien
| Datei | Änderung |
|---|---|
| `Manual.md` | **Neu** – Für Menschen verständliche Systembeschreibung (Architektur, Dateikonvention, Event-Types, Startlogik) |
| `Excel/IMPORT.json` | **Neu** – Test-JSON vom VBA-Makro (Info, Races, Starter) |

### Config-Ergänzung
| Datei | Änderung |
|---|---|
| `python/config/app_settings.json` | `startreihe_offset_s: 15` ergänzt |
| `python/config/app_config.py` | `AppSettings.startreihe_offset_s: int = 15` |

### GUI/CLI-Anbindung
| Datei | Änderung |
|---|---|
| `python/gui/main_window.py` | AppController akzeptiert `excel_path` + `json_path`; vollständige Lade-Kette in `_load_data()` mit Auto-Suche (IMPORT.json → *.xlsm → *.xlsx im EXE-Ordner); Crash-Recovery; Fehlerdialog statt Crash |
| `python/main.py` | `--excel` + `--json` CLI-Argumente |
| `scripts/preview_gui.py` | `--excel` + `--json` CLI-Argumente; Fehlerdialog |

### Stand
| Komponente | Status |
|---|---|
| Datenmodell (Named Ranges) | ✅ |
| ExcelReader V2 | ✅ (13 Tests) |
| GUI + RaceEngine + Blackbox | ✅ (155 Tests) |
| JSON-Architektur | ✅ JsonRaceStore (12 Tests) |
| Crash-Recovery | ✅ RaceStateManager (12 Tests), AppController-Integration |
| Lade-Kette | ✅ race_state.json → JSON → Excel → Fehler |
| `--json` CLI-Argument | ✅ main.py + preview_gui.py |
| VBA-Makros | ⏳ Kunde |

### Offene Schritte
1. `JsonRaceStore` bauen (liest IMPORT.json, schreibt IMPORT.json)
2. Crash-Recovery in AppController
3. Demo-Daten entfernen (Fehlermeldung stattdessen)
4. VBA-Makros vom Kunden
5. Release v0.2.0 nach Fertigstellung

---

## 2026-08-15 – Meilenstein: Export-Button + PyInstaller-Build (MVP komplett)

### Export-Button in der GUI (Pflichtenheft §7 „Excel-Log")
- `HotkeyPanel`: Bereich „Ergebnis-Export" mit Button + Status-Label (grün/rot/neutral)
- `AppController.on_export_results()`: baut `RaceResultExport` (Event + RaceConfig + Platzierung) und schreibt `Ergebnis_Rennen{N}_<Zeitstempel>.xlsx` in den Exportordner (Entwicklung: Projekt-Root; .exe: Ordner der .exe). Immer neue Datei – Rohdaten (Eingabe-Excel, Blackbox) bleiben unangetastet.
- Fehlerpfad (z. B. Datei in Excel geöffnet): Log-Feed + rotes Status-Label, kein Absturz

### PyInstaller-Build (AGENTS.md §11)
- `scripts/build_exe.py` → `dist/Wasserski-Zeitnehmung.exe` (14,1 MB, `--onefile --noconsole`)
- **`--hidden-import keyboard` ist ZWINGEND**: `input_handler.py` importiert `keyboard` erst zur Laufzeit (lazy) → ohne Hinweis fehlt die Library im Bundle
- `--collect-all customtkinter` bündelt die Theme-Assets
- Bundle-fähige Settings: `resolve_settings_path()` legt `app_settings.json` beim ersten Start NEBEN die .exe (editierbar; Quelle: `--add-data` in `sys._MEIPASS/config/`)
- Smoke-Test: `.exe 5` → Start, Auto-Close, Exit-Code 0, Logs neben der .exe ✅

### 🐛 Zwei Build-Bugs gefunden und behoben
1. **Stdlib-Konflikt `logging`:** Das Paket `python/logging/` wurde beim Start aus `python\main.py` (Skript-Verzeichnis `python/` liegt im sys.path) und im Bundle als stdlib-`logging` aufgelöst → `AttributeError: module 'logging' has no attribute 'getLogger'`. **Fix: Paket umbenannt in `python/logger/`** (alle Imports + AGENTS.md-Struktur). Historische Log-Einträge (ACTIVE_CHANGES/PROJECT_LOG) bleiben unverändert – sie dokumentieren den Stand zum Zeitpunkt X.
2. **`sys.stderr=None` bei `--noconsole`:** loguru-Konsolen-Sink crashte die .exe („Unhandled exception in script") schon vor der Logdatei-Anlage. **Fix:** `setup_logging` überspringt den Konsolen-Sink, wenn `sys.stderr is None`. Zusätzlich FATAL-Handler in `main.py`: unbehandelte Exceptions landen in `gui_startup.log`.

### Tk-Stabilität in Tests (Flaky-Beseitigung)
- Mehrere Tk-Fenster pro Prozess (je Modul) führten sporadisch zu `TclError` → **ein Session-weites Fenster** in `tests/conftest.py` (`tk_window`-Fixture, scope="session"); alle GUI-Module teilen es. 2 Läufe × 146/146 grün.

### Stand
| Komponente | Status |
|---|---|
| Rennlogik + GUI + Blackbox + Hotkeys | ✅ (vorherige Sessions) |
| Excel-Export (Writer + Button) | ✅ |
| PyInstaller-Build (.exe) | ✅ `dist/Wasserski-Zeitnehmung.exe` |
| Tests | ✅ **146/146** |
| Version | 0.1.0 (unverändert, kein Release) |

### Offen / nächste Schritte
- Echte Kunden-Excel einlesen (StartLine-Offsets §3.3, wenn die finale Datei da ist)
- Release-Prozess nach AGENTS.md §5, sobald die Kunden-Excel verifiziert ist
- ggf. Admin-Start der .exe testen (systemweite Hotkeys, AGENTS.md §10)

---

## 2026-08-13 – Objektplan freigegeben & Modelle mit Demo-Daten befüllt

### Offene Fragen Q1–Q8 geklärt (Kunde)
| # | Frage | Entscheidung |
|---|---|---|
| Q1 | Sperrzeit konfigurieren? | **App-Parameter** → `app_settings.json` (JSON, nicht .env/XML) |
| Q2 | ZIEL-Event? | **Automatisch** – letzte Passage nach Renndauer = Ziel (kein Hotkey) |
| Q3 | Strafanzeige? | **Entfällt** |
| Q4 | Reset-Button? | **Nächstes Rennen laden** |
| Q5 | Rennen-Auswahl? | **Ja** – Dropdown über alle RaceConfigs |
| Q6 | Manuell −1? | Offen (Vorschlag: nur +1 im MVP) |
| Q7 | Mehrere Boote je Klasse? | **Ja** |
| Q8 | Start automatisch nach Countdown? | Offen (Vorschlag: Button RENNSTART) |

### Erledigt (Basis für GUI – unabhängig von Excel-Blockade)
- [x] `_BOTBRAIN/object_model_plan.md` aktualisiert (Q1–Q8, AppSettings-Kapitel 4.11)
- [x] `python/core/models.py` – **NEU**: EventType/RacePhase-Enums, Event, Starter, StartLine, RaceConfig, RaceEvent (frozen), Lap, BoatState (Properties: laps_count, total_time, last_lap, best_lap), BoatResult, RaceClass – englische Bezeichner, deutsche Docstrings
- [x] `python/config/app_config.py` – **NEU**: AppConfig (Konstanten/Farben) + AppSettings + ConfigManager (JSON load/save, kaputte JSON → Warnung + Defaults)
- [x] `python/config/app_settings.json` – **NEU**: App-Parameter (lockout_seconds=2.0)
- [x] `python/core/demo_data.py` – **NEU**: fiktive, realistische Daten (ÖM Ybbs 2026, 3 Rennen, 9 Starter A–I, Rennen 2 U18 Open mit 8/7/6 Runden, Ereignisliste inkl. INVALID-Sperrzeit-Demo, deterministisch/reproduzierbar)
- [x] `tests/test_models_demo.py` – **NEU**: 11 Tests (Modelle, Demo-Daten, ConfigManager)
- [x] **Alle 42 Tests grün** (31 alt + 11 neu)

### Hinweis
- Excel-Reader (`excel_reader.py`) bleibt unangetastet (Blockade). Seine Dataclasses (`RaceData`, `RaceConfig`, `Starter`) sind Alt-Logik; das neue Modell in `models.py` ist maßgeblich. Refactoring beim Einlesen der neuen Excel-Datei.
- Nächster Schritt: **GUI-Grundgerüst** (`python/gui/main_window.py`) gegen die Demo-Daten bauen.

---

## 2026-08-13 – Objektplan erstellt (UI-Start vorbereitet)

### Hintergrund
- Kunde wartet noch auf finale Excel-Liste → Excel-Reader-Blockade bleibt
- Fachliche Objektstruktur ist aus Pflichtenheft + GUI-Description + bestehendem Excel-Reader ableitbar
- Entscheidung: **UI/GUI-Entwicklung kann unabhängig von der Excel-Datei starten** (Domänenmodell vom Excel-Format entkoppelt)

### Erledigt
- [x] `_BOTBRAIN/object_model_plan.md` erstellt – vollständiger Objektplan:
  - Domänenmodelle (`models.py`): Starter, RaceConfig, RaceEvent, Lap, BoatState, BoatResult, RaceClass, StartLine, Enums EventType/RacePhase
  - Kern (`core/`): RaceEngine (Zustandsmaschine), LockoutManager (Sperrzeit), ResultCalculator, ClassFinishTracker (klassenweise Rennende-Logik)
  - Threading (ADR-007): InputHandler (Keyboard-Thread) → Queue → AppController (Main-Thread)
  - Persistenz: ExcelRaceReader (existiert), ExcelResultWriter + BlackboxWriter (NEU), HotkeyMapping (ADR-008)
  - GUI: 10 Klassen (MainWindow + 9 Panels/Controller) nach 05_a_GUI_Description
  - 8 offene fachliche Fragen (Q1–Q8) zur Klärung mit Kunde

### WICHTIG – Konvention angepasst (Kundenwunsch)
- Kunde wünscht: **Code auf Englisch, Kommentare reichlich auf Deutsch**
- AGENTS.md sagt bisher „Code-Kommentare in Englisch“ → Widerspruch, bei nächster Freigabe in AGENTS.md anpassen

### Nächste Schritte (nach Freigabe des Objektplans)
1. Offene Fragen Q1–Q8 mit Kunde klären (Sperrzeit-Config, ZIEL-Event, Strafanzeige, Reset-Logik, Rennen-Auswahl, −1-Korrektur)
2. `python/core/models.py` anlegen (Basis für alles)
3. GUI-Grundgerüst (`python/gui/main_window.py`) – kann parallel zum Excel-Warten gebaut werden
4. Rennlogik danach (oder parallel): RaceEngine, LockoutManager, ResultCalculator

---

## 2026-08-12 – Projekt-Initialisierung

### AGENTS.md neu geschrieben
- Alte AGENTS.md war vom Gastro-Tischreservierungs-Projekt (Laravel/PHP/Web)
- Komplett neu geschrieben für Waterski-Racing (Python/CustomTkinter/Desktop)
- Universelle Regeln beibehalten (Ewiges Protokoll, Secrets, BotBrain, Active Changes, Änderungsliste, Bildanalyse)
- Waterski-spezifische Regeln hinzugefügt (Python-Konventionen, Excel-Vorsicht, keyboard-Admin-Rechte, PyInstaller-Build)
- Architektur-Entscheidungen aus Pflichtenheft + architecture_and_roadmap/ übernommen

### Projektstand
- Pflichtenheft V1 (17.06.2026) – vollständig, verbindlich
- ProjectDesckription.md – Kundenversion
- Architecture.md – Einstiegsdokument
- 9 Architektur-Detaildokumente in `architecture_and_roadmap/`
- Prototyp-Code: `python/logging_util.py` + `scripts/test_logging.py`
- Referenz-Implementierung: `Excel/Test_StopUhr_V1.xlsm` (VBA)
- Kein Git-Repo initialisiert
- Keine virtuelle Umgebung eingerichtet
- Keine requirements.txt vorhanden

### Offene Punkte vor Entwicklungsstart
- [ ] Dev-Umgebung prüfen (Python 3.11+, .venv)
- [ ] requirements.txt erstellen
- [ ] Git-Repo initialisieren
- [ ] .gitignore erstellen
- [ ] Architektur-Entscheidungen reviewen (nächster Schritt)

---

## Architektur-Entscheidungen (ADR)

### ADR-001: Python + CustomTkinter statt Excel-VBA
**Datum:** 17.06.2026 (aus Pflichtenheft/Architecture.md)
**Status:** Akzeptiert
**Begründung:**
- Systemweite Hotkey-Erfassung (keyboard-Library) unabhängig vom Fensterfokus
- Kein 32/64-Bit-Konflikt mit Excel-Installationen
- Auslieferung als Single .exe (keine Python-Installation beim Kunden)
- Bessere KI-Unterstützung als VBA

### ADR-002: Excel für Datenhaltung, Python für Logik
**Datum:** 17.06.2026
**Status:** Akzeptiert
**Begründung:**
- Kunde pflegt Stammdaten in gewohnter Excel-Umgebung
- Trennung von Konfiguration und Laufzeitsystem
- openpyxl liest/schreibt .xlsx ohne Excel-Instanz

### ADR-003: Offline-First
**Datum:** 17.06.2026
**Status:** Akzeptiert
**Begründung:**
- Rennveranstaltungen oft ohne stabile Internetverbindung
- Keine Abhängigkeit von externen Diensten

### ADR-004: Blackbox-Log (TXT) + Excel-Ergebnis
**Datum:** 17.06.2026
**Status:** Akzeptiert
**Begründung:**
- TXT = unveränderliches Beweismittel (append-only)
- Excel = strukturierte Auswertung
- Klare Trennung Rohdaten ↔ Ergebnisse

### ADR-005: Zustandsmaschine für Rennphasen
**Datum:** 17.06.2026
**Status:** Akzeptiert
**Begründung:**
- Klare, testbare Transitionen: Vorstart → Aktiv → Rennende → Reset
- Verhindert inkonsistente Zustände

### ADR-006: Loguru für Logging
**Datum:** 17.06.2026 (aus 02_tech_stack.txt)
**Status:** Akzeptiert
**Begründung:**
- Einfachere Konfiguration als stdlib logging
- Automatische Rotation
- Farbige Konsolenausgabe für Entwicklung

### ADR-007: Threading-Modell (Keyboard + GUI)
**Datum:** 12.08.2026
**Status:** Akzeptiert
**Begründung:**
- `keyboard`-Listener läuft blockierend (`keyboard.wait()` / `keyboard.on_press_key()`)
- CustomTkinter benötigt den Main-Thread für die GUI-Event-Loop
- Entkopplung via `queue.Queue`: Keyboard-Thread schreibt Events, GUI-Thread pollt via `after()`
- Kein direktes GUI-Update aus Hintergrund-Threads (Tkinter ist nicht thread-safe)
- Logging (Blackbox/Excel) erfolgt im Keyboard-Thread (append-only, keine GUI-Abhängigkeit)

### ADR-008: Hotkey-Mapping (Buchstaben A–Z primär)
**Datum:** 12.08.2026
**Status:** Akzeptiert
**Begründung:**
- Pflichtenheft §3.2 definiert Boot-Key = A–Z (Buchstaben)
- GUI-Design zeigt zusätzlich Zahlenblock – dieser wird optional unterstützt
- Primäres Mapping: Buchstaben A–Z, geladen aus Excel `Starter!Boot-Key`
- Zahlenblock 1–0 als sekundäres Alias-Mapping (für Num-Pad-Bediener)

---

## 2026-08-12 – Setup abgeschlossen

### Erledigt
- [x] Git-Repo initialisiert
- [x] .gitignore erstellt (.venv/, *.xlsx, *.xlsm, dist/, build/, __pycache__/, *.log)
- [x] requirements.txt erstellt (customtkinter, openpyxl, keyboard, pyinstaller, loguru, pytest)
- [x] Ordnerstruktur angelegt: python/core/, gui/, excel/, logging/, config/ + tests/
- [x] __init__.py in allen Packages
- [x] python/config/version.py + VERSION-Datei (0.1.0)
- [x] 01_system_setup.txt korrigiert (src/ → python/)
- [x] ADR-007 (Threading) + ADR-008 (Hotkey-Mapping) dokumentiert

### Nächste Schritte
- [x] Dev-Umgebung prüfen: Python 3.11+, .venv, pip install -r requirements.txt
- [x] logging_util.py nach python/logging/ verschieben und auf loguru umstellen
- [x] test_logging.py nach tests/ verschieben
- [x] Excel-Reader-Modul (python/excel/) – Renndaten, Starter, Konfiguration einlesen
- [x] GUI-Screenshot analysiert (Gemini-Bild → bestätigt GUI-Design aus 05_a_GUI_Description.txt)
- [ ] Rennlogik (python/core/) – Zustandsmaschine, Sperrzeit, Rundenberechnung
- [ ] GUI-Grundgerüst (python/gui/) – CustomTkinter Hauptfenster

---

## 2026-08-12 – Excel-Reader-Modul fertiggestellt

### python/excel/excel_reader.py
- Liest 3 Sheets: Renndaten, Starter, Rennkonfiguration
- Fuzzy Column Matching: Header-Erkennung über normalisierte Namen (case-insensitive, Umlaut-toleranz)
- Dataclass-basierte Datenmodelle: RaceData, Starter, RaceConfig, RaceExcelData
- Vollständige Validierung (fehlende Felder, doppelte Boot-Keys, ungültige Keys A–Z, Klassen-Mapping-Check)
- 30+ Aliase für Spaltennamen (Deutsch/Englisch gemischt)
- 23 Tests, alle grün (31/31 gesamt mit logging-Tests)

### GUI-Screenshot-Analyse
- Bild via AnalyzeImage.ps1 (Gemini 2.5 Flash) analysiert
- Bestätigt exakt das GUI-Layout aus 05_a_GUI_Description.txt:
  4 Hauptbereiche (Header, Dashboard, Main mit Tabelle+Hotkeys, Footer)
  Dark Theme, Farbcodierung (Grün=aktiv, Rot=Warnung, Gelb=wartend, Blau=Fortschritt)
  Sperrzeit-Anzeige direkt in der Tabellenzelle

---

## 2026-08-12 – SESSION-ENDE: Stand & nächste Session

### ⚠️ WICHTIG: Auf neue Excel-Version warten!
Der Kunde hat eine **neuere Version der Excel-Konfigurationsdatei** zugesichert.
**Vor dem Weiterbau an Rennlogik/GUI MUSS diese neue Excel-Datei analysiert werden,**
da sich Spaltennamen, Sheet-Struktur oder Datenfelder ändern könnten.
→ Excel-Reader ist bewusst flexibel gebaut (Fuzzy Matching, 30+ Aliase), aber Anpassungen wahrscheinlich.

### Aktueller Stand (Session 1)
| Komponente | Status | Tests |
|---|---|---|
| Dev-Umgebung | ✅ Python 3.14, .venv, alle 6 Pakete | — |
| Git | ✅ Initialisiert (noch kein Commit) | — |
| Projekt-Struktur | ✅ 5 Packages + tests/ | — |
| Logging (`python/logging/`) | ✅ logging_util.py (Bug-fixes done) | 4/4 ✓ |
| Excel-Reader (`python/excel/`) | ✅ Renndaten, Starter, Konfiguration + Validierung | 23/23 ✓ |
| GUI-Analyse | ✅ Screenshot bestätigt 05_a_GUI_Description.txt | — |
| Rennlogik (`python/core/`) | ⏸️ BLOCKIERT – wartet auf neue Excel-Version | — |
| GUI (`python/gui/`) | ⏸️ BLOCKIERT – wartet auf neue Excel-Version | — |

### Für die nächste Session
1. **PROJECT_LOG.md lesen** (dieses File – Source of Truth)
2. **Neue Excel-Datei vom Kunden einlesen:**
   - `python -c "from python.excel.excel_reader import read_race_excel; print(read_race_excel('NEUE_DATEI.xlsx'))"`
   - Sheets & Spalten mit Pflichtenheft abgleichen
   - `excel_reader.py` ggf. anpassen + Tests ergänzen
3. **Dann: Rennlogik** (`python/core/race_engine.py`) – Zustandsmaschine, Sperrzeit, Rundenberechnung
4. **Danach: GUI-Grundgerüst** (`python/gui/main_window.py`) – CustomTkinter

### Bekannte technische Details
- Python 3.14.0 (nicht upgraden auf 3.14.7 – kein Mehrwert)
- PyInstaller 6.22.0 (angepasst für 3.14, statt urspr. 6.2.0)
- `keyboard`-Library braucht Admin-Rechte für systemweite Hotkeys
- `.venv/` im Root, aktivieren: `.venv\Scripts\activate`
- Tests: `python -m pytest tests\ -v`

---

## 2026-08-14 – GUI-Bug „schwarzes Fenster" behoben + Logging-Infrastruktur

### 🐛 Problem (vom Nutzer gemeldet)
Das GUI-Startskript zeigte nur ein schwarzes Fenster ohne Widgets; beim Schließen
flackerten kurz dunkle Texte. Verdacht: GUI wird nie gerendert.

### 🔍 Diagnose (Logging-basiert, ohne Raten)
1. **`python/logging/app_logger.py`** (neu): zentrale loguru-Logging-Klasse
   (Konsole + TXT-Datei, `log_progress` für Start-Schritte)
2. **`scripts/preview_gui.py`**: 5-Schritt-Start-Logging (`gui_startup.log`)
3. **`python/gui/main_window.py`**: Schritt-Logging je Panel + `report_callback_exception`
   (fängt verschluckte Tk-Fehler ins Log)
4. **`scripts/diagnose_gui.py`** (neu): Isolationstest in 3 Stufen
   - T1 nacktes tkinter → ✅ sauber
   - T2 nacktes CustomTkinter → ✅ sauber (aber Fenster `state=withdrawn`)
   - T3 unser MainWindow → ❌ `TclError: can't invoke "wm" command: application has been destroyed`

### 🎯 Ursache
CustomTkinter `windows/ctk_tk.py` `_windows_set_titlebar_color()`:
- Zeile 282: `!= "iconic" or != "withdrawn"` → **Tautologie** (logischer Fehler)
- Zeile 316: `if self._window_exists or True:` → immer wahr
→ Fenster blieb `withdrawn` (unsichtbar), mainloop crashte. Reproduziert mit
CustomTkinter 5.2.1 **und** 6.0.0 auf Python 3.14 + Tk 8.6.

### ✅ Fix
`python/gui/main_window.py`:
```python
ctk.CTk._deactivate_windows_window_header_manipulation = True
```
Offizieller Schalter deaktiviert die buggy Titelbar-Manipulation komplett.
`requirements.txt`: customtkinter 5.2.1 → 6.0.0.

### ✅ Verifikation
- `mainloop` läuft durch, Fenster normal sichtbar (kein TclError)
- Screenshot `_BOTBRAIN/gui_fixed.png` (1456×939) via `capture_window.py --activate`
  + KI-Analyse (`_BOTBRAIN/gui_fixed.txt`): **alle Bereiche gerendert**
  (Header, Renninfo, Countdown 00:00:20/30:00, RENNSTART/NEUSTART, Hotkey-Block A–G,
  Log-Feed mit Live-Einträgen, Rennende-Status, +1-Runde, Footer)
- Tests: **46/46 grün**

### 📌 Notiz / Folge
- `RaceEndStatusPanel` zeigt noch „Keine Klassen geladen" → kommt mit der RaceEngine
- Offene Objektplan-Fragen Q6 (−1-Runde) und Q8 (Start-Auslösung) weiter offen

---

## 2026-08-14 – Q6/Q8 entschieden: Countdown startet das Rennen automatisch

### Entscheidungen (Kunde)
| Frage | Entscheidung |
|---|---|
| **Q6** Manuell −1 Korrektur | **Nur +1 im MVP** – keine −1-Funktion |
| **Q8** Rennstart automatisch nach Countdown? | **Ja, automatisch** – kein eigenes Startsignal. Countdown unterbrechbar (PAUSE/WEITER) und neu startbar (NEUSTART) |

### Umsetzung
- `CountdownPanel`: RENNSTART-Button (rot) entfernt → **PAUSE/WEITER** (gelb) + **NEUSTART** (grün); neue API `set_callbacks`, `set_pause_mode`, `set_pause_enabled`
- `AppController`: `PHASE_COUNTDOWN` entfernt – der Countdown läuft direkt in `PHASE_PRESTART` und startet bei 0 automatisch `PHASE_ACTIVE`; Pause friert die Restzeit ein (`_countdown_paused`), WEITER verschiebt die Zeitbasis so, dass die Restzeit exakt weiterläuft; NEUSTART = Countdown von vorn (im Rennen: zurück zum Vorstart, Q4)
- Buttons sind über `set_callbacks` verdrahtet (Controller setzt sie nach dem Panel-Bau – Entkopplung)

### Verifikation
- 4 neue Tests (auto_start, pause/resume, pause blockiert Start, reset) → **50/50 Tests grün**
- Screenshot `_BOTBRAIN/gui_q8.png` + KI-Analyse: VORSTART 00:00:19 (rot, läuft), VERBLEIBENDE ZEIT 30:00, gelber PAUSE-Button, grüner NEUSTART-Button ✓

---

## 2026-08-14 – RaceEngine (Kernlogik) gebaut + GUI-Anbindung

### Meilenstein: Erste komplette Kernlogik nach TDD (33 neue Tests)

**Neue Module (`python/core/`):**
| Modul | Verantwortung |
|---|---|
| `lockout_manager.py` | Sperrzeit je Boot (§5.2): `is_allowed`/`register`/`remaining`/`reset` (normalisiert UPPER) |
| `result_calculator.py` | Runden verbuchen + Wertung: `add_lap(state, end_time, race_start)` (erste Runde ab Rennstart), `compute_results` (Runden absteigend, Gesamtzeit aufsteigend, Platz 0 = ohne Runde) |
| `class_finish_tracker.py` | Klassenweise Rennende-Logik (§5.3): WAITING → TRIGGERED → CLOSED; `on_passage` triggert `finish_mode` für alle Boote der Klasse |
| `race_engine.py` | **RaceEngine**: Phasen PRESTART → ACTIVE → FINISHING → FINISHED; Countdown mit Pause/Weiter (Q8); `handle_key_press` (Sperrzeit → Runde → FINISHING-Logik, Q2 automatischer Zieleinlauf); `handle_manual_correction` nur +1 (Q6); `tick`; `reset`; `get_placements`; `get_class_finish_status` |

**Design-Entscheidungen:**
- Zeitquelle wird als `now`-Parameter injiziert → deterministisch testbar ohne Zeit-Mocking
- `ClassFinishTracker`-API weicht geringfügig vom Objektplan ab (hält Referenzen auf classes/boats, `on_passage(klasse)`/`close_class(klasse)`)
- `ResultCalculator.add_lap` braucht zusätzlich `race_start` für die erste Runde
- TODO dokumentiert: StartLine-Offsets (§3.3) erst mit der finalen Kunden-Excel

**Tests:** `test_lockout_manager.py` (6), `test_result_calculator.py` (6),
`test_class_finish_tracker.py` (5), `test_race_engine.py` (16) → **33/33 grün**

### GUI-Anbindung (AppController → RaceEngine)
- `AppController` nutzt jetzt eine echte `RaceEngine` statt der Demo-Phasen-Simulation:
  - `_load_race` → `engine.load_race(...)` (nur Starter der Renn-Klassen), Panels befüllt
  - Tick (50 ms) → `engine.tick(now)` + Countdown-/Rennzeit-Anzeige, Lockout-Aufräumen,
    `engine.get_placements()` (schreibt Plätze zurück), `update_boats`, `update_states`
  - `on_key_press` → `engine.handle_key_press` (Eingaben außerhalb ACTIVE/FINISHING werden nur protokolliert)
  - `on_manual_correction` → `engine.handle_manual_correction(boot_key, 1, now)` (Q6)
  - PAUSE/WEITER + NEUSTART → `engine.pause/resume_countdown()` bzw. `engine.reset()`
  - Engine-Events (PASSAGE/FINISH/INVALID/CORRECTION_PLUS/START) werden in den Log-Feed gespiegelt
- `RaceEndStatusPanel`: neues schlankes `update_states()` (Tick-Update ohne Widget-Neubau);
  `HotkeyPanel.set_on_key()` und `ManualCorrectionPanel.set_on_correct()` als Setter ergänzt
- `race_engine.py`: setzt nach gültiger Passage `state.lockout_until` (Anzeige-Feld für die SPERRZEIT-Zelle)

### Verifikation
- GUI-Smoke-Tests auf RaceEngine umgestellt; **Tk-Stabilität:** nur EIN Fenster pro Testlauf
  (Modul-Fixture) – mehrfaches `Tk()`/`destroy()` im selben Prozess crasht unter Windows
  mit „Can't find a usable tk.tcl" (Tk 8.6/Python 3.14)
- **Gesamt: 83/83 Tests grün** (~11 s; vorher 46 s wegen vieler Tk-Instanzen)
- Screenshot `_BOTBRAIN/gui_engine.png`: Countdown VORSTART läuft (rot), PAUSE (gelb),
  NEUSTART (grün), Hotkeys grün markiert, Live-Tabelle gefüllt – **Pixel-Analyse** bestätigt
  alle UI-Farben deterministisch (KI-Bildanalyse hatte die dunklen Tabellenzeilen fälschlich
  als „leer" beschrieben → Farbzählung widerlegt)

### Offen / Nächste Schritte
- `python/logging/blackbox.py` (append-only TXT, Beweisfunktion) + echte Hotkey-Erfassung (keyboard)
- StartLine-Offsets mit neuer Kunden-Excel (§3.3)
- AGENTS.md: Kommentare Deutsch vs. Englisch (Kundenwunsch, wartet auf Freigabe)

---

## 2026-08-14 – Blackbox (Beweis-Log) + systemweite Hotkey-Erfassung

### Ziel
Der digitale Ersatz für den unverfälschbaren **Zeilendrucker** (Pflichtenheft §7):
Jeder Tastendruck und jedes Verarbeitungsergebnis wird **sofort, append-only**
und thread-sicher in eine TXT-Blackbox geschrieben. Dazu echte systemweite
Hotkeys (keyboard-Library) statt nur der virtuellen GUI-Tastatur.

### Bestandsaufnahme Logging
- Fehler-/Verlaufs-Logging existiert bereits: `python/logging/app_logger.py`
  (loguru → Konsole + `gui_startup.log`, `report_callback_exception` für Tk-Fehler)
- Spezifikation `05_gui_design.txt` sieht zusätzlich rotierende `error.log`/
  `current.log` vor → späterer Feinschliff, keine eigene Baustelle heute
- **Es fehlte genau der Beweis-Teil:** die Blackbox für Tastendrücke → gebaut

### Neue Module
| Modul | Verantwortung |
|---|---|
| `python/logging/blackbox.py` | **BlackboxWriter**: append-only (`"a"`-Modus, vorhandene Datei wird NIE geleert), `flush()` nach jedem Eintrag (Daten liegen bei Absturz/Stromausfall auf der Platte), `threading.Lock` (Keyboard-Thread + GUI-Thread), Rotation bei 10 MB (03_data_flow.txt) mit Zeitstempel-Suffix, `replay()` für Renn-Rekonstruktion (04_race_logic.txt), `write_key_event` im Objektplan-Format, `format_timestamp` (Mikro→ms) |
| `python/core/input_handler.py` | **HotkeyMapping**: Boot-Key → `"a".."z"` (ADR-008) + Zahlenblock-Alias `1..0` für die ersten zehn Starter (keyboard-Name `"num 1"`..); **InputHandler**: `keyboard.on_press`, bei jedem Druck **sofortiger Blackbox-Rohdruck** `TASTE: '<taste>'` (ohne EVENT/STATUS – die Verarbeitung kennt das Ergebnis noch nicht), dann `input_queue.put(boot_key)`; `update_mapping` für Renn-Wechsel; `stop()` unhookt |

### Integration (AppController)
- `AppController(..., blackbox_path=..., enable_keyboard=False)`: Blackbox wird
  beim Start geöffnet, `_show_event` schreibt das **Verarbeitungsergebnis**
  (`EVENT: START/PASSAGE/FINISH/CORRECTION_PLUS/INVALID STATUS: VALID/INVALID`)
- `_process_boot_key`: gemeinsamer Pfad für GUI-Klick **und** System-Hotkey
  (Phase-Check, Engine-Aufruf, Blackbox-Eintrag)
- Tick (after-Polling, ADR-007): drainnt die `input_queue` → Hotkeys werden im
  GUI-Thread verarbeitet (kein Threading-Chaos mit Tk)
- `run_app()`: startet mit `blackbox_path="blackbox.log"`; systemweite Hotkeys
  bleiben bewusst **deaktiviert** (benötigen Windows-Admin, AGENTS.md §10) →
  Aktivierung später per Konfiguration
- `_load_race`: ruft `update_mapping(...)` bei Renn-Wechsel (aktive Starter)

### Design-Entscheidungen
- **Append-only + sofortiges flush()** statt Pufferung: Beweisfunktion übersteht
  Absturz/Stromausfall (03_data_flow.txt: "sofort in die Blackbox schreiben")
- **Rohdruck vor Verarbeitung:** Der Keyboard-Thread schreibt die tatsächlich
  gedrückte Taste (z. B. `'num 2'`) unmittelbar; die Interpretation folgt später
  aus dem GUI-Thread – die Beweiskette ist lückenlos
- Blackbox-Zeilen sind append-only; `replay()` flusht vor dem Lesen
  (Wiederherstellung nach Absturz)
- Rotation bei 10 MB: volle Datei → `blackbox_YYYYMMDD_HHMMSS.log`, neue beginnt
- `_rotate_locked` ist auch aus `__init__` aufrufbar (vor dem Öffnen der Datei –
  Bug beim ersten Rotations-Test gefunden und behoben)

### Verifikation
- **18 neue Tests**: `test_blackbox.py` (12, inkl. 20-Thread-Parallelität mit
  200 Einträgen verlustfrei), `test_input_handler.py` (9, FakeKeyEvent ohne
  echte Hardware), GUI-Smoke +2 Integrationstests (Blackbox-Einträge,
  Queue-Drain)
- **Gesamt: 110/110 Tests grün** (~12 s)
- Smoke-Test der App mit `blackbox_path`: `blackbox.log` enthält
  `[2026-08-14 08:33:32,108] TASTE: 'A' EVENT: PASSAGE STATUS: VALID` und
  `[2026-08-14 08:33:32,0xx] EVENT: START STATUS: VALID`

### Offen / Nächste Schritte
- `ExcelResultWriter` (Excel-Ergebnisausgabe, letzter MVP-Baustein)
- StartLine-Offsets mit neuer Kunden-Excel (§3.3)
- PyInstaller-Build (`--onefile --noconsole`, Admin-Hinweis keyboard)

---

## 2026-09-03 – Hotkey-Zeile entfernt + Leerzeile eliminiert + Hotkeys beendeter Klassen inaktiv

### Ziel
Drei Kundenanforderungen (2026-09-03) zur Platzersparnis und Bedienlogik:
1. **"Aktiv: ..."-Hotkey-Zeile entfernen** (Platz sparen) – der Admin-Status in
   der Überschrift bleibt unverändert.
2. **Leerzeile unter "Rennende-Status" eliminieren** – das Info-Label wird nur
   noch bei leerer Klassenliste gepackt.
3. **Hotkeys einer beendeten Klasse inaktiv machen** – CLOSED/FERTIG → Boot-Keys
   grau/inaktiv, auch wenn gestartet.

### Änderungen
| Datei | Änderung |
|---|---|
| `python/gui/panels.py` | **HotkeyPanel:** `_info`-Label entfernt (1); neues Feld `_finished_keys` + `set_finished_keys()` (3); `_refresh_buttons()` berücksichtigt `_finished_keys`; `set_starters()` setzt `_finished_keys` zurück. **RaceEndStatusPanel:** `update_classes()` packt `_info` nur bei leerer Klassenliste (2) |
| `python/gui/main_window.py` | `_tick()`: Boot-Keys der CLOSED-Klassen aus `get_class_finish_status()` + `starter.klasse` → `hotkeys.set_finished_keys()` (3) |
| `tests/test_gui_smoke.py` | `test_hotkey_status_and_started_keys` erweitert (set_finished_keys); **+1 Test** `test_race_end_status_no_empty_line_when_classes_loaded`; `app`-Fixture + 3 Export-Tests rufen `stop_tick()` auf (verhindert Datei-Lock auf `race_state.json`) |
| `tests/conftest.py` | `_clean_race_state`-Fixture: Löschen von `race_state.json` mit Retry (5×, 50 ms) gegen PermissionError durch weiterlaufenden after()-Tick |

### Verifikation
- **190/190 Tests grün** (6× stabil, ~8s).

### Hinweis (Test-Isolation)
Das `race_state.json`-Restfile nach dem Testlauf kann bestehen bleiben (der
after()-Tick eines Controllers kann nach dem Teardown noch einmal `save()`
schreiben). Das `_clean_race_state`-Fixture löscht die Datei vor jedem Test
(mit Retry gegen PermissionError), daher ist die Test-Isolation gewährleistet.
`stop_tick()` in den Fixtures + Retry im Fixture reduzieren die Flakiness
deutlich (6× stabil grün).

---

*Legende: ADR = Architecture Decision Record. Neue Entscheidungen hier mit Datum und Begründung dokumentieren.*