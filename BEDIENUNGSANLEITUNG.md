# Wasserski-Zeitnehmung – Bedienungsanleitung (Kurzfassung)

Stand: 2026-11-06, Version 0.3.0 (Release-Kandidat)

## 1. Voraussetzungen

- Windows 10/11
- Microsoft Excel (nur zum Erzeugen der `IMPORT.json` aus der Kunden-Excel)
- Für systemweite Hotkeys: Administrator-Rechte
- Keine Internetverbindung nötig

## 2. Installation

1. Den kompletten Ordner auf den Zielrechner kopieren.
2. `Wasserski-Zeitnehmung.exe` und `IMPORT.json` müssen im **selben Ordner**
   liegen.
3. Beim ersten Start legt die App `app_settings.json` daneben an.

## 3. Renndaten vorbereiten

1. `Test_StopUhr_V1.xlsm` (oder die aktuelle Kunden-Excel) öffnen.
2. Das Makro `ExportExpRangesToJSON` ausführen (Makros müssen in Excel
   erlaubt sein; ggf. die Datei als vertrauenswürdigen Speicherort
   hinzufügen).
3. Die Meldung „Export erfolgreich“ bestätigen.
4. Die entstandene `IMPORT.json` neben die `Wasserski-Zeitnehmung.exe`
   legen.

> **Bekannte Einschränkung (offener Punkt 1):** Der direkte Excel-Start aus
> der App ist derzeit nicht freigegeben, weil der Python-Aufruf noch den
> alten Modulnamen `mdlEngl` verwendet, die aktuelle Vorlage aber
> `mdl_Engl_Export`. Bis zur Korrektur bitte den Weg über die manuell
> erzeugte `IMPORT.json` verwenden.

## 4. Start

- **Normaler Start:** `Wasserski-Zeitnehmung.exe` doppelklicken.
- **Mit systemweiten Hotkeys:** Rechtsklick → „Als Administrator ausführen“
  (oder `Start_Zeitnehmung_Admin.cmd` in der Entwicklungsumgebung).
- Ohne Admin-Rechte funktioniert die Bedienung über die GUI, aber nicht
  über systemweite Tastatur-Hotkeys.

## 5. Bedienung

1. Rennen im Dropdown auswählen.
2. **PLAY** drücken – der Countdown (Startintervall) läuft.
3. Nach dem Countdown startet das Rennen automatisch.
4. Rundenpassagen mit den Boot-Hotkeys erfassen.
5. Nach Ablauf der Renndauer jede Klasse über **Beenden** abschließen.
6. **Export** schreibt alle fertigen Rennen als
   `RESULT_<Zeitstempel>.json` neben die `.exe`.

## 6. Dateien im Programmordner

| Datei | Bedeutung |
|-------|-----------|
| `IMPORT.json` | Renndaten (Eingabe) |
| `RESULT_*.json` | Ergebnis-Export (Ausgabe) |
| `blackbox.log` | Append-only Beweisprotokoll – **nie löschen** |
| `race_state.json` | Crash-Recovery – wird automatisch verwaltet |
| `gui_startup.log` | Start-/Diagnose-Log |
| `app_settings.json` | Sperrzeit/Hotkey-Einstellung |

## 7. Crash-Recovery

- Nach einem Absturz startet die App mit dem letzten gespeicherten Stand,
  sofern dieser **maximal 12 Stunden** alt ist und zur geladenen
  `IMPORT.json` passt.
- Ein alter oder fremder State wird automatisch verworfen.
- Rundenzeiten werden exakt aus dem State wiederhergestellt; es werden
  keine Zeiten geschätzt.

## 8. Störungshilfe

| Problem | Ursache / Lösung |
|---------|------------------|
| „Keine Renndaten gefunden“ | `IMPORT.json` fehlt neben der `.exe` oder ist ungültig. |
| „IMPORT.json verwendet das alte Feldformat“ | Excel mit der aktuellen Vorlage neu exportieren (`FLD_`/`CODE`-Felder). |
| Hotkeys reagieren nicht | App ohne Admin-Rechte gestartet → als Administrator starten. |
| Excel-Makro meldet „Makro nicht gefunden“ | Offener Punkt 1: Modulname `mdl_Engl_Export` vs. `mdlEngl`; `IMPORT.json` manuell erzeugen. |
| App startet nicht | `gui_startup.log` im Programmordner prüfen. |
