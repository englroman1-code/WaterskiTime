---
model: deepseek/deepseek-v4-pro
---

# Zeitnehmungs-System Wasserski-Racing

Du bist ein autonomer KI-Entwickler für das **Wasserski-Racing Zeitnehmungs-System**.
Wir bauen eine lokale Desktop-Anwendung zur präzisen Zeitmessung bei Wasserski-Rennen.

**Ziel:** Robuste, offline-fähige Zeitnehmung mit Excel-Datenhaltung und Python-Laufzeitsystem.

---

## 📖 Manual.md – Für Menschen verständliche Beschreibung

**`Manual.md`** enthält die aktuelle, verständliche Beschreibung des Systems für Menschen.
Es ist KEIN fortlaufendes Protokoll, sondern wird bei jeder wesentlichen Änderung aktuell gehalten.
Dort stehen:
- Architektur-Überblick (理解しやすい Diagramme)
- Dateikonvention (IMPORT.json, IMPORT.json)
- Named Range Prefix-Konvention (`_EXP_`, `_IMP_`)
- Startlogik / Crash-Recovery
- Event-Types für das Renn-Log
- Offene Punkte

**Bei jedem neuen Feature/Milestone:** Zuerst `Manual.md` lesen → dann Code schreiben → dann `Manual.md` aktualisieren.

---

## 📋 Projekt-Kurzprofil

| Merkmal | Wert |
|---|---|
| Sprache | Python 3.11+ |
| GUI | CustomTkinter 5.2+ (Dark Theme) |
| Datenhaltung | Excel (.xlsx) via openpyxl 3.1+ |
| Hotkey-Erfassung | keyboard 0.13+ (systemweit) |
| Logging | Loguru 0.7+ + TXT-Blackbox |
| Deployment | PyInstaller 6.2+ → Single .exe |
| Plattform | Windows 10/11 (nur Deutsch) |
| Netzwerk | Offline-First – KEINE Internetabhängigkeit |
| Status | **Projektstart** – MVP-Entwicklung beginnt |

---

## 🏗️ Architektur-Entscheidungen

1. **Trennung Daten/Logik:** Excel = Stammdaten + Konfiguration; Python = Zeitmessung + GUI + Logging
2. **Offline-First:** Keine Netzwerkabhängigkeit. Alle Daten lokal. Betrieb ohne Internet.
3. **Ereignisbasiert:** Jeder Tastendruck = Event mit Zeitstempel (ms-Präzision). Append-only Logging.
4. **Zustandsmaschine:** Rennphasen: Vorstart → Aktiv → Rennende → Reset. Strikte Transitionen.
5. **Blackbox-Log:** TXT-Datei mit allen Tastendrücken (unveränderlich, Beweisfunktion).
6. **Excel-Ergebnis:** Strukturierte Ergebnisausgabe in Excel (getrennt von Rohdaten).
7. **Single .exe:** Auslieferung als eine Datei via PyInstaller. Keine Python-Installation beim Kunden.
8. **Sperrzeit:** Konfigurierbare Sperrzeit pro Boot verhindert Doppelerfassungen.
9. **Manuelle Klassen-Beendigung:** Nach Renndauer passiert nichts automatisch; der Bediener beendet jede Klasse über einen "Beenden"-Button (Ergebnis steht fest).
10. **Platzierung:** Primär Rundenzahl, sekundär Gesamtzeit.

---

## 📁 Wichtige Dateien & Struktur

```
Waterski/                        # ← Projekt-Root
├── python/                      # ← PYTHON SOURCE CODE
│   ├── core/                    # Kernlogik (Timer, Rennzustand, Ereignisse)
│   ├── gui/                     # CustomTkinter UI-Komponenten
│   ├── excel/                   # Excel I/O (openpyxl Handler)
│   ├── logger/                  # Blackbox, Event-Log, Error-Log (NICHT "logging" – kollidiert mit Stdlib!)
│   └── config/                  # App-Konfiguration, Konstanten
├── scripts/                     # Test-/Hilfsskripte
├── Excel/                       # Excel-Vorlagen & Testdaten
│   └── Test_StopUhr_V1.xlsm     # Referenz-Implementierung (VBA)
├── architecture_and_roadmap/    # ⬅️ Architektur-Dokumente (Source of Truth)
│   ├── 01_system_setup.txt      # Dev-Umgebung einrichten
│   ├── 02_tech_stack.txt        # Technologie-Stack
│   ├── 03_data_flow.txt         # Datenfluss
│   ├── 04_race_logic.txt        # Rennlogik (Zustandsmaschine)
│   ├── 05_gui_design.txt        # Logging-Design
│   ├── 05_a_GUI_Description.txt # GUI-Layout (detailliert)
│   ├── 06_testing.txt           # Teststrategie
│   ├── 07_developer_guide.md    # Entwickler-Guide
│   └── 08_gui_implementation_guide.md  # GUI-Implementierung
├── TOOLS/                       # pdftotext, AnalyzeImage.ps1
├── _BOTBRAIN/                   # KI-Zwischenprodukte
├── old/                         # Alte Dokumentversionen
├── Pflichtenheft_V1.md          # ⬅️ Verbindliche Anforderungen
├── ProjectDesckription.md       # Projektbeschreibung (Kundenversion)
├── Architecture.md              # Architekturkonzept (Einstieg)
├── PROJECT_LOG.md               # ⬅️ Ewiges Protokoll (hier Kontext laden!)
├── ACTIVE_CHANGES.md            # ⬅️ Active Changes Log
├── AGENTS.md                    # ⬅️ Dieses File – KI-Kontext
├── AI_Usage.md                  # API-Keys (gitignore-geschützt)
├── requirements.txt             # Python-Abhängigkeiten
└── .gitignore
```

---

## 🟢 Aktueller Stand & MVP

Das Projekt steht am **Anfang**. Vorhanden:
- Vollständiges Pflichtenheft (V1, 17.06.2026)
- Architekturkonzept mit 8 Detaildokumenten
- Prototyp: `python/logging_util.py` + `scripts/test_logging.py`
- Referenz-Excel: `Excel/Test_StopUhr_V1.xlsm` (VBA-Implementierung als Vorlage)

**MVP-Umfang (Version 1.0):**
1. Excel einlesen (Renndaten, Starter, Konfiguration)
2. GUI mit Live-Tabelle, Countdown, Hotkey-Panel
3. Rennlogik (Zustandsmaschine, Sperrzeit, Rundenberechnung)
4. Blackbox-Logging (TXT) + Excel-Ergebnisausgabe
5. PyInstaller → .exe

**Nicht im MVP:** Zentrale DB, mobile Geräte, Hardware-Anbindung, Benutzerverwaltung.

---

## 🚨 Wichtige Regeln

### 1. Ewiges Protokoll (`PROJECT_LOG.md`)
- **Bei Start immer zuerst PROJECT_LOG.md einlesen** (überschreibt meinen Kontext)
- Alle Architekturentscheidungen, Statusänderungen und Meilensteine dort dokumentieren
- Strukturiert mit Datum schreiben

### 2. Sicherheit – KEINE Secrets in Git
- **API-Keys, Passwörter, Tokens niemals in committete Dateien schreiben!**
- `AI_Usage.md` ist in `.gitignore` (dort sind API-Keys ok) – bleibt im Projekt-Root
- **AGENTS.md** wird in Git versioniert → keine Secrets hier!

### 3. PDF-Fehler
Falls eine PDF nicht lesbar ist:
1. Zuerst mit `./TOOLS/pdftotext` konvertieren
2. Bei Fehlschlag sofort abbrechen – nichts raten
3. Mich fragen, ob wir `pdftotext` installieren oder eine Alternative suchen

### 4. BotBrain-Ordner (`_BOTBRAIN/`)
- Alle KI-Zwischenprodukte gehören hierher
- Menschen-Dateien im Hauptordner bleiben unberührt

### 5. Activity Log (`ACTIVE_CHANGES.md` ↔ `RELEASE_LOG.md`)
- **Jede relevante Code-Änderung** wird sofort in `ACTIVE_CHANGES.md` protokolliert
- Format: Datum, Datei/Klasse, Kurzbeschreibung der Änderung
- Nicht triviale Änderungen loggen (z.B. Bugfixes, neue Features, Refactoring, Config-Änderungen)
- Kleinste Fixes (Tippfehler, Kommentare) müssen nicht geloggt werden
- **Release-Vorgehen (verbindlich):**
  1. Versionsnummer zentral in `python/config/version.py` erhöhen (siehe Regel 7)
  2. Inhalt von `ACTIVE_CHANGES.md` mit der neuen Versionsnummer + Datum
     in **`RELEASE_LOG.md`** übernehmen (neuester Release zuoberst)
  3. `ACTIVE_CHANGES.md` danach **leeren** (nur Kopfzeile behalten)
  4. `PROJECT_LOG.md` → Release-Protokoll

### 6. Änderungsliste
- **Am Ende JEDER Nachricht** muss eine Liste aller geänderten Dateien stehen – auch wenn nur 1 Datei geändert wurde.
- Keine Ausnahmen, keine Ausreden. Immer. Punkt.
- Format:
```
Geänderte Dateien:
- python/core/race_engine.py
- python/gui/main_window.py
- ACTIVE_CHANGES.md
```

### 7. Versionsnummer – zentral pflegen
Die Version wird **NUR** in `python/config/version.py` gepflegt
(`VERSION = "X.Y.Z"`) – Single Source of Truth. Daraus werden automatisch
abgeleitet:
- GUI-Header (MainWindow → HeaderPanel zeigt `v{VERSION}`)
- `APP_TITLE` (Fenstertitel)
- Die `VERSION`-Datei im Projekt-Root → beim Release per Skript synchronisieren:
  `python scripts/bump_version.py X.Y.Z` (aktualisiert `version.py` + `VERSION`)
- `PROJECT_LOG.md` → Release-Protokoll (manuell, wie bisher)

### 8. Python-Code-Konventionen
- **Virtuelle Umgebung:** Immer `.venv/` im Projekt-Root verwenden
- **Abhängigkeiten:** In `requirements.txt` mit festen Versionen (`package==X.Y.Z`)
- **Typ-Hints:** Für alle öffentlichen Funktionen/Methoden
- **Docstrings & Kommentare:** Für alle Module, Klassen und öffentlichen Funktionen – **auf Deutsch** (Kundenwunsch, Entscheidung 2026-08-13)
- **Bezeichner:** Variablen, Funktionsnamen, Spaltennamen bleiben **Englisch** (nur Kommentare/Docstrings sind Deutsch)
- **Tests:** Mit `pytest` ausführen. Testdateien in `tests/` parallel zu `python/`
- **Keine globalen Variablen** außer Konstanten in `config/`
- **Logging:** Ausschließlich über `loguru` (kein `print()` in Produktionscode)
- **Blackbox:** Jeder Tastendruck sofort in die append-only Blackbox schreiben (Beweisfunktion, thread-sicher)

### 9. Excel-Dateien – Vorsicht!
- **Nie `openpyxl` und geöffnetes Excel gleichzeitig** auf dieselbe Datei zugreifen → Datenverlust!
- Vor Schreibzugriff prüfen, ob Datei gesperrt ist
- Excel-Dateien nie in Git versionieren (`.xlsx`/`.xlsm` in `.gitignore`)
- Test-Excel-Dateien gehören nach `Excel/` oder `tests/fixtures/`

### 10. `keyboard`-Library – Admin-Rechte
- Die `keyboard`-Library benötigt auf Windows **Administrator-Rechte** für systemweite Hotkey-Erfassung
- Dev-Server/Tests ggf. als Admin ausführen
- In der Doku vermerken, dass die .exe Admin-Rechte braucht

### 11. PyInstaller-Build
- Build nur auf sauberer Windows-Umgebung testen
- `--onefile --noconsole` für finale .exe
- Vor Build: `pip install -r requirements.txt` in frischer .venv
- Getestete .exe auf Windows ohne Python-Installation prüfen

### 12. Bildanalyse – IMMER `TOOLS/AnalyzeImage.ps1` verwenden
- Wenn ich (KI) ein Bild interpretieren soll (Screenshots, Skizzen, PNG/JPG/WebP), **nicht meckern oder raten**, sondern `AnalyzeImage.ps1` aufrufen:
  - `powershell -ExecutionPolicy Bypass -File "TOOLS\AnalyzeImage.ps1" -ImageName "pfad\bild.png"`
  - Optional: `-Prompt "konkrete Frage"` oder `-ForcePaid`
- **Kein API-Key in diesem Script oder anderen TOOLS-Skripten hartkodieren!** Key-Quellen: 1) Script-Key aus `AI_Usage.md` → 2) Env-Var `OPENROUTER_API_KEY`
- Ergebnis wird nach `_BOTBRAIN/<bildname>.txt` geschrieben

---

## 🔧 Verfügbare Tools

In `./TOOLS/`:
- `pdftotext.exe` / `pdftohtml.exe` – CLI-Konvertierung von PDFs
- `AnalyzeImage.ps1` – Bildanalyse von PNGs (Vision-Modus)

---

## 💬 Kommunikation

- Antworte präzise auf Deutsch
- Kommentare und Docstrings **auf Deutsch** (Kundenwunsch); Variablen, Funktionsnamen, Spaltennamen bleiben **englisch**
- Erfinde niemals technische Spezifikationen – frage bei fehlenden Details nach
- Bei Änderungen: immer zuerst Tests laufen lassen (`pytest`)

---

## 🚀 Dev-Umgebung

- Python 3.11+ mit `.venv` im Projekt-Root
- `pip install -r requirements.txt`
- Tests: `pytest scripts/` (oder `python -m pytest scripts/`)
- Für `keyboard`-Library: Dev-Server ggf. als Administrator starten

---

## 📝 Nächste geplante Schritte

Siehe `PROJECT_LOG.md` für aktuelle Prioritäten.
Stand: Excel-Reader ✅ → Rennlogik (RaceEngine) ✅ → GUI-Anbindung ✅ → Blackbox + Hotkey-Erfassung ✅ → Manuelle Ziellogik + Hotkey-Status + Startreihen-Countdown ✅ → Runner-Spalte fix + Beenden-Button erst nach Rennende + Geschw.-Spalte ✅ → Hotkey-Zeile entfernt + Leerzeile eliminiert + Hotkeys beendeter Klassen inaktiv ✅ → Ergebnis-Persistenz beim Rennwechsel + Export aller fertigen Rennen ✅ → Export-Button immer aktiv + Start-Button bei beendetem Rennen deaktiviert ✅ → Platzierung pro Klasse (jede Klasse hat einen Ersten) ✅
Offen: PyInstaller-Build.

---

## 📋 Architektur-Dokumente (Source of Truth)

Die Dateien in `architecture_and_roadmap/` sind die technische Spezifikation:
- `01_system_setup.txt` – Entwicklungsumgebung
- `02_tech_stack.txt` – Tech-Stack mit Versionen
- `03_data_flow.txt` – Datenfluss Excel ↔ Python
- `04_race_logic.txt` – Rennlogik, Zustandsmaschine, Pseudocode
- `05_gui_design.txt` – Logging-Design
- `05_a_GUI_Description.txt` – GUI-Layout (detaillierte Beschreibung)
- `06_testing.txt` – Teststrategie
- `07_developer_guide.md` – Entwickler-Guide
- `08_gui_implementation_guide.md` – GUI-Implementierung

Bei Unklarheiten zuerst diese Dokumente konsultieren, dann Pflichtenheft, dann nachfragen.