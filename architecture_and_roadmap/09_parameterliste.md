# 09 – Parameterliste (tatsächlich benötigte Parameter)

> Stand: 2026-09-02 · Entscheidung: **KEINE hartcodierten Fallbacks** – fehlende Pflichtparameter
> führen zu einem Validierungsfehler, nie zu stillen Defaults.
>
> **Kundenentscheidungen (2026-09-02, umgesetzt):**
> 1. **Startintervall = Vorlaufzeit** – kommt aus Excel/IMPORT.json, **Pflichtfeld**, pro Rennen unterschiedlich.
> 2. **Grid Time = Zeit zwischen den Startreihen** – kommt aus Excel, **Pflichtfeld**.
> 3. Beide Werte in **Sekunden**.
> 4. `startreihe_offset_s` aus der App-Config **entfernt** (durch Grid Time ersetzt).
> 5. `Starttimer`/`Startzeit` werden nicht benötigt → aus dem VBA-Export entfernen.

## Legende

| Symbol | Bedeutung |
|---|---|
| ✅ Pflicht | Ohne diesen Parameter kann das System nicht arbeiten → Validierungsfehler |
| ⭕ Optional | Darf fehlen → wird dann als "–" angezeigt |
| ❌ Nicht nötig | Wird nicht benötigt → aus IMPORT.json/Excel entfernen |

---

## A) Renn-Event (INFO-Block)

| Parameter | Excel-Spalte / JSON-Key | Code-Feld | Status | Verwendung |
|---|---|---|---|---|
| Veranstaltung | `Veranstaltung` | `Event.title` | ✅ Pflicht | Anzeige (Header) |
| Datum | `Datum` | `Event.date` | ✅ Pflicht | Anzeige (Header) |
| Organisator | `Organisator` | `Event.organizer` | ✅ Pflicht | Anzeige (Header) |

---

## B) Renn-Konfiguration (RACES-Block, pro Rennen)

| Parameter | Excel-Spalte / JSON-Key | Code-Feld | Status | Verwendung |
|---|---|---|---|---|
| Rennnummer | `Race` | `race_number` | ✅ Pflicht | Zuordnung Starter → Rennen |
| Renndauer [min] | `Renndauer [min]` | `race_duration_min` | ✅ Pflicht | Rennende-Berechnung (`race_end`) |
| 1. Runde [km] | `1. Runde [km]` | `lap1_length_m` | ✅ Pflicht | Anzeige + Validierung |
| Rundenlänge [km] | `Rundenlänge [km]` | `standard_lap_length_m` | ✅ Pflicht | Anzeige + Validierung |
| **Startintervall (Vorlaufzeit) [s]** | `StartInterval` | `start_interval_s` | ✅ Pflicht | Countdown vor Rennstart (pro Rennen unterschiedlich) |
| **Grid Time [s]** | `Grid Time [s]` | `grid_time_s` | ✅ Pflicht | Zeit zwischen den Startreihen (Startreihen-Offsets) |
| Starttimer | `Starttimer` | – | ❌ Nicht nötig | Kundenentscheidung 2026-08-20 → aus VBA-Export entfernen |
| Startzeit | `Startzeit` | – | ❌ Nicht nötig | Immer null → aus VBA-Export entfernen |

---

## C) Starter (STARTER-Block, pro Boot)

| Parameter | Excel-Spalte / JSON-Key | Code-Feld | Status | Verwendung |
|---|---|---|---|---|
| Bootnummer | `BoatNr` | `boat_number` | ✅ Pflicht | Anzeige |
| Klasse | `Klasse` | `klasse` | ✅ Pflicht | Manuelle Klassen-Beendigung (2026-09-03) |
| Fahrer | `Skier` | `skier` | ✅ Pflicht | Anzeige |
| Rundentaste | `RundenTaste` | `boot_key` | ✅ Pflicht | Hotkey-Erfassung |
| Rennnummer | `Race` | `race_number` | ✅ Pflicht | Zuordnung Starter → Rennen |
| Startreihe | `Startreihe` | `startreihe` | ✅ Pflicht | Startreihen-Offset |
| Team | `Team` | `team` | ⭕ Optional | Anzeige |
| Fahrer (Beifahrer) | `Driver` | `driver` | ⭕ Optional | Anzeige |
| Beobachter | `Observer` | `observer` | ⭕ Optional | Anzeige |
| Verein | `Club` | `club` | ⭕ Optional | Anzeige |
| Verband | `Federation` | `federation` | ⭕ Optional | Anzeige |

---

## D) App-Einstellungen (app_settings.json)

| Parameter | JSON-Key | Code-Feld | Status | Verwendung |
|---|---|---|---|---|
| Sperrzeit [s] | `lockout_seconds` | `lockout_seconds` | ✅ Pflicht | Verhindert Doppelerfassung |
| Hotkeys aktiv | `enable_keyboard` | `enable_keyboard` | ✅ Pflicht | Systemweite Hotkey-Erfassung |
| ~~Startreihen-Offset [s]~~ | ~~`startreihe_offset_s`~~ | – | ❌ Entfernt | Ersetzt durch Grid Time aus der Excel (2026-09-02) |

---

## ✅ Entscheidungen (2026-09-02) – alle offenen Punkte geklärt

### 1. Startintervall = Vorlaufzeit ✅
- `StartInterval` aus der Excel/IMPORT.json treibt den Countdown (`start_interval_s`).
- **Pflichtfeld** – fehlt es, blockiert der DataValidator das Rennen.
- Kann pro Rennen unterschiedlich sein (Rennen 1: 15 s, Rennen 2: 20 s, …).

### 2. Grid Time = Zeit zwischen den Startreihen ✅
- `Grid Time [s]` aus der Excel/IMPORT.json steuert die Startreihen-Offsets (`grid_time_s`).
- **Pflichtfeld** – fehlt es, blockiert der DataValidator das Rennen.
- Der feste `startreihe_offset_s` aus der App-Config wurde **entfernt**.

### 2a. Startreihen-Offsets (Variante A – zeitversetzte Starts) ✅
- **Kundenentscheidung (2026-09-02):** Jedes Boot startet seine Zeitmessung
  erst, wenn seine Startreihe startet (Variante A).
- **Reihe 1** startet bei T=0, **Reihe 2** bei T=+Grid Time, **Reihe 3** bei
  T=+2×Grid Time, usw.
- `BoatState.start_time` = individueller Startzeitpunkt des Boots.
- Erste Runde + Gesamtzeit/Platzierung ab individuellem Start.
- Passage vor individuellem Start → **UNGÜLTIG** (INVALID).
- GUI: Startreihe in Live-Tabelle, Status WARTET/GESTARTET, Countdown-Kachel
  "START REIHE N", STARTLINE-Events im Renn-Log.

### 3. Beides in Sekunden ✅
- `start_interval_s` und `grid_time_s` sind beide in Sekunden – keine Mischeinheiten.

### 4. Starttimer / Startzeit entfernen ⏳ (VBA-Export)
- Laut Kundenentscheidung 2026-08-20 nicht nötig.
- **Offen:** Aus dem VBA-Makro `ExportExpRangesToJSON` entfernen (Kunden-Excel).

---

## Befüllungs-Kette (wie kommen die Parameter in die App?)

```
Excel (Named Ranges _EXP_*) 
   → VBA-Makro ExportExpRangesToJSON 
   → IMPORT.json 
   → JsonRaceStore (python/excel/json_race_store.py) 
   → RaceData 
   → DataValidator (Pflichtfelder prüfen!) 
   → App
```

App-Einstellungen (D) kommen direkt aus `python/config/app_settings.json` (kein Excel).