# Objektübersicht – Wasserski-Racing Zeitnehmung

Stand: 2026-09-06 · Version 0.2.0

Diese Übersicht zeigt die **Objekte** (Klassen/Module) des Systems, ihre
**Einbettungen** (welche Objekte sie enthalten/halten) und ihre
**Verbindungen** (welche Objekte sie nutzen/aufrufen).

---

## 1. Architektur auf einen Blick

```
┌────────────────────────────────────────────────────────────────────┐
│                        GUI-Schicht (python/gui/)                    │
│  MainWindow ── enthält ──> 9 Panels (Header, RaceInfo, Countdown,   │
│                             LiveTable, Hotkey, LogFeed,             │
│                             RaceEndStatus, ManualCorrection)        │
│  AppController  = Verbinder GUI ↔ Kernlogik                         │
└───────────────────────────────┬────────────────────────────────────┘
                                │ steuert / liest
┌───────────────────────────────▼────────────────────────────────────┐
│                        Kernlogik (python/core/)                    │
│  RaceEngine (Zustandsmaschine)                                     │
│    ├─ LockoutManager      (Sperrzeit)                              │
│    ├─ ClassFinishTracker  (manuelle Klassen-Beendigung)            │
│    ├─ ResultCalculator    (Wertung/Platzierung)                    │
│    ├─ InputHandler        (systemweite Hotkeys)                    │
│    └─ RaceStateManager    (Crash-Recovery)                         │
└───────────────┬──────────────────────────────┬─────────────────────┘
                │ liest                        │ schreibt
┌───────────────▼──────────────┐   ┌───────────▼─────────────────────┐
│  Datenhaltung (python/excel/)│   │  Logging (python/logger/)       │
│  JsonRaceStore   (IMPORT.json)│   │  BlackboxWriter (blackbox.log) │
│  JsonResultWriter (Ergebnis) │   │  AppLogger (loguru)             │
│  VbaMacroCaller  (Excel↔JSON)│   └─────────────────────────────────┘
└──────────────────────────────┘
```

---

## 2. Domänenmodell (python/core/models.py)

Die **fachlichen Datenstrukturen** – bewusst unabhängig vom Excel-Format.

### Enums
| Objekt | Werte | Bedeutung |
|---|---|---|
| `EventType` | START, STARTLINE, PASSAGE, FINISH, CORRECTION_PLUS, CORRECTION_MINUS, INVALID | Ereignistypen (§5.1) |
| `RacePhase` | PRESTART, ACTIVE, FINISHING, FINISHED, RESET | Rennphasen der Zustandsmaschine (ADR-005) |

### Stammdaten (aus Excel/IMPORT.json)
| Objekt | Enthält | Verbindungen |
|---|---|---|
| `Event` | title, date, organizer | Veranstaltung (1 Event → viele Rennen) |
| `Starter` | boot_key, boat_number, skier, team, driver, observer, club, federation, klasse, race_number, startreihe | 1 Starter = 1 Boot; gehört zu 1 Klasse + 1 Startreihe |
| `StartLine` | number, offset_seconds | Startreihe mit Zeitoffset |
| `RaceConfig` | race_number, race_duration_min, start_interval_s, lap1_length_m, standard_lap_length_m, grid_time_s | Konfiguration EINES Rennens |

### Laufzeit-Objekte (entstehen während des Rennens)
| Objekt | Enthält | Verbindungen |
|---|---|---|
| `RaceEvent` (frozen) | timestamp, boot_key, event_type, valid, source | Rohdaten, unveränderlich (Beweisfunktion) |
| `Lap` | number, start_time, end_time, duration | Eine gefahrene Runde |
| `BoatState` | **starter**, **laps[]**, last_passage, lockout_until, finished_at, place, start_time | **Einbettung:** hält `Starter` + Liste von `Lap`; berechnet total_time, last_lap, best_lap, speed |
| `BoatResult` | starter, laps_count, total_time, best_lap, place | Endergebnis für Wertung/Export |
| `RaceClass` | name, finish_state (WAITING/CLOSED) | Laufzeit-Klasse, nur für Auswertung |

---

## 3. Kernlogik (python/core/)

| Objekt | Verantwortung | Nutzt (Verbindungen) |
|---|---|---|
| **`RaceEngine`** | Zentrale Zustandsmaschine: Phasen, Countdown, Ereignisverarbeitung, Wertung | **Einbettet:** `boats: dict[str,BoatState]`, `classes: dict[str,RaceClass]`, `events: list[RaceEvent]`, `start_lines: dict[int,StartLine]`, `finished_races: dict[int,dict]`; **nutzt:** `LockoutManager`, `ClassFinishTracker`, `ResultCalculator`, `models` |
| `LockoutManager` | Sperrzeit je Boot (§5.2) | wird von RaceEngine injiziert |
| `ClassFinishTracker` | Manuelle Klassen-Beendigung (WAITING→CLOSED) | hält Referenzen auf `classes` + `boats` |
| `ResultCalculator` | Runden verbuchen + Wertung (Runden primär, Zeit sekundär) | statische Methoden auf `BoatState` |
| `InputHandler` | Systemweite Hotkey-Erfassung (keyboard) | **Einbettet:** `HotkeyMapping`; schreibt in `input_queue` + `BlackboxWriter` |
| `HotkeyMapping` | Boot-Key → Taste (A–Z + Zahlenblock-Alias) | aus `Starter` |
| `RaceStateManager` | Crash-Recovery (`race_state.json`) | serialisiert/deserialisiert Engine-Zustand |
| `StarterList` | Starter-Verwaltung | aus `Starter` |
| `RaceData` | Container: Event + Races + Starter | Sammelobjekt für geladene Daten |
| `data_validator.validate_scenario` | Validierung der geladenen Daten | prüft `RaceData` |

---

## 4. GUI-Schicht (python/gui/)

### MainWindow (python/gui/main_window.py)
| Objekt | Verantwortung | Einbettungen |
|---|---|---|
| **`MainWindow`** (ctk.CTk) | Hauptfenster, baut alle Panels | **Enthält:** HeaderPanel, RaceInfoPanel, CountdownPanel, LiveTablePanel, HotkeyPanel, LogFeedPanel, RaceEndStatusPanel, ManualCorrectionPanel |
| **`AppController`** | Verbinder GUI ↔ RaceEngine | **Enthält:** `engine: RaceEngine`, `blackbox: BlackboxWriter`, `_input_handler: InputHandler`, `_state_manager: RaceStateManager`, `window: MainWindow`; **nutzt:** JsonRaceStore, JsonResultWriter, VbaMacroCaller |

### Panels (python/gui/panels.py)
| Objekt | Verantwortung | Verbindungen |
|---|---|---|
| `HeaderPanel` | Titel, Version, Quelle, Refresh-/Export-Button | Callbacks → AppController |
| `RaceInfoPanel` | Veranstaltungs-/Renninfo | zeigt `Event` + `RaceConfig` |
| `CountdownPanel` | Countdown, PAUSE/WEITER, NEUSTART, Rennen-Auswahl | Callbacks → AppController |
| `LiveTablePanel` | Live-Tabelle (Runden, Zeiten, Geschw., Platz) | zeigt `BoatState`-Liste |
| `HotkeyPanel` | Virtuelle Tastatur (Boot-Keys) | Callback → AppController |
| `LogFeedPanel` | Live-Ereignis-Log | zeigt `RaceEvent` |
| `RaceEndStatusPanel` | Klassen-Status + "Beenden"-Button | zeigt `RaceClass`; Callback → AppController |
| `ManualCorrectionPanel` | Manuelle +1-Runde-Korrektur | zeigt `BoatState`; Callback → AppController |

---

## 5. Datenhaltung (python/excel/)

| Objekt | Verantwortung | Verbindungen |
|---|---|---|
| **`JsonRaceStore`** | Liest `IMPORT.json` (Event, Races, Starter) | → liefert `Event`, `RaceConfig[]`, `Starter[]` |
| **`JsonResultWriter`** | Schreibt Ergebnis-JSON (`Ergebnis_AlleRennen_*.json`) | nutzt `RaceResultExport` (Container) |
| `RaceResultExport` | Container für Export (Event + Races + Ergebnisse) | aus `BoatResult` |
| **`VbaMacroCaller`** | Ruft VBA-Makro via COM auf (Excel↔JSON) | Excel-Datei |

---

## 6. Logging (python/logger/)

| Objekt | Verantwortung | Verbindungen |
|---|---|---|
| **`BlackboxWriter`** | Append-only Beweisprotokoll (`blackbox.log`), thread-sicher | wird von InputHandler + AppController genutzt |
| `AppLogger` | loguru-Konfiguration (Konsole + Datei) | global |
| `logging_util` | Prototyp/Alt-Logik | — |

---

## 7. Konfiguration (python/config/)

| Objekt | Verantwortung |
|---|---|
| `AppConfig` | Konstanten/Farben |
| `AppSettings` + `ConfigManager` | App-Parameter (z. B. `lockout_seconds`), JSON load/save |
| `version.py` | `VERSION = "0.2.0"` – Single Source of Truth |

---

## 8. Zentrale Verbindungsübersicht (Wer nutzt wen)

```
AppController
  ├─ RaceEngine          (steuert Rennlogik)
  ├─ MainWindow + Panels (GUI)
  ├─ BlackboxWriter      (Beweis-Log)
  ├─ InputHandler        (Hotkeys)
  ├─ RaceStateManager    (Crash-Recovery)
  ├─ JsonRaceStore       (liest IMPORT.json)
  ├─ JsonResultWriter    (schreibt Ergebnis-JSON)
  └─ VbaMacroCaller      (Excel↔JSON)

RaceEngine
  ├─ LockoutManager      (Sperrzeit)
  ├─ ClassFinishTracker  (Klassen-Beendigung)
  ├─ ResultCalculator    (Wertung)
  └─ models              (BoatState, RaceEvent, ...)

InputHandler
  ├─ HotkeyMapping       (Tasten-Zuordnung)
  ├─ BlackboxWriter      (Rohdruck)
  └─ input_queue         (→ AppController)
```

---

## 9. Datenfluss (Dateien)

```
Excel (Named Ranges _EXP_)
   │  VbaMacroCaller (COM)
   ▼
IMPORT.json ──JsonRaceStore──▶ RaceEngine ──▶ GUI (Live)
   ▲                              │
   │ JsonResultWriter             │ BlackboxWriter
   ▼                              ▼
Ergebnis_AlleRennen_*.json    blackbox.log (append-only)

race_state.json  ◀──RaceStateManager──▶  Crash-Recovery
```

---

## 10. Einbettungs-Hierarchie (Komposition)

```
MainWindow
 └─ AppController
     ├─ RaceEngine
     │   ├─ boats: dict[str, BoatState]
     │   │    └─ BoatState
     │   │        ├─ starter: Starter
     │   │        └─ laps: list[Lap]
     │   ├─ classes: dict[str, RaceClass]
     │   ├─ events: list[RaceEvent]
     │   ├─ start_lines: dict[int, StartLine]
     │   ├─ finished_races: dict[int, dict]
     │   ├─ LockoutManager
     │   ├─ ClassFinishTracker
     │   └─ ResultCalculator (statisch)
     ├─ BlackboxWriter
     ├─ InputHandler
     │    └─ HotkeyMapping
     ├─ RaceStateManager
     └─ (nutzt) JsonRaceStore / JsonResultWriter / VbaMacroCaller
```
