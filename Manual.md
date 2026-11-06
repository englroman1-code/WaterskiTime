# Wasserski-Racing Zeitnehmung – Benutzerhandbuch

Dieses Dokument beschreibt das System verständlich für Menschen.
Es wird bei jeder wesentlichen Änderung aktuell gehalten (kein fortlaufendes Protokoll).

---

## 1. Architektur-Überblick

```
                    ┌──────────────┐
  Kunde pflegt →   │  Excel-Datei  │  (renn.xlsx / Test_StopUhr_V1.xlsm)
                    │  NamedRanges │
                    └──────┬───────┘
                           │
                  VBA Makro ruft
                  ExportExpRangesToJSON auf
                           │
                    ┌──────┴───────┐
                    │ IMPORT.json  │  (zentrale Datenquelle)
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │  Python App  │
                    │  RaceEngine  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
          Live-Tabelle  Blackbox    RESULT_*.json
          (GUI)        (blackbox    (Ergebnisse +
                        .log)        Renn-Log)
```

### Datenfluss

1. **Kunde** pflegt Excel (Named Ranges mit `_EXP_`-Prefix)
2. **Python-App** ruft VBA-Makro `ExportExpRangesToJSON` via COM auf
3. **VBA-Makro** erzeugt `IMPORT.json` aus den `_EXP_`-Ranges
4. **Python App** liest `IMPORT.json` via `JsonRaceStore`
5. **Python App** schreibt `RESULT_<Zeitstempel>.json` (Ergebnisse + Renn-Log)
6. **Optional:** VBA-Makro `MainJsonImport` liest die Ergebnis-JSON zurück in
   die Excel-Sheets `results` und `log`

---

## 2. Dateikonvention

| Datei | Inhalt | Wer schreibt |
|-------|--------|--------------|
| `IMPORT.json` | Event, Starter, Rennen (alle `_EXP_`-Ranges) | VBA-Makro (Eingabe) |
| `RESULT_<Zeitstempel>.json` | **ALLE fertigen Rennen** (Platzierungen, Renn-Log), gruppiert nach Rennen und Klasse | Python App (Ausgabe) |

Plus app-interne Dateien (liegen neben der `.exe`; in der Entwicklung im
Projekt-Root):

| Datei | Inhalt | Wann |
|-------|--------|------|
| `race_state.json` | Crash-Recovery-State | Persistent (nur bei Änderungen/Heartbeat) |
| `blackbox.log` | Append-only Beweisprotokoll | Immer (nie löschen) |
| `gui_startup.log` | Start-/Diagnose-Log | Bei jedem Start (überschrieben) |
| `app_settings.json` | Sperrzeit/Hotkey-Einstellung | Beim ersten Start neben die `.exe` kopiert |

---

## 3. Named Ranges – Prefix-Konvention

| Prefix | Bedeutung | Inhalt |
|--------|-----------|--------|
| `_EXP_` | **Export** (Excel → JSON) | Daten, die die App aus Excel liest |
| `_IMP_` | **Import** (App → JSON) | Daten, die die App zurückschreibt |

### Export-Ranges (`_EXP_`)

| Range-Name | Inhalt |
|------------|--------|
| `_EXP_INFO` | Veranstaltung, Datum, Organisator |
| `_EXP_STARTER` | Starter-Liste (Boote, Fahrer, Klasse, Race, Startreihe) |
| `_EXP_RACES` | Rennkonfiguration (Dauer, Rundenlängen, Startintervall, Grid Time) |

### Import-Ranges (`_IMP_`)

| Range-Name | Inhalt |
|------------|--------|
| `_IMP_LOG` | Vollständiges Renn-Log (Zeilendrucker-Stil) |
| `_IMP_RESULTS` | Ergebnisse (Platzierungen, Runden, Zeiten) |

---

## 3a. Rennparameter (Pflichtfelder, Entscheidung 2026-09-02)

Zwei Rennparameter kommen pro Rennen aus der Excel (`_EXP_RACES` → IMPORT.json)
und sind **Pflichtfelder** – fehlt einer, blockiert die Validierung das Rennen
(kein stiller Default, keine hartcodierten Fallbacks):

| Parameter | Bedeutung | Einheit | Quelle |
|-----------|-----------|---------|--------|
| **Startintervall** | Vorlaufzeit bis zum wirklichen Start (Countdown) – kann pro Rennen unterschiedlich sein | Sekunden | `_EXP_RACES` → `StartInterval` |
| **Grid Time** | Zeit zwischen den Startreihen | Sekunden | `_EXP_RACES` → `Grid Time [s]` |

- Beide Werte sind **in Sekunden** angegeben (keine Mischeinheiten).
- Der frühere feste `startreihe_offset_s` aus der App-Config wurde **entfernt** –
  die Zeit zwischen den Startreihen kommt jetzt ausschließlich aus der Excel.
- Fehlende Pflichtfelder → Validierungsfehler im `DataValidator`:
  „Startintervall (Vorlaufzeit) muss > 0 sein" / „Grid Time (Zeit zwischen Startreihen) muss > 0 sein".

---

## 4. Startlogik (Crash-Recovery)

```
App-Start
  │
  ├─ 1. Gibt es race_state.json?
  │     → JA: Sofort weiter! Keine Nachfrage!
  │     → NEIN: weiter mit 2.
  │
  ├─ 2. Wurde --json übergeben?
  │     → JA: IMPORT.json laden
  │     → NEIN: weiter mit 3.
  │
  ├─ 3. Wurde --excel übergeben?
  │     → JA: VBA-Makro aufrufen → IMPORT.json erzeugen → laden
  │     → NEIN: weiter mit 4.
  │
├─ 4. Wurde ein Scenario übergeben? (Tests)
  │     → JA: Testdaten laden (VOR Auto-Suche!)
  │     → NEIN: weiter mit 5.
  │
  ├─ 5. Auto-Suche im Programmordner (*.exe-Ordner oder CWD):
  │     a) IMPORT.json vorhanden? → laden
  │     b) *.xlsm vorhanden? → VBA-Makro aufrufen → IMPORT.json → laden
  │     c) *.xlsx vorhanden? → VBA-Makro aufrufen → IMPORT.json → laden
  │     → Nichts gefunden: Fehlermeldung
  │
  └─ 6. Zurückschreiben: Ähnliche Logik
        ├─ Excel frei → VBA-Makro
        └─ Gesperrt → EXPORT.json erzeugen + Meldung
```

**Wichtig:** Bei Crash-Recovery wird OHNE Nachfrage fortgefahren!
Die Zeit beim Rennen ist kritisch – Nachfragen kosten wertvolle Sekunden.
Der State wird aber nur übernommen, wenn er zur aktuellen Datenquelle passt
(siehe §4f). Ein alter/fremder State wird verworfen und gelöscht.

**VBA-Makro:** Die aktuelle Excel-Vorlage (`Test_StopUhr_V1.xlsm`) enthält
das Export-Makro im Modul **`mdl_Engl_Export`** (`ExpRangesToJSON` bzw.
`ExportExpRangesToJSON`). Der Python-Aufruf ist derzeit noch auf den alten
Modulnamen `mdlEngl` hardcodiert – das ist der offene Punkt 1 (siehe §7).
Bis dahin ist der direkte Excel-Start aus der App nicht freigegeben;
`IMPORT.json` kann in Excel manuell über das Makro erzeugt und neben die
`.exe` gelegt werden.

### 4a. Zeitversetzte Starts (Variante A – Startreihen)

**Kundenentscheidung (2026-09-02):** Jedes Boot startet seine Zeitmessung
erst, wenn seine Startreihe startet (Variante A).

- **Reihe 1** startet bei T=0 (Rennstart)
- **Reihe 2** startet bei T=+Grid Time
- **Reihe 3** startet bei T=+2×Grid Time
- usw.

**Konsequenzen:**
- `BoatState.start_time` = individueller Startzeitpunkt des Boots (Reihen-Offset).
- Die **erste Runde** wird ab `start_time` gemessen (nicht ab globalem Rennstart).
- Gesamtzeit/Platzierung zählen ab dem individuellen Start.
- Eine Passage **vor** dem individuellen Start ist **UNGÜLTIG** (INVALID).
- Die GUI zeigt in der Live-Tabelle die **Startreihe** und den Status
  **WARTET** (vor Start) / **GESTARTET**.
- **Startreihen-Countdown ANSTATT Vorstart-Countdown (2026-09-03):** Nach dem
  Rennstart zeigt die **VORSTART-Kachel** den Countdown bis zum Start der
  nächsten Startreihe ("START REIHE N:"). Es gibt **keine separate** Kachel
  mehr – der Startreihen-Countdown ersetzt den Vorstart-Countdown.
- Beim Start jeder Startreihe wird ein **STARTLINE**-Event protokolliert.

---

## 4b. Manuelle Ziellogik (Kundenentscheidung 2026-09-03)

**Nach Ablauf der Renndauer passiert NICHTS automatisch.** Die frühere
"Letzte Runde"-Logik (finish_mode, TRIGGERED) wurde komplett entfernt.

- Nach der Renndauer wechselt die Engine in die Phase **FINISHING**.
- Jede Klasse bekommt im Rennende-Status einen **"Beenden"-Button**.
- Beim Drücken werden **alle Boote der Klasse** als fertig markiert
  (`finished_at = Zeitpunkt der Beendigung`) und ein **FINISH**-Event je Boot
  protokolliert. Das Ergebnis steht damit fest (meiste Runden in kürzester Zeit).
- **Platzierung pro Klasse (2026-09-04):** Die Platzierung wird **innerhalb
  jeder Klasse** vergeben – in jeder Klasse gibt es einen Ersten, Zweiten, …
  (nicht global über alle Boote). Sortierung je Klasse: erst Rundenzahl
  absteigend, dann Gesamtzeit aufsteigend.
- Klassen-Status nur noch: **WARTEND** (offen) → **FERTIG** (beendet).
- Wenn **alle Klassen** beendet sind, wechselt die Engine zu **FINISHED**.
- Ein beendetes Boot nimmt keine weiteren Passagen mehr an (INVALID).
- **Keine Leerzeile unter der Überschrift (2026-09-03):** Das Hinweis-Label
  ("Keine Klassen geladen") wird nur angezeigt, wenn wirklich keine Klassen
  vorhanden sind – sonst entsteht keine unnötige Leerzeile.

## 4b. Ergebnis-Persistenz beim Rennwechsel (2026-09-03)

- **Option 1 (Kundenentscheidung):** Die Ergebnisse eines **beendeten** Rennens
  bleiben beim Rennwechsel **in-memory** erhalten (`engine.finished_races`,
  keyed by `race_number`).
- Beim Zurückwechseln zu einem bereits beendeten Rennen werden die Ergebnisse
  wiederhergestellt: Runden, `finished_at`, Platzierung, Klassen-Status
  (FERTIG/CLOSED) und das Renn-Log (Events).
- Ein frisch geladenes Rennen steht immer auf **RESET** (bereit für PLAY) –
  auch wenn es zuvor beendet war. Die wiederhergestellten Ergebnisse sind
  dann sichtbar.
- **Kein Start bei beendetem Rennen (2026-09-03):** Ist das geladene Rennen
  bereits beendet (liegt in `finished_races`), ist der **START-Button grau und
  inaktiv** – das Rennen ist fertig, es kann nur noch angesehen/exportiert
  werden. Ein nicht beendetes Rennen hat den START-Button aktiv.

## 4c. Export aller fertigen Rennen (2026-09-03)

- Der Export-Button ist **immer aktiv** – er ist unabhängig vom aktuellen
  Rennen, weil er ALLE fertigen Rennen auf einmal exportiert.
- Er schreibt **ALLE fertigen Rennen** in EINE Datei
  `RESULT_<Zeitstempel>.json`.
- Aufbau: `races[]` sortiert nach Rennnummer, innerhalb jedes Rennens die
  Ergebnisse **nach Klasse gruppiert** (Kundenwunsch: "Rennen 1 Klasse Herren:
  erster, zweiter, … / Rennen 2 Klasse Junioren: …").
- Enthalten sind alle bereits beendeten Rennen aus `engine.finished_races`
  plus das aktuelle Rennen, falls es gerade FINISHED ist.
- **Noch kein Rennen beendet:** Es wird trotzdem eine Datei erzeugt – mit nur
  den Stammdaten (Event) und leerer `races`-Liste (keine Fehlermeldung).

## 4d. Hotkeys & Admin-Rechte (2026-09-03)

- **Hotkeys nur bei gestarteten Startern aktiv:** Ein Hotkey ist nur aktiv
  (grün), wenn die Startreihe des Boots gestartet ist. Nicht gestartete Boote
  sind grau und inaktiv.
- **Hotkeys beendeter Klassen inaktiv (2026-09-03):** Sobald eine Klasse
  beendet (Status FERTIG/CLOSED) ist, werden die Hotkeys ihrer Boote grau und
  inaktiv – auch wenn sie gestartet waren.
- **Keine "Aktiv: ..."-Zeile mehr (2026-09-03):** Die zweite Zeile unter der
  Überschrift (die Liste der aktiven Boot-Keys) wurde entfernt, um Platz zu
  sparen. Der Admin-Status in der Überschrift bleibt unverändert.
- **Admin-Rechte-Status:** Bei der Überschrift "Tastaturbedienung (Hotkeys)"
  wird informativ angezeigt, ob die systemweiten Hotkeys aktiv (grün) oder
  inaktiv (grau) sind. Die systemweiten Hotkeys (keyboard-Library) benötigen
  Windows-Admin (AGENTS.md §10) – Start als Admin über
  `Start_Zeitnehmung_Admin.cmd`.

## 4d. Live-Tabelle: Runner-Spalte + Geschw.-Spalte (2026-09-03)

- **Runner-Spalte mit fixer Breite:** Die Spalte "Runner" hat eine feste
  Breite und dehnt sich nicht. Zu lange Namen werden auf 18 Zeichen gekürzt
  und mit "…" abgeschnitten.
- **Neue Spalte "Geschw.":** Zwischen "Letzte Runde" und "Gesamtzeit" zeigt
  die Spalte zwei Werte getrennt durch "/":
  - **a) km/h letzte Runde** = Strecke der letzten Runde / Rundenzeit.
    Die 1. Runde nutzt `lap1_length_m`, alle weiteren Runden
    `standard_lap_length_m`.
  - **b) km/h gesamt** = Gesamtstrecke / Zeit bis zum letzten Passieren der
    Startlinie. Gesamtstrecke = 1. Runde + (Runden-1) × Standardrunde.
  - Fehlt ein Wert (noch keine Runde), wird "–" angezeigt (z. B. "–/–").
- Die Streckenlängen kommen aus der IMPORT.json (`lap1_length_m`,
  `standard_lap_length_m` des aktuellen Rennens).

## 4e. "Beenden"-Button erst nach Rennende aktiv (2026-09-03)

- Der "Beenden"-Button je Klasse ist **immer sichtbar**, aber **erst aktiv**,
  wenn die Rennzeit abgelaufen ist (Phase FINISHING/FINISHED).
- Vorher ist er **inaktiv (grau)**.
- Nach Rennende wird er **aktiv (gelb)** – solange die Klasse noch nicht
  beendet (CLOSED) ist.
- Sobald die Klasse beendet ist (Status FERTIG), wird der Button wieder
  **inaktiv (grau)**.

## 4f. Crash-Recovery-Details (2026-11-06)

- `race_state.json` liegt neben der `.exe` (Entwicklung: Projekt-Root).
- Gespeichert werden: Rennnummer, Phase, Zeitstempel, Boot-Zustände,
  **vollständige Runden (Start/Ende)**, Events, Klassen-Status und
  `started_lines`.
- Der State enthält `_saved_at`, `_version = 2` und
  `_source_fingerprint` (Pfad + Größe + Änderungszeit der geladenen
  JSON-/Excel-Quelle).
- Beim Start wird der State nur übernommen, wenn:
  - er höchstens **12 Stunden** alt ist,
  - die Rennnummer zur geladenen Konfiguration passt,
  - der Quell-Fingerprint zur aktuellen Datei passt.
  Sonst wird er verworfen und gelöscht.
- Unveränderte States werden höchstens alle **30 Sekunden** erneut
  geschrieben (Heartbeat). Das Schreiben erfolgt atomar
  (Temp-Datei + `os.replace`), damit kein halbes JSON entsteht.
- Rundenzeiten werden **nicht mehr synthetisch gemittelt**. Fehlen in einem
  alten State die Lap-Details, bleibt die Rundenliste leer (lieber keine
  Daten als falsche Zeiten).

## 4g. Dateien neben der `.exe`

| Datei | Zweck |
|-------|-------|
| `Wasserski-Zeitnehmung.exe` | Programm |
| `IMPORT.json` | Renndaten (aus Excel exportiert) |
| `app_settings.json` | Sperrzeit/Hotkeys (wird beim ersten Start angelegt) |
| `blackbox.log` | Beweisprotokoll (append-only, nie löschen) |
| `race_state.json` | Crash-Recovery (wird automatisch verwaltet) |
| `RESULT_*.json` | Ergebnis-Exporte |
| `gui_startup.log` | Diagnose bei Startproblemen |

---

## 5. Renn-Log (`_IMP_LOG`)

Das Log ist ein **vollständiges Ereignisprotokoll** – so als wäre ein Zeilendrucker angeschlossen.
Jede Zeile hat einen Zeitstempel, einen EventType (immer UPPERCASE) und einen Datenbereich.

### Event-Types

| Event | Wann | Daten-Format | Beispiel |
|-------|------|-------------|----------|
| `START` | Beginn eines Rennens | `Race={Nr}` | `START: Race=1 STATUS: VALID` |
| `STARTLINE` | Start einer Startreihe | `Race={Nr};Line={Nr}` | `STARTLINE: Race=1;Line=1 STATUS: VALID` |
| `PASSAGE` | Fahrer hat Runde vollendet | `Boot={Nr}` | `PASSAGE: Boot=173 STATUS: VALID` |
| `FINISH` | Klasse manuell beendet | `Boot={Nr}` | `FINISH: Boot=173 STATUS: VALID` |
| `CORRECTION_PLUS` | Manuelle Korrektur +1 Runde | `Boot={Nr};Delta=+1` | `CORRECTION_PLUS: Boot=65;Delta=+1 STATUS: VALID` |
| `CORRECTION_MINUS` | Manuelle Korrektur −1 Runde | `Boot={Nr};Delta=-1` | `CORRECTION_MINUS: Boot=65;Delta=-1 STATUS: VALID` |
| `INVALID` | Sperrzeit verletzt / Fehlbedienung | `Boot={Nr}` | `INVALID: Boot=65 STATUS: INVALID` |

**Regel:** EventType ist **immer UPPERCASE** (z.B. `PASSAGE`, nicht `Passage`).
`PAUSE`/`RESUME`/`ENDRACE` sind derzeit **keine** eigenen Log-Events;
Pause/Weiter steuern nur den Countdown, das Rennende wird über `FINISH`
je Boot abgebildet.

### Log-Zeilen-Format

```
[2026-08-20 14:30:00.123] START: Race=1 STATUS: VALID
[2026-08-20 14:30:00.125] STARTLINE: Race=1;Line=1 STATUS: VALID
[2026-08-20 14:30:15.200] STARTLINE: Race=1;Line=2 STATUS: VALID
[2026-08-20 14:31:05.445] PASSAGE: Boot=173 STATUS: VALID
[2026-08-20 14:31:08.112] INVALID: Boot=65 STATUS: INVALID
[2026-08-20 14:33:22.890] FINISH: Boot=173 STATUS: VALID
```

---

## 6. GUI-Beschreibung

*(Wird bei Bedarf ergänzt – siehe `architecture_and_roadmap/05_a_GUI_Description.txt` für Details)*

---

## 7. Offene Punkte

- [x] VBA-Script `ExportExpRangesToJSON` (alle `_EXP_`-Ranges → JSON) ✅ im Excel
- [x] Python `VbaMacroCaller` (ruft VBA-Makro via COM auf) ✅
- [x] Python `JsonRaceStore` (liest IMPORT.json) ✅
- [x] Python `JsonResultWriter` (schreibt Ergebnis-JSON) ✅
- [x] Crash-Recovery-Logik in AppController ✅
- [x] Demo-Daten entfernt (App lädt NUR echte Daten; Testdaten in `tests/demo_data.py`) ✅
- [x] Rennparameter-Entscheidung: Startintervall (Vorlaufzeit) + Grid Time (Zeit zwischen Startreihen) als Pflichtfelder aus der Excel, keine hartcodierten Fallbacks ✅
- [x] Startreihen-Funktionalität (Variante A: zeitversetzte Starts) – individuelle Startzeit pro Startreihe, Startreihen-Countdown, STARTLINE-Events, Startreihe in Live-Tabelle ✅
- [x] Manuelle Ziellogik (2026-09-03): "Beenden"-Button je Klasse statt automatischer Letzte-Runde-Logik; Hotkeys nur bei gestarteten Startern aktiv; Startreihen-Countdown ANSTATT Vorstart-Countdown; Admin-Rechte-Status bei "Tastaturbedienung" ✅
- [x] Live-Tabelle (2026-09-03): Runner-Spalte mit fixer Breite (Name wird abgeschnitten); neue "Geschw."-Spalte (km/h letzte Runde / km/h gesamt); "Beenden"-Button erst nach Rennende aktiv ✅
- [x] Ergebnis-Persistenz beim Rennwechsel (2026-09-03): Ergebnisse beendeter Rennen bleiben in-memory erhalten (`finished_races`), beim Zurückwechseln wiederhergestellt ✅
- [x] Export aller fertigen Rennen (2026-09-03): `RESULT_<Zeitstempel>.json`, gruppiert nach Rennen und Klasse ✅
- [x] VBA-Script `MainJsonImport` (Ergebnis-JSON → Sheets `results`/`log`) ✅ im Excel
- [x] Crash-Recovery gehärtet (2026-11-06): vollständige Runden, 12h-Altersprüfung, Rennnummer + Quell-Fingerprint, atomares Schreiben, Save-Drosselung ✅
- [x] Altes `IMPORT.json`-Format (ohne `FLD_`/`CODE`) wird klar abgelehnt statt still 0 Rennen zu laden ✅
- [x] Blackbox mit `fsync` (Beweisfunktion auch bei Stromausfall) ✅
- [x] Laufzeitdateien (`race_state.json`, `blackbox.log`, `gui_startup.log`, Exporte) neben der `.exe` ✅
- [ ] **Excel-Direktstart:** Python-Aufruf von `mdlEngl` auf das aktuelle Modul `mdl_Engl_Export` umstellen (offener Punkt 1, Kunde prüft Excel)
- [ ] Race-End-Event (`ENDRACE`) – oder reicht `FINISH` als letztes pro Boot?
- [ ] VBA-Export bereinigen: `Starttimer`/`Startzeit` entfernen (Kundenentscheidung 2026-08-20, nicht benötigt)

