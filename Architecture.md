# Architekturkonzept: Zeitnehmungs-System via Excel & Python

Dieses Dokument dient als technische Ausgangslage und Leitfaden für die Entwicklung des Zeitnehmungs-Systems. Die Lösung trennt die Datenhaltung (Excel) strikt von der Logik und Benutzeroberfläche (Python), um maximale Stabilität in gemischten IT-Umgebungen zu gewährleisten.

## 1. Systemübersicht & Design-Entscheidung

Der Kunde pflegt Stammdaten (Fahrer, Klassen) und finale Ergebnisse in **Excel**. Die Erfassung der Rundenzeiten erfolgt über eine eigenständige **Python-Applikation**, die als vorkompilierte `.exe` ausgeliefert wird.

### Warum Python statt Excel-VBA?
* **Robuste Tastatur-Erfassung:** Echtzeit-Abfang von Hotkeys (`q`, `w`, `e`...) funktioniert in Python unabhängig vom Fokus des Fensters. VBA blockiert hierbei oft die Excel-Bedienung.
* **Kein Bit-Konflikt:** Die Python-App greift direkt auf die Datei zu. Es gibt keine Abstürze durch gemischte Excel-Installationen (32-Bit vs. 64-Bit) oder Versionsunterschiede (Excel 2016 vs. M365).
* **Zero Installation:** Der Kunde benötigt kein installiertes Python. Das System wird als einzelne `.exe`-Datei bereitgestellt.
* **KI-Unterstützung:** Python-Code lässt sich über KI-Tools in VS Code (GitHub Copilot / Cursor) deutlich fehlerfreier generieren und erweitern als VBA.

---

## 2. Technischer Stack

* **Programmiersprache:** Python 3.11+
* **UI-Framework:** `CustomTkinter` (Modernes, leichtgewichtiges GUI)
* **Hotkey-Erfassung:** `keyboard` (Echtzeit-Überwachung von Tastendrücken)
* **Excel-Schnittstelle:** `openpyxl` (Direktes Lesen/Schreiben von `.xlsx` ohne Excel-Instanz im Hintergrund)
* **Kompilierung:** `PyInstaller` (Erstellt die finale `.exe` für den Kunden)

---

## 3. Datenfluss & Workflow

1. **Vorbereitung:** Der Kunde öffnet die `zeitnehmung.xlsx` und trägt in die Tabelle `Fahrer` die Startnummern und Namen ein.
2. **Start:** Der Nutzer startet die `zeitnehmung.exe`. Das Skript liest die Fahrerdaten im Hintergrund ein.
3. **Rennen:** Das Python-GUI zeigt die Live-Stoppuhr. Bei Druck auf `q` (Fahrer 1), `w` (Fahrer 2) etc., loggt Python die exakte Systemzeit (Millisekunden-Präzision).
4. **Speichern:** Nach dem Rennen (oder optional live) schreibt Python die Rundenzeiten in eine neue Tabelle `Ergebnisse` in dieselbe Excel-Datei zurück.

---

## 4. Prototyp-Code (Einstieg für VS Code)

Erstellen Sie im Projektordner die folgenden zwei Dateien, um die Kernfunktionen direkt zu testen.

### Datei 1: `core_timer.py` (Hotkey & Zeit-Log)
Dieses Skript läuft im Hintergrund und demonstriert, wie Tastenanschläge präzise mitgeschrieben werden.

```python
import keyboard
import time
from datetime import datetime

# Zuweisung: Taste -> Startnummer
TASTEN_MAP = {
    'q': 1,
    'w': 2,
    'e': 3,
    'r': 4
}

print("=== Zeitnehmung gestartet ===")
print("Drücke Q, W, E oder R für die Fahrer 1-4. Drücke 'esc' zum Beenden.")

def taste_gedrueckt(event):
    taste = event.name
    if taste in TASTEN_MAP:
        fahrer_id = TASTEN_MAP[taste]
        jetzt = datetime.now()
        zeitstempel = jetzt.strftime("%H:%M:%S") + f",{jetzt.microsecond // 1000:03d}"
        
        print( f"Fahrer {fahrer_id} passiert! Zeit: {zeitstempel}" )

# Registriere die Hotkeys für alle definierten Tasten
for taste in TASTEN_MAP.keys():
    keyboard.on_press_key(taste, taste_gedrueckt)

# Halte das Skript am Laufen, bis 'esc' gedrückt wird
keyboard.wait('esc')
print("=== Zeitnehmung beendet ===")
```

### Datei 2: `excel_handler.py` (Excel lesen/schreiben)
Dieses Skript zeigt, wie unkompliziert Daten ohne geöffnetes Excel manipuliert werden.

```python
import openpyxl
from openpyxl import Workbook
import os

DATEI_NAME = "zeitnehmung.xlsx"

def erstelle_beispiel_excel():
    """Erstellt eine Test-Excel-Datei mit Fahrerdaten."""
    if not os.path.exists(DATEI_NAME):
        wb = Workbook()
        ws = wb.active
        ws.title = "Fahrer"
        ws.append(["Startnummer", "Name"])
        ws.append([1, "Max Mustermann"])
        ws.append([2, "Erika Mustermann"])
        wb.save(DATEI_NAME)
        print(f"'{DATEI_NAME}' wurde erfolgreich erstellt.")

def schreibe_rundenzeit(fahrer_id, runde, zeit):
    """Schreibt eine Rundenzeit in das Blatt 'Ergebnisse'."""
    wb = openpyxl.load_workbook(DATEI_NAME)
    
    if "Ergebnisse" not in wb.sheetnames:
        ws = wb.create_sheet(title="Ergebnisse")
        ws.append(["Startnummer", "Runde", "Zeitstempel"])
    else:
        ws = wb["Ergebnisse"]
        
    ws.append([fahrer_id, runde, zeit])
    wb.save(DATEI_NAME)
    print(f"Runde {runde} für Fahrer {fahrer_id} in Excel gespeichert.")

# Testlauf
if __name__ == "__main__":
    erstelle_beispiel_excel()
    schreibe_rundenzeit(1, 1, "12:30:15,450")
```

---

## 5. Deployment (Erstellung der .exe)

Um aus dem Python-Projekt eine ausführbare Datei für den Kunden zu generieren, werden folgende Schritte im VS Code Terminal ausgeführt:

1. **Benötigte Bibliotheken installieren:**
   ```bash
   pip install openpyxl keyboard customtkinter pyinstaller
   ```

2. **EXE generieren:**
   ```bash
   pyinstaller --onefile --noconsole main.py
   ```
   *(Hinweis: `--noconsole` versteckt das schwarze Eingabeaufforderungs-Fenster, sobald die GUI integriert ist. Für die obigen Konsolen-Prototypen weglassen).*

Die fertige Datei befindet sich anschließend im Ordner `dist/` und kann direkt an den Kunden weitergegeben werden.
