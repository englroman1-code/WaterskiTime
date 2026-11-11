# Wasserski-Racing Zeitnehmung – Benutzerhandbuch

**Für Bediener, Veranstalter und technische Betreuung**

| Merkmal | Inhalt |
|---|---|
| Produkt | Wasserski-Racing Zeitnehmung |
| Version | 0.5.0 |
| Dokumentstand | 10.11.2026 |
| Zielgruppe | Bediener am Veranstaltungsort, Rennleitung, technische Betreuung |
| Grundlage | Abgleich mit dem Python-Code (`python/`) und Pflichtenheft V1.0 vom 17.06.2026 |
| Sprache | Deutsch |

> **Hinweis zur Verbindlichkeit**
>
> Dieses Handbuch beschreibt den tatsächlichen Stand der Anwendung. Wo das
> Pflichtenheft und der umgesetzte Code voneinander abweichen, ist das in
> Abschnitt 16 ausdrücklich dokumentiert. Bei Widersprüchen gilt für die
> Bedienung der aktuelle Programmstand; für den Lieferumfang gilt das
> Pflichtenheft.

---

## Inhalt

1. Zweck und Überblick
2. Systemvoraussetzungen
3. Lieferumfang und Dateien
4. Schnellstart für den Renntag
5. Die Oberfläche im Detail
6. Renndaten in Excel vorbereiten
7. Rennablauf Schritt für Schritt
8. Anzeigen richtig lesen
9. Sperrzeit, Fehlbedienung und Korrekturen
10. Crash-Recovery und Stromausfall
11. Ergebnis-Export
12. Datenfluss, Ablage und Datensicherung
13. Technische Referenz: Excel-Schnittstelle
14. Renn-Log und Ereignistypen
15. Störungshilfe und häufige Fragen
16. Abgleich mit dem Pflichtenheft
17. Offene Punkte und bekannte Einschränkungen
18. Glossar
19. Bildplatzhalter und Screenshot-Liste
20. Dokumentenhistorie

---

## 1. Zweck und Überblick

Die **Wasserski-Racing Zeitnehmung** ist eine lokale Desktop-Anwendung zur
präzisen Zeitmessung bei Wasserski-Rennen. Sie unterstützt den Bediener dabei,
Rundenpassagen mehrerer Boote und Klassen zu erfassen, die Renndauer im Blick
zu behalten und am Ende belastbare Ergebnislisten zu erzeugen.

Die Anwendung ist für den Einsatz **am Veranstaltungsort** gedacht:

- Sie läuft vollständig **offline**. Es ist keine Internetverbindung nötig.
- Die Stammdaten und die Rennkonfiguration werden in **Excel** gepflegt.
- Die Zeitmessung, die Rennlogik, die Anzeige und die Protokollierung
  übernimmt die Python-Anwendung.
- Jede Eingabe wird **sofort und unveränderlich** in einer Blackbox-Datei
  protokolliert. Damit bleibt auch bei einem Absturz oder Stromausfall
  nachvollziehbar, was wann gedrückt wurde.
- Die Ergebnisse werden als **JSON-Datei** exportiert und können optional
  wieder in die Excel-Vorlage eingelesen werden.

### 1.1 Was das System leistet

- Verwaltung mehrerer Rennen, Klassen und Startreihen.
- Countdown mit Vorlaufzeit und automatischem Rennstart.
- Zeitversetzte Starts pro Startreihe über die **Grid Time**.
- Rundenpassagen per systemweitem Hotkey oder per Mausklick auf die
  virtuelle Tastatur.
- Sperrzeit gegen Doppelerfassungen.
- Manuelle Klassen-Beendigung nach Ablauf der Renndauer.
- Live-Anzeige von Runden, Rundenzeiten, Geschwindigkeiten, Gesamtzeiten
  und Status.
- Crash-Recovery über `race_state.json`.
- Beweisprotokoll `blackbox.log`.
- Export aller fertigen Rennen in eine gemeinsame Ergebnisdatei.

### 1.2 Was das System nicht leistet

Folgende Punkte sind **nicht** Bestandteil der Version 0.5.0:

- Keine automatische Hardware-Anbindung (keine Lichtschranke, keine
  Startanlage, keine Zeitimpulse).
- Keine zentrale Datenbank über mehrere Veranstaltungen.
- Keine mobile App und keine Bedienung über Tablet oder Smartphone.
- Keine Benutzerverwaltung mit Rollen und Rechten.
- Kein automatisches Rennende pro Klasse. Das Rennende wird immer vom
  Bediener eingeleitet (siehe Abschnitt 7.7).
- Keine automatische Korrektur um eine Runde nach unten (−1).

### 1.3 Grundprinzip: Excel liefert die Daten, die App misst

Die Excel-Datei ist die **Datenquelle**. Sie enthält Veranstaltung, Rennen,
Starter, Klassen und Startreihen. Ein VBA-Makro exportiert diese Daten in die
Datei `IMPORT.json`. Die Python-App liest ausschließlich diese JSON-Datei und
schreibt ihre Ergebnisse als eigene JSON-Datei zurück. Die Excel-Datei selbst
wird während der Zeitmessung nicht verändert.

Dieses Prinzip hat einen wichtigen Vorteil: Die Zeitmessung ist unabhängig
davon, ob Excel gerade geöffnet ist oder nicht. Für den reinen Rennbetrieb
genügt die `IMPORT.json`.

---

## 2. Systemvoraussetzungen

### 2.1 Technische Voraussetzungen

| Anforderung | Details |
|---|---|
| Betriebssystem | Windows 10 oder Windows 11 |
| Bildschirm | Empfohlen 1920 × 1080 oder größer; Mindestfenster 1280 × 800 |
| Excel | Microsoft Excel wird für die Datenaufbereitung und den Export der `IMPORT.json` benötigt |
| Benutzerrechte | Für systemweite Hotkeys sind **Administrator-Rechte** erforderlich |
| Internet | Nicht erforderlich |
| Programmordner | Lokaler Ordner mit Schreibrechten, z. B. `C:\Wasserski` |
| Laufzeit | Keine Python-Installation nötig, wenn die fertige `.exe` verwendet wird |

### 2.2 Empfehlungen für den Renntag

- Legen Sie den Programmordner **lokal** ab, zum Beispiel `C:\Wasserski`.
  Vermeiden Sie OneDrive-, SharePoint- oder Netzlaufwerke während des Rennens.
  Synchronisationsdienste können Dateien sperren oder verzögert schreiben.
- Starten Sie die Anwendung als Administrator, wenn die Boot-Tasten
  systemweit funktionieren sollen.
- Schließen Sie vor dem Rennstart alle Excel-Dateien, die als Datenquelle
  dienen. Excel darf die Datei nicht gleichzeitig sperren.
- Prüfen Sie vor dem ersten Rennen, ob die Hotkeys reagieren und ob die
  Live-Tabelle die erwarteten Boote anzeigt.
- Exportieren Sie die Ergebnisse **vor dem Schließen der Anwendung**. Die
  fertigen Rennen liegen nur im Arbeitsspeicher und werden nicht dauerhaft
  über einen Programmneustart hinweg gespeichert.

### 2.3 Administrator-Rechte und Hotkeys

Die systemweite Tastaturerfassung verwendet die Windows-Bibliothek
`keyboard`. Diese Bibliothek darf nur mit erhöhten Rechten Tastendrücke
außerhalb des eigenen Fensters abhören.

- **Mit Administrator-Rechten:** Die systemweiten Hotkeys werden beim Start
  automatisch aktiviert. In der Überschrift „Tastaturbedienung (Hotkeys)“
  erscheint der Status **„Hotkeys aktiv“** in Grün.
- **Ohne Administrator-Rechte:** Die Anwendung läuft normal, aber die
  systemweiten Hotkeys bleiben inaktiv. Es erscheint der Hinweis
  **„Hotkeys inaktiv (keine Admin-Rechte)“**. Die Bedienung über die
  virtuelle Tastatur mit der Maus funktioniert weiterhin.

**Start als Administrator:**

1. Im Programmordner mit der rechten Maustaste auf
   `Wasserski-Zeitnehmung.exe` klicken.
2. **„Als Administrator ausführen“** wählen.
3. Die Windows-Abfrage der Benutzerkontensteuerung bestätigen.

In der Entwicklungsumgebung steht zusätzlich
`Start_Zeitnehmung_Admin.cmd` zur Verfügung.

---

## 3. Lieferumfang und Dateien

### 3.1 Programmordner

Im Programmordner liegen nach der Auslieferung mindestens diese Dateien:

| Datei | Zweck | Verhalten |
|---|---|---|
| `Wasserski-Zeitnehmung.exe` | Die Anwendung | Wird gestartet |
| `IMPORT.json` | Renndaten aus Excel | Wird von der App gelesen |
| `app_settings.json` | Sperrzeit und Hotkey-Einstellung | Wird beim ersten Start neben die `.exe` kopiert |
| `blackbox.log` | Beweisprotokoll aller Tastendrücke | Append-only, wird nie geleert |
| `race_state.json` | Zwischenstand für Crash-Recovery | Wird automatisch verwaltet |
| `RESULT_<Zeitstempel>.json` | Ergebnis-Export | Wird bei jedem Export neu erzeugt |
| `gui_startup.log` | Start- und Diagnose-Log | Wird bei jedem Start überschrieben |
| `blackbox_<Zeitstempel>.log` | Archiv einer vollen Blackbox | Entsteht automatisch ab 10 MB |

Optional können im Ordner liegen:

- die Excel-Vorlage, zum Beispiel `Test_StopUhr_V1.xlsm`,
- zusätzliche Ergebnisdateien früherer Rennen,
- diese Anleitung und der Ordner `bilder/` mit Screenshots.

### 3.2 Was darf gelöscht werden?

| Datei | Löschen erlaubt? | Hinweis |
|---|---|---|
| `blackbox.log` | **Nein** | Beweisfunktion. Nach dem Rennen archivieren, nicht löschen. |
| `RESULT_*.json` | Erst nach Sicherung | Ergebnisdateien aufbewahren. |
| `race_state.json` | Ja, wenn kein Rennen läuft | Wird automatisch neu erzeugt. Bei laufendem Rennen führt Löschen zum Verlust der Wiederherstellung. |
| `gui_startup.log` | Ja | Reines Diagnose-Log, wird ohnehin überschrieben. |
| `app_settings.json` | Ja, mit Vorsicht | Beim nächsten Start werden Standardwerte verwendet. |
| `IMPORT.json` | Erst nach dem Rennen | Ohne diese Datei findet die App keine Renndaten. |
| `Wasserski-Zeitnehmung.exe` | Nein | Programmdatei. |

> **Wichtig:** Die Blackbox ist das digitale Gegenstück zu einem
> Zeilendrucker. Sie dokumentiert jeden Tastendruck mit Millisekunden-
> Zeitstempel. Bei Rückfragen oder Streitfällen ist sie die wichtigste
> Beweisquelle.

### 3.3 Bildplatzhalter: Programmordner

> **Bildplatzhalter B13 – Dateien im Programmordner**
>
> Datei: `bilder/13_dateien_programmordner.png`
>
> Motiv: Windows-Explorer mit geöffnetem Programmordner.
>
> Zu sehen: `Wasserski-Zeitnehmung.exe`, `IMPORT.json`,
> `app_settings.json`, `blackbox.log`, `race_state.json`,
> `RESULT_...json`, `gui_startup.log`.
>
> Hinweis: Keine echten Teilnehmerdaten im Screenshot verwenden.

---

## 4. Schnellstart für den Renntag

Diese Kurzanleitung beschreibt den typischen Ablauf. Die Details stehen in
den folgenden Abschnitten.

### 4.1 Vor dem Rennen

1. **Programmordner lokal kopieren**, zum Beispiel nach `C:\Wasserski`.
2. **Excel-Datei öffnen** und die Renndaten prüfen.
3. Das Makro **`ExportExpRangesToJSON`** ausführen. Es erzeugt die Datei
   `IMPORT.json`.
4. Die erzeugte `IMPORT.json` in denselben Ordner wie
   `Wasserski-Zeitnehmung.exe` legen.
5. Die Anwendung **als Administrator** starten.
6. Die gefundene Datenquelle im Dialog **bestätigen**.
7. Im Dropdown das richtige **Rennen** auswählen.
8. Prüfen, ob die Renninformationen und die Starterliste stimmen.

### 4.2 Während des Rennens

1. **START** drücken. Der Countdown für das Startintervall läuft.
2. Nach Ablauf des Countdowns startet das Rennen automatisch.
3. Die Boote der ersten Startreihe starten bei T = 0.
4. Weitere Startreihen starten im Abstand der **Grid Time**.
5. Jede Rundenpassage mit dem Boot-Hotkey erfassen.
6. Die Live-Tabelle und den Ereignis-Feed beobachten.

### 4.3 Nach Ablauf der Renndauer

1. Die Anwendung wechselt in die Endphase. Die verbleibende Zeit steht auf
   `00:00`.
2. Für jede Klasse im Panel **Rennende-Status** den Button **Beenden**
   drücken.
3. Erst danach steht das Ergebnis der Klasse fest.
4. Wenn alle Klassen beendet sind, ist das Rennen abgeschlossen.
5. **Ergebnis exportieren** drücken.
6. Die entstandene Datei `RESULT_<Zeitstempel>.json` sichern.
7. Die `blackbox.log` ebenfalls sichern.

### 4.4 Nach dem Rennen

- Ergebnisdatei und Blackbox auf einen zweiten Datenträger kopieren.
- Die Anwendung erst schließen, wenn alle fertigen Rennen exportiert sind.
- Die Excel-Vorlage und die `IMPORT.json` für die Dokumentation aufbewahren.

### 4.5 Kurzcheckliste

- [ ] Programmordner lokal vorhanden
- [ ] Excel-Daten vollständig und plausibel
- [ ] `IMPORT.json` neben der `.exe`
- [ ] Anwendung als Administrator gestartet
- [ ] Datenquelle bestätigt
- [ ] Rennen und Klassen geprüft
- [ ] Hotkey-Status grün
- [ ] Countdown und Startreihen geprüft
- [ ] Alle Klassen beendet
- [ ] Ergebnis exportiert
- [ ] Blackbox gesichert

---

## 5. Die Oberfläche im Detail

Die Anwendung verwendet ein dunkles, kontrastreiches Layout. Es ist in vier
Bereiche gegliedert:

```text
+-----------------------------------------------------------------------+
| 1. Kopfbereich: Titel, Version, Datenquelle, Aktionsbuttons           |
+-----------------------------------+-----------------------------------+
| 2. Renninformationen              | 2. Countdown-Anzeige              |
|                                   |                                   |
| 3. Ereignis-Feed (Logs)           | 3. Tastaturbedienung (Hotkeys)    |
|                                   |                                   |
| 4. Live-Tabelle (Rangliste)       | 4. Rennende-Status                |
|                                   |                                   |
|                                   | 4. Manuell +1 Runde               |
+-----------------------------------+-----------------------------------+
| Fußzeile: Datenquelle und Branding                                    |
+-----------------------------------------------------------------------+
```

> **Bildplatzhalter B1 – Hauptfenster gesamt**
>
> Datei: `bilder/01_hauptfenster.png`
>
> Motiv: Vollständiges Anwendungsfenster nach dem Laden eines Testrennens.
>
> Zu sehen: Kopfbereich, Renninformationen, Countdown, Live-Tabelle,
> Hotkey-Panel, Ereignis-Feed, Rennende-Status und Fußzeile.
>
> Hinweis: Screenshot mit einem neutralen Testrennen, keine echten
> Teilnehmerdaten.

### 5.1 Kopfbereich

Der Kopfbereich enthält:

- den Titel **„Zeitnehmungs-System Wasserski-Racing“**,
- die Versionsnummer, zum Beispiel `v0.5.0`,
- das Branding **EDV Engl Roman** mit Webadresse,
- die Anzeige **„Datenquelle: …“**,
- den Button **„Daten aktualisieren“**,
- den Button **„Ergebnis exportieren“**,
- ein Statusfeld für den letzten Export.

**Datenquelle:** Zeigt an, woher die aktuellen Renndaten stammen, zum
Beispiel `JSON: IMPORT.json (auto)`, `Excel: Test_StopUhr_V1.xlsm` oder
`Crash-Recovery (race_state.json)`.

**Daten aktualisieren:** Lädt die Renndaten aus derselben Quelle erneut.
Der Button ist nur verfügbar, solange kein Rennen läuft (Phase `RESET`).
Während eines laufenden Rennens ist er deaktiviert. Nach einem Reset wird er
wieder aktiv.

**Ergebnis exportieren:** Schreibt alle fertigen Rennen in eine neue
Ergebnisdatei. Der Button ist unabhängig vom aktuell gewählten Rennen
verfügbar. Einzelheiten siehe Abschnitt 11.

> **Bildplatzhalter B2 – Kopfbereich**
>
> Datei: `bilder/02_kopfbereich.png`
>
> Motiv: Kopfbereich mit Titel, Version, Datenquelle und beiden Buttons.
>
> Zu sehen: Datenquellen-Anzeige, „Daten aktualisieren“,
> „Ergebnis exportieren“ und ein grüner Export-Status.

### 5.2 Renninformationen

Das Panel **Renninformationen** zeigt eine reine Übersicht:

| Feld | Bedeutung |
|---|---|
| Event | Name der Veranstaltung |
| Datum | Veranstaltungsdatum |
| Rennen | Rennnummer und die enthaltenen Klassen |
| Länge R1 | Streckenlänge der ersten Runde in Metern |
| Länge R2+ | Streckenlänge aller weiteren Runden in Metern |

Die Werte kommen aus `IMPORT.json`. Wenn ein Wert fehlt, erscheint `–`.

> **Bildplatzhalter B3 – Renninformationen**
>
> Datei: `bilder/03_renninformationen.png`
>
> Motiv: Panel „Renninformationen“ mit ausgefüllten Beispielwerten.

### 5.3 Countdown-Anzeige

Das Panel **Countdown-Anzeige** ist die zentrale Startsteuerung. Es enthält:

- das Dropdown **Rennen N (Klassen)** zur Rennen-Auswahl,
- die linke Kachel **VORSTART** beziehungsweise **START REIHE N** und nach
  dem Start aller Reihen **RENNDAUER**,
- die rechte Kachel **VERBLEIBENDE ZEIT**,
- den Button **START**,
- die Buttons **PAUSE/WEITER** und **NEUSTART**.

#### Rennen-Auswahl

Das Dropdown listet alle Rennen aus `IMPORT.json` auf. Die Auswahl wechselt
das geladene Rennen und befüllt alle Panels neu. Während ein Rennen läuft,
ist das Dropdown deaktiviert. Es wird wieder bedienbar, wenn das Rennen
zurückgesetzt ist oder alle Boote fertig sind.

#### VORSTART-Kachel

Vor dem Rennstart zeigt die linke Kachel den Countdown des
**Startintervalls** in Rot. Die Anzeige hat das Format `HH:MM:SS`. Der
Fortschrittsbalken läuft mit.

Nach dem Rennstart wechselt dieselbe Kachel auf **„START REIHE N“** und
zeigt in Gelb die Zeit bis zum Start der nächsten Startreihe. Es gibt
bewusst **keine zweite Countdown-Kachel**; der Startreihen-Countdown
ersetzt den Vorstart-Countdown.

Sobald **alle Startreihen gestartet** sind, hat der Startreihen-Countdown
keine Bedeutung mehr. Die linke Kachel zeigt dann **„RENNDAUER:“** und
zählt in Weiß die vergangene Zeit seit dem ersten Start (Startreihe 1)
mit. Nach dem Rennende bleibt der Wert beim letzten Zieleinlauf stehen.
Der blaue Fortschrittsbalken zeigt den Anteil der geplanten Renndauer.

#### VERBLEIBENDE ZEIT

Die rechte Kachel zeigt in Grün die verbleibende Renndauer. Das Format ist
`MM:SS`, ab einer Stunde `HH:MM:SS`. Im Zustand `RESET` (nach **NEUSTART**
oder nach dem Laden eines Rennens) steht sie auf `00:00`.

#### START

Der Button **START** startet den Countdown. Vorher prüft die Anwendung die
Renndaten. Bei Fehlern erscheint ein Dialog **„Rennen nicht freigegeben“**
mit einer Liste der Probleme. Erst nach erfolgreicher Prüfung beginnt der
Countdown.

Bei einem bereits beendeten Rennen ist **START** grau und nicht bedienbar.
Das Rennen kann dann nur angesehen oder exportiert werden.

#### PAUSE/WEITER

Der Button unterbricht den Countdown und setzt ihn exakt an derselben Stelle
fort. Er ist nur im Vorstart bedienbar. Während des Rennens ist er
deaktiviert.

#### NEUSTART

Der Button setzt das aktuelle Rennen zurück. Vorher erscheint eine
Sicherheitsabfrage:

> „Sind Sie sicher, dass Sie das Rennen neu starten möchten? Alle bisherigen
> Ereignisse und Runden gehen verloren.“

Nach Bestätigung werden Runden, Ereignisse und Sperrzeiten des aktuellen
Rennens gelöscht und der Crash-Recovery-State entfernt. Das Rennen steht
wieder auf `RESET` und kann neu gestartet werden.

> **Bildplatzhalter B4 – Vorstart-Countdown**
>
> Datei: `bilder/04_countdown_vorstart.png`
>
> Motiv: Countdown-Panel während des Vorstarts.
>
> Zu sehen: rote Kachel „VORSTART:“ mit laufender Zeit, grüne Kachel
> „VERBLEIBENDE ZEIT:“, Button PAUSE und Button NEUSTART.

> **Bildplatzhalter B5 – Startreihen-Countdown**
>
> Datei: `bilder/05_startreihe_countdown.png`
>
> Motiv: Countdown-Panel nach dem Rennstart.
>
> Zu sehen: gelbe Kachel „START REIHE 2:“ mit Restzeit bis zur zweiten
> Startreihe, grüne Kachel „VERBLEIBENDE ZEIT:“.

### 5.4 Live-Tabelle

Die Live-Tabelle zeigt alle Boote des aktuellen Rennens. Die Spalten sind:

| Spalte | Bedeutung |
|---|---|
| `#` | Laufende Platznummer in der Live-Reihenfolge |
| `Runner` | Boot-Nummer und Team (ohne Klasse); zu lange Namen werden gekürzt |
| `Klasse` | Rennklasse des Boots |
| `Boot` | Boot-Key (Hotkey-Buchstabe) |
| `Reihe` | Startreihe |
| `Runden` | Anzahl der vollständig abgeschlossenen Runden |
| `Letzte Runde` | Dauer der zuletzt abgeschlossenen Runde |
| `Geschw.` | Geschwindigkeit: km/h letzte Runde / km/h gesamt |
| `Gesamtzeit` | Summe aller Rundenzeiten |
| `Status` | `WARTET`, `SPERRZEIT (Ns)`, `GESTARTET` oder `FERTIG` |

#### Statusspalte und Rennende-Ampel

Nach Ablauf der Renndauer erscheint in der Statusspalte links neben dem
Statustext ein Punkt:

- **grün**: Das Boot hatte nach dem Rennende mindestens eine echte
  Zielpassage.
- **rot**: Das Boot war seit dem Rennende noch nicht im Ziel.

Passend zum Punkt wird im Panel **Tastaturbedienung** die klickbare
Hotkey-Taste des Boots rot beschriftet, solange der Punkt rot ist. Sobald
das Boot im Ziel ist (grüner Punkt), erscheint die Schrift wieder weiß. Die
Taste bleibt dabei grün hinterlegt und klickbar.

Vor Rennende bleibt die Statusspalte ohne Punkt. Maßgeblich sind
ausschließlich echte Zielpassagen (Hotkeys); eine manuelle **+1 Runde**
macht den Punkt nicht grün, weil ihr Zeitstempel die Klickzeit und keine
Zielpassage ist.

#### Sortierung und Platznummer

Die Live-Tabelle sortiert nach:

1. Rundenzahl absteigend,
2. bei gleicher Rundenzahl nach Gesamtzeit aufsteigend.

Die Platznummer `#` ist eine **laufende Gesamtreihenfolge über alle Boote
des Rennens**. Sie ist eine Orientierungshilfe während des Rennens. Die
**endgültige Platzierung wird pro Klasse** vergeben und kann daher von der
Live-Reihenfolge abweichen. Beispiel: Ein Boot kann in der Live-Tabelle
insgesamt auf Platz 4 stehen, in seiner Klasse aber Platz 1 belegen.

Der jeweils Führende der Live-Reihenfolge wird grün hinterlegt.

#### Runner-Spalte

Die Spalte `Runner` zeigt Boot-Nummer und Team, **nicht** die Klasse – die
steht in der eigenen Spalte `Klasse`. Sie hat eine feste Breite; Namen, die
länger als 18 Zeichen sind, werden mit `…` abgeschnitten. Die vollständigen
Daten stehen weiterhin in `IMPORT.json` und im Export.

#### Geschwindigkeit

Die Spalte `Geschw.` zeigt zwei Werte, getrennt durch `/`:

- **km/h letzte Runde:** Strecke der letzten Runde geteilt durch die
  Rundenzeit.
- **km/h gesamt:** Gesamtstrecke geteilt durch die Zeit vom individuellen
  Start bis zur letzten Passage.

Die erste Runde verwendet die Länge `Länge R1`, alle weiteren Runden die
Länge `Länge R2+`. Wenn noch keine Runde abgeschlossen ist, erscheint
`–/–`.

> **Bildplatzhalter B6 – Live-Tabelle**
>
> Datei: `bilder/06_live_tabelle.png`
>
> Motiv: Live-Tabelle mit mehreren Booten, Runden, Geschwindigkeiten und
> Statusanzeigen.
>
> Zu sehen: grün hinterlegter Führender, Spalte „Geschw.“ mit Werten wie
> `58.3/56.1`, Status `WARTET`, `GESTARTET`, `SPERRZEIT` und `FERTIG`.

### 5.5 Tastaturbedienung (Hotkeys)

Das Panel zeigt die Buchstaben **A bis Z** als virtuelle Tastatur in drei
Reihen. Jeder Buchstabe entspricht einem Boot-Key.

Die Farben bedeuten:

| Darstellung | Bedeutung |
|---|---|
| Grün | Boot ist gestartet; der Hotkey ist aktiv |
| Grau, bedienbar wirkend | Boot ist im Rennen vorhanden, aber noch nicht gestartet |
| Grau, inaktiv | Boot gehört zu einer bereits beendeten Klasse |
| Dunkel | Kein Boot ist diesem Buchstaben zugeordnet |

Ein Klick auf einen grünen Buchstaben löst dieselbe Passage aus wie ein
echter Tastendruck. Das ist nützlich, wenn die systemweiten Hotkeys nicht
verfügbar sind.

In der Überschrift steht der Status der systemweiten Hotkeys:

- `Hotkeys aktiv` in Grün,
- `Hotkeys inaktiv (keine Admin-Rechte)` in Grau,
- `Hotkeys inaktiv (Admin, aber deaktiviert)` in Grau.

> **Bildplatzhalter B7 – Hotkey-Panel**
>
> Datei: `bilder/07_hotkeys.png`
>
> Motiv: Virtuelle Tastatur A–Z mit unterschiedlichen Zuständen.
>
> Zu sehen: grüne gestartete Boote, graue noch nicht gestartete Boote,
> dunkle nicht belegte Tasten und der Hotkey-Status in der Überschrift.

### 5.6 Ereignis-Feed (Logs)

Der Ereignis-Feed zeigt die wichtigsten Ereignisse des laufenden Rennens in
zeitlicher Reihenfolge:

```text
14:30:00 Rennen gestartet
14:30:00 Startreihe 1 gestartet
14:30:30 Startreihe 2 gestartet
14:31:05 Boot A Passage
14:31:08 Boot B UNGÜLTIG (Sperrzeit)
```

Ungültige Eingaben werden rot dargestellt. Der Feed zeigt etwa sieben Zeilen
gleichzeitig und kann gescrollt werden.

Der Ereignis-Feed ist eine **Bedieneranzeige**, nicht das Beweisprotokoll.
Die vollständige, unveränderliche Aufzeichnung steht in `blackbox.log`.

> **Bildplatzhalter B8 – Ereignis-Feed**
>
> Datei: `bilder/08_ereignisfeed.png`
>
> Motiv: Ereignis-Feed mit gültigen und ungültigen Einträgen.
>
> Zu sehen: Zeitstempel, Meldungen zu Start, Startreihen, Passagen und eine
> rote Zeile für eine Sperrzeit.

### 5.7 Rennende-Status

Das Panel **Rennende-Status** zeigt für jede Klasse eine Zeile:

```text
Klasse Herren:   WARTEND   [Beenden]
Klasse Junioren: FERTIG    [Beenden]
```

| Anzeige | Bedeutung |
|---|---|
| `WARTEND` in Gelb | Klasse ist noch offen |
| `FERTIG` in Grün | Klasse wurde beendet, Ergebnis steht fest |

Der Button **Beenden** ist:

- **sichtbar**, aber **grau und inaktiv**, solange die Renndauer noch läuft,
- **gelb und aktiv**, sobald die Renndauer abgelaufen ist und die Klasse noch
  nicht beendet wurde,
- **grau und inaktiv**, sobald die Klasse beendet ist.

Wenn keine Klassen geladen sind, erscheint der Hinweis
**„Keine Klassen geladen“**. Bei geladenen Klassen entsteht keine unnötige
Leerzeile.

> **Bildplatzhalter B9 – Rennende-Status**
>
> Datei: `bilder/09_rennende_status.png`
>
> Motiv: Rennende-Status mit mehreren Klassen.
>
> Zu sehen: eine Klasse `WARTEND` mit aktivem gelbem Beenden-Button, eine
> Klasse `FERTIG` mit grauem Button.

**Zähler und Buttonfarbe (2026-11-10):**

Nach Ablauf der Renndauer zeigt jede Klasse im Rennende-Status den Zähler
`fertig/gesamt` (z. B. `3/4`). Der **Beenden**-Button ist grün, wenn alle
Boote der Klasse nach dem Rennende im Ziel waren, sonst rot. Er bleibt in
beiden Fällen klickbar – die Entscheidung liegt beim Bediener. Die Punkte
je Boot stehen in der **Statusspalte der Live-Tabelle** (siehe 5.4).

### 5.8 Manuell +1 Runde

Das Panel **Manuell +1 Runde** enthält:

- ein Dropdown mit allen Booten des Rennens,
- den Button **+1 RUNDE**.

Die manuelle Korrektur fügt dem gewählten Boot eine zusätzliche Runde hinzu.
Sie ist nur während eines laufenden Rennens sinnvoll. Einzelheiten siehe
Abschnitt 9.3.

> **Bildplatzhalter B10 – Manuelle Korrektur**
>
> Datei: `bilder/10_manuell_plus1.png`
>
> Motiv: Panel „Manuell +1 Runde“ mit geöffnetem Boot-Dropdown.
>
> Zu sehen: Boot-Auswahl und blauer Button „+1 RUNDE“.

### 5.9 Fußzeile

Die Fußzeile zeigt links die aktuelle Datenquelle und Rennnummer, rechts das
Branding:

```text
Datenquelle: JSON: IMPORT.json (auto) (Rennen 1)
EDV Engl Roman | www.engl.biz | edv@engl.biz
```

### 5.10 Farben und ihre Bedeutung

| Farbe | Bedeutung in der Oberfläche |
|---|---|
| Grün | Aktiv, gestartet, FERTIG, Erfolg, Führender |
| Gelb | Wartend, Startreihen-Countdown, Beenden-Button aktiv |
| Rot | Vorstart-Countdown, Sperrzeit, Fehler, Warnung |
| Blau | Aktionen, Fortschrittsbalken, Export |
| Grau | Inaktiv, deaktiviert, keine Zuordnung |

---

## 6. Renndaten in Excel vorbereiten

### 6.1 Grundaufbau

Die Excel-Vorlage enthält benannte Bereiche (Named Ranges). Die Namen
beginnen mit einem Präfix:

| Präfix | Richtung | Bedeutung |
|---|---|---|
| `_EXP_` | Excel → JSON | Daten, die die App aus Excel liest |
| `_IMP_` | JSON → Excel | Daten, die optional in Excel zurückgeschrieben werden |

Die wichtigsten Export-Bereiche:

| Named Range | Inhalt |
|---|---|
| `_EXP_INFO` | Veranstaltung, Datum, Organisator |
| `_EXP_STARTER` | Starterliste mit Booten, Fahrern, Klassen, Rennen und Startreihen |
| `_EXP_RACES` | Rennkonfiguration mit Renndauer, Startintervall, Grid Time und Rundenlängen |

Die Import-Bereiche:

| Named Range | Inhalt |
|---|---|
| `_IMP_LOG` | Vollständiges Renn-Log |
| `_IMP_RESULTS` | Ergebnisse mit Platzierungen, Runden und Zeiten |

### 6.2 Rennparameter und Einheiten

Die folgenden Werte sind **Pflichtfelder pro Rennen**:

| Parameter | Excel-Feld | Einheit | Bedeutung |
|---|---|---|---|
| Rennnummer | `FLD_RACE` | Zahl | Eindeutige Nummer des Rennens |
| Renndauer | `FLD_RACEDUR` | Minuten | Gesamtdauer des Rennens |
| Startintervall | `FLD_STARTINT` | Sekunden | Vorlaufzeit bis zum Rennstart (Countdown) |
| Grid Time | `FLD_GRIDTIME` | Sekunden | Zeit zwischen den Startreihen |
| Länge Runde 1 | `FLD_ROUND1` | **Kilometer** | Streckenlänge der ersten Runde |
| Länge Standard-Runde | `FLD_ROUND` | **Kilometer** | Streckenlänge aller weiteren Runden |

> **Wichtig – Einheiten der Rundenlängen**
>
> In der aktuellen Excel-Vorlage werden die Rundenlängen in **Kilometern**
> gepflegt, zum Beispiel `2` für 2 km und `3,5` für 3,5 km. Die Anwendung
> rechnet diese Werte in Meter um und zeigt sie in der Oberfläche als
> `2000 m` beziehungsweise `3500 m` an.
>
> Tragen Sie in Excel **keine Meterwerte** ein. Aus `2000` würden sonst
> 2.000.000 Meter. Im Zweifel die erzeugte `IMPORT.json` prüfen: Dort
> stehen die Kilometerwerte.

Das Feld `FLD_STARTTIME` wird von der aktuellen Vorlage noch exportiert,
aber von der Anwendung nicht verwendet.

### 6.3 Starterfelder

| Excel-Feld | Bedeutung | Pflicht |
|---|---|---|
| `FLD_BOATNR` | Boot-Nummer | Ja |
| `FLD_SKIER` | Fahrer-Name | Ja |
| `FLD_CLASS` | Rennklasse | Ja |
| `FLD_RACE` | Rennnummer | Ja |
| `FLD_LINE` | Startreihe (1, 2, 3, …) | Ja, muss größer als 0 sein |
| `FLD_HOTKEY` | Boot-Key A–Z | Nein, wird sonst automatisch vergeben |
| `FLD_TEAM` | Team | Nein |
| `FLD_DRIVER` | Fahrer des Boots | Nein |
| `FLD_OBSERVER` | Beobachter | Nein |
| `FLC_CLUB` | Verein | Nein |
| `FLD_FED` | Verband | Nein |

**Automatische Boot-Keys:**

- Fehlt `FLD_HOTKEY`, vergibt die Anwendung beim Laden automatisch den
  nächsten freien Buchstaben A–Z innerhalb des Rennens.
- Bereits in Excel vergebene Keys haben Vorrang und werden nicht
  überschrieben.
- Doppelte Keys innerhalb desselben Rennens werden beim Laden automatisch
  auf den nächsten freien Buchstaben umgesetzt. Im Log erscheint eine
  Warnung.
- Pro Rennen sind maximal 26 Boote möglich, weil nur die Buchstaben A–Z zur
  Verfügung stehen.
- Derselbe Boot-Key darf in **verschiedenen Rennen** verwendet werden.

### 6.4 Export nach `IMPORT.json`

1. Excel-Datei öffnen.
2. Makros erlauben. Bei Bedarf die Datei als vertrauenswürdigen Speicherort
   hinzufügen.
3. Das Makro **`ExportExpRangesToJSON`** ausführen. Es liegt in der
   aktuellen Vorlage im Modul `mdl_Engl_Export`.
4. Die Erfolgsmeldung bestätigen.
5. Die erzeugte `IMPORT.json` neben `Wasserski-Zeitnehmung.exe` legen.
6. Die Anwendung starten oder – wenn sie bereits läuft und kein Rennen
   aktiv ist – **Daten aktualisieren** drücken.

> **Bildplatzhalter B11 – Excel-Exportmakro**
>
> Datei: `bilder/11_excel_export_makro.png`
>
> Motiv: Excel-Vorlage mit geöffnetem Makro-Dialog oder Entwicklerbereich.
>
> Zu sehen: Makro `ExportExpRangesToJSON` und die Erfolgsmeldung nach dem
> Export.

### 6.5 Bekannte Einschränkung: direkter Excel-Start

Die Anwendung kann eine Excel-Datei grundsätzlich über den Parameter
`--excel` öffnen und das VBA-Makro selbst aufrufen. In Version 0.5.0 ist
dieser Weg jedoch **noch nicht freigegeben**, weil der Python-Aufruf den
alten Modulnamen `mdlEngl` verwendet, die aktuelle Vorlage aber
`mdl_Engl_Export` nutzt.

**Aktueller verbindlicher Weg:**

1. `IMPORT.json` in Excel manuell über `ExportExpRangesToJSON` erzeugen.
2. `IMPORT.json` neben die `.exe` legen.
3. Die Anwendung liest die JSON-Datei.

Der offene Punkt ist in Abschnitt 17 dokumentiert.

---

## 7. Rennablauf Schritt für Schritt

### 7.1 Datenquelle beim Start

Die Anwendung sucht beim Start in einer festen Reihenfolge nach Renndaten:

| Reihenfolge | Quelle | Verhalten |
|---|---|---|
| 1 | `race_state.json` | Crash-Recovery. Der Zustand wird **ohne Nachfrage** übernommen, sofern er gültig ist. |
| 2 | `--json <Datei>` | Die angegebene `IMPORT.json` wird direkt geladen. |
| 3 | `--excel <Datei>` | Die Excel-Datei wird geladen. Derzeit wegen des Modulnamens eingeschränkt. |
| 4 | Testdaten | Nur für automatisierte Tests, nicht für den Rennbetrieb. |
| 5 | Auto-Suche im Programmordner | Zuerst `IMPORT.json`, dann `*.xlsm`, dann `*.xlsx`. Die gefundene Datei muss bestätigt werden. |
| 6 | Nichts gefunden | Fehlermeldung „Keine Renndaten gefunden“. |

Die Auto-Suche zeigt einen Bestätigungsdialog:

> „Gefundene Datenquelle: … Möchten Sie diese Datei verwenden?“

Bei **Ja** wird die Datei geladen. Bei **Nein** startet die Anwendung nicht
und zeigt einen Hinweis, dass die Datenquelle nicht bestätigt wurde.

Bei einer Crash-Recovery erscheint **kein** Bestätigungsdialog. Das ist
Absicht: Beim Rennen zählt jede Sekunde. Die Prüfung, ob der Zustand zur
Datenquelle passt, erfolgt automatisch (siehe Abschnitt 10).

> **Bildplatzhalter B14 – Fehlermeldung bei fehlenden Renndaten**
>
> Datei: `bilder/14_fehlerdialog.png`
>
> Motiv: Fehlerdialog „Keine Renndaten gefunden“.
>
> Zu sehen: Meldung mit Suchordner und Hinweis, `IMPORT.json` oder eine
> Excel-Datei in den Programmordner zu legen.

### 7.2 Rennen auswählen

1. Im Dropdown **Rennen N (Klassen)** das gewünschte Rennen wählen.
2. Das Panel **Renninformationen** prüfen:
   - Event und Datum,
   - Rennnummer und Klassen,
   - Längen der ersten und der weiteren Runden.
3. Die Starter in der Live-Tabelle prüfen:
   - Sind alle Boote vorhanden?
   - Stimmen Klasse und Startreihe?
   - Sind die Boot-Keys plausibel?

Die Live-Tabelle zeigt beim Laden alle Boote mit `0` Runden. Die Startreihen
sind noch nicht gestartet; der Status ist `WARTET`, sobald die Startzeit in
der Zukunft liegt.

### 7.3 Rennen freigeben und starten

1. **START** drücken.
2. Die Anwendung prüft die Daten des aktuellen Rennens.
3. Bei Fehlern erscheint **„Rennen nicht freigegeben“**. Die Meldung nennt
   die betroffenen Felder.
4. Bei erfolgreicher Prüfung beginnt der Countdown.
5. Die Kachel **VORSTART** zählt herunter.
6. Bei `00:00:00` startet das Rennen automatisch.

Es gibt **kein separates Startsignal**. Der Countdown selbst startet das
Rennen. Das ist eine bewusste Entscheidung (Q8, 2026-08-14).

#### Typische Validierungsfehler

| Meldung | Bedeutung / Lösung |
|---|---|
| `Event-Titel fehlt` | In `_EXP_INFO` den Veranstaltungsnamen eintragen. |
| `Keine Rennkonfiguration vorhanden` | In `_EXP_RACES` mindestens ein Rennen pflegen. |
| `Rennen N: Renndauer muss > 0 sein` | `FLD_RACEDUR` ist 0 oder leer. |
| `Rennen N: Startintervall (Vorlaufzeit) muss > 0 sein` | `FLD_STARTINT` ist 0 oder leer. |
| `Rennen N: Grid Time (Zeit zwischen Startreihen) muss > 0 sein` | `FLD_GRIDTIME` ist 0 oder leer. |
| `Rennen N: Länge Runde 1 muss > 0 sein` | `FLD_ROUND1` ist 0 oder leer. |
| `Rennen N: Länge Standard-Runde muss > 0 sein` | `FLD_ROUND` ist 0 oder leer. |
| `Rennen N: Keine Starter` | Kein Starter ist diesem Rennen zugeordnet. |
| `Boot …: Keine Klasse zugewiesen` | `FLD_CLASS` fehlt. |
| `Boot …: Startreihe muss > 0 sein` | `FLD_LINE` fehlt oder ist 0. |
| `Doppelter Boot-Key …` | Zwei Boote haben denselben Key im selben Rennen. |
| `Ungültiger Boot-Key …` | Der Key ist kein einzelner Buchstabe A–Z. |

Die Prüfung betrifft nur das aktuell ausgewählte Rennen. Fehler in anderen
Rennen blockieren den Start nicht.

### 7.4 Countdown und Rennstart

- Der Countdown verwendet das **Startintervall** des Rennens in Sekunden.
- **PAUSE** friert die Restzeit ein.
- **WEITER** setzt den Countdown mit der eingefrorenen Restzeit fort.
- **NEUSTART** bricht ab und setzt das Rennen zurück.
- Nach Ablauf des Countdowns wird das Ereignis `START` protokolliert.
- Der offizielle Rennstart ist der Zeitpunkt, an dem der Countdown 0
  erreicht. Die Renndauer wird ab diesem Zeitpunkt gerechnet.

### 7.5 Startreihen und Grid Time

Jedes Boot gehört zu einer Startreihe (`FLD_LINE`). Die Startreihen starten
zeitversetzt:

| Startreihe | Individueller Startzeitpunkt |
|---|---|
| Reihe 1 | Rennstart + 0 × Grid Time |
| Reihe 2 | Rennstart + 1 × Grid Time |
| Reihe 3 | Rennstart + 2 × Grid Time |
| … | … |

**Beispiel:** Startintervall 10 Sekunden, Grid Time 30 Sekunden.

- Countdown läuft 10 Sekunden.
- Bei `00:00:00` startet das Rennen und Startreihe 1.
- 30 Sekunden später startet Startreihe 2.
- 60 Sekunden nach dem Rennstart startet Startreihe 3.

Beim Start jeder Reihe wird ein `STARTLINE`-Ereignis protokolliert. In der
VORSTART-Kachel erscheint der Countdown bis zur nächsten Reihe. Sind alle
Reihen gestartet, zeigt dieselbe Kachel stattdessen die laufende Renndauer
(`RENNDAUER:`).

**Wichtig für die Wertung:** Die erste Runde eines Boots wird ab dem
**individuellen Startzeitpunkt seiner Startreihe** gemessen, nicht ab dem
globalen Rennstart. Eine Passage vor dem individuellen Start ist ungültig.

### 7.6 Rundenpassagen erfassen

Eine Passage wird erfasst durch:

- den systemweiten Hotkey des Bootes (Buchstabe A–Z),
- den Zahlenblock 1–0 als Alias für die ersten zehn Boot-Keys (sofern
  systemweite Hotkeys aktiv sind),
- einen Klick auf den grünen Buchstaben in der virtuellen Tastatur.

Eine Passage wird nur gewertet, wenn alle Bedingungen erfüllt sind:

1. Das Rennen läuft (`ACTIVE` oder `FINISHING`).
2. Die Startreihe des Boots ist bereits gestartet.
3. Das Boot ist noch nicht fertig.
4. Die Sperrzeit des Boots ist abgelaufen.

Andernfalls wird ein `INVALID`-Ereignis erzeugt. Es wird protokolliert,
aber nicht als Runde gewertet.

#### Rundenberechnung

- **Erste Runde:** vom individuellen Startzeitpunkt des Boots bis zur ersten
  Passage.
- **Weitere Runden:** von der vorherigen Passage bis zur aktuellen Passage.
- **Gesamtzeit:** Summe aller Rundenzeiten. Die Wartezeit vor dem
  individuellen Start zählt nicht mit.
- **Letzte Runde:** Dauer der zuletzt abgeschlossenen Runde.
- **Beste Runde:** schnellste Runde des Boots; wird im Export ausgegeben.

### 7.7 Rennende und Klassen beenden

Nach Ablauf der Renndauer passiert **nichts automatisch**. Die Anwendung
wechselt in die Phase `FINISHING`. Die verbleibende Zeit steht auf `00:00`.

So beenden Sie das Rennen:

1. Im Panel **Rennende-Status** die erste offene Klasse suchen
   (Anzeige `WARTEND`).
2. **Beenden** drücken. Der Button ist jetzt gelb und aktiv.
3. Die Anwendung markiert **alle Boote dieser Klasse** als fertig.
4. Für jedes Boot wird ein `FINISH`-Ereignis protokolliert.
5. Die Klasse wechselt auf `FERTIG`.
6. Die Hotkeys der Klasse werden grau und inaktiv.
7. Die Platzierung der Klasse steht fest.
8. Für die nächste Klasse wiederholen.
9. Wenn alle Klassen `FERTIG` sind, wechselt das Rennen auf `FINISHED`.

**Warum wird pro Klasse beendet?**

Die Klassen können unterschiedliche Renndauern und Teilnehmerzahlen haben.
Der Bediener entscheidet bewusst, wann eine Klasse abgeschlossen ist. Die
frühere automatische „Letzte Runde“-Logik wurde entfernt
(Kundenentscheidung 2026-09-03).

**Was passiert mit Booten ohne Runde?**

Ein Boot, das keine Runde abgeschlossen hat, erhält im Ergebnis Platz 0 und
wird am Ende der Klasse geführt. Es ist kein gültiger Platzierungsrang.

**Ampel als Kontrolle vor dem Beenden (2026-11-10):**

Vor dem Klick auf **Beenden** prüfen Sie die Punkte in der Statusspalte der
Live-Tabelle. Grün bedeutet: Das Boot ist nach dem Rennende noch im Ziel
gewesen. Rot bedeutet: Es fehlt noch eine Passage (oder das Boot ist
ausgefallen) – die zugehörige Hotkey-Taste im Panel Tastaturbedienung ist
dann ebenfalls rot beschriftet. Beenden Sie die Klasse erst, wenn alle Boote
der Klasse grün sind. Der Button bleibt auch bei Rot klickbar – die App
verhindert die Beendigung bewusst nicht.

### 7.8 Rennen wechseln

Nach dem Beenden eines Rennens können Sie ein anderes Rennen wählen.

- Ein bereits beendetes Rennen bleibt **im Arbeitsspeicher** erhalten.
- Beim Zurückwechseln werden Runden, Zeiten, Platzierungen, Klassenstatus
  und das Renn-Log wiederhergestellt.
- Der **START**-Button ist bei einem bereits beendeten Rennen grau und
  inaktiv. Das Rennen kann nur angesehen oder exportiert werden.
- Ein frisch geladenes, noch nicht beendetes Rennen steht auf `RESET` und
  kann gestartet werden.

> **Wichtig:** Die fertigen Rennen liegen nur im Arbeitsspeicher. Sie werden
> **nicht** über einen Programmneustart hinweg gespeichert. Exportieren Sie
> deshalb alle fertigen Rennen, bevor Sie die Anwendung schließen.

### 7.9 Daten aktualisieren

Der Button **Daten aktualisieren** lädt die Renndaten aus derselben Quelle
neu. Voraussetzungen:

- Es läuft kein Rennen (Phase `RESET`).
- Es gibt eine Datei-Quelle (`IMPORT.json` oder Excel).

Nach dem Neuladen werden Rennen-Auswahl, Panels und Engine mit den neuen
Daten befüllt. Änderungen an `IMPORT.json` werden also erst nach dem
Aktualisieren wirksam.

### 7.10 Neustart und Reset

Der Button **NEUSTART** im Countdown-Panel setzt das aktuelle Rennen zurück:

- Runden und Ereignisse des aktuellen Rennens werden gelöscht.
- Alle Boote beginnen wieder bei 0 Runden.
- Klassen stehen wieder auf `WARTEND`.
- Der Crash-Recovery-State wird gelöscht.
- Die Anwendung zeigt wieder den **START**-Button.

Bereits beendete **andere** Rennen bleiben im Arbeitsspeicher erhalten,
solange die Anwendung läuft.

---

## 8. Anzeigen richtig lesen

### 8.1 Rennphasen

Die Anwendung kennt fünf Phasen:

| Phase | Bedeutung | Typische Anzeige |
|---|---|---|
| `RESET` | Rennen geladen, noch nicht gestartet | START-Button sichtbar, rechte Uhr `00:00` |
| `PRESTART` | Countdown läuft | VORSTART-Kachel rot |
| `ACTIVE` | Rennen läuft | VERBLEIBENDE ZEIT grün, Startreihen-Countdown gelb, danach RENNDAUER weiß |
| `FINISHING` | Renndauer abgelaufen, Klassen offen | Beenden-Buttons gelb |
| `FINISHED` | Alle Klassen beendet | Alle Klassen `FERTIG` |

### 8.2 Statuswerte in der Live-Tabelle

| Status | Bedeutung |
|---|---|
| `WARTET` | Die Startreihe des Boots ist noch nicht gestartet. |
| `SPERRZEIT (Ns)` | Die Sperrzeit läuft noch; die nächste Eingabe wird verworfen. |
| `GESTARTET` | Das Boot hat mindestens eine Runde abgeschlossen. |
| `FERTIG` | Die Klasse des Boots wurde beendet. |
| leer | Das Boot ist gestartet, hat aber noch keine Runde abgeschlossen. |

### 8.3 Zeitformate

| Anzeige | Format | Beispiel |
|---|---|---|
| Vorstart-Countdown | `HH:MM:SS` | `00:00:10` |
| Startreihen-Countdown | `HH:MM:SS` | `00:00:23` |
| Renndauer (ab erstem Start) | `MM:SS` oder `HH:MM:SS` | `14:32` |
| Verbleibende Renndauer | `MM:SS` oder `HH:MM:SS` | `01:45` |
| Rundenzeit in der Live-Tabelle | `MM:SS.t` | `02:14.2` |
| Gesamtzeit in der Live-Tabelle | `MM:SS.t` | `14:32.8` |
| Zeit im Renn-Log | `YYYY-MM-DD HH:MM:SS.mmm` | `2026-08-20 14:30:00.123` |
| Zeit in der Blackbox | `YYYY-MM-DD HH:MM:SS,mmm` | `2026-08-20 14:30:00,123` |

Die Anzeige rundet auf Zehntelsekunden. Die Blackbox und die internen
Ereignisse speichern Millisekunden.

### 8.4 Platzierung

Die endgültige Platzierung wird **pro Klasse** berechnet:

1. Mehr vollständige Runden ist besser.
2. Bei gleicher Rundenzahl ist die geringere Gesamtzeit besser.
3. Boote ohne vollständige Runde erhalten Platz 0.

In jeder Klasse gibt es einen Ersten, einen Zweiten und so weiter. Die
Platznummer beginnt in jeder Klasse wieder bei 1.

Die Live-Tabelle zeigt dagegen eine laufende Gesamtreihenfolge über alle
Boote. Diese ist nur eine Orientierung während des Rennens.

### 8.5 Geschwindigkeit

Die Geschwindigkeitswerte sind Durchschnittsgeschwindigkeiten in km/h:

- **Letzte Runde:** Strecke der letzten Runde / Rundenzeit.
- **Gesamt:** Gesamtstrecke / Zeit vom individuellen Start bis zur letzten
  Passage.

Beispiel: `58.3/56.1` bedeutet 58,3 km/h in der letzten Runde und
56,1 km/h im Gesamtschnitt. Die Anzeige verwendet einen Punkt als
Dezimaltrennzeichen.

---

## 9. Sperrzeit, Fehlbedienung und Korrekturen

### 9.1 Sperrzeit

Die Sperrzeit verhindert Doppelerfassungen. Standardwert: **2,0 Sekunden**
pro Boot.

Ablauf:

1. Eine gültige Passage wird verbucht.
2. Für dieses Boot beginnt die Sperrzeit.
3. Eine weitere Eingabe innerhalb der Sperrzeit wird als `INVALID`
   protokolliert.
4. Sie zählt nicht als Runde.
5. Die Sperrzeit wird durch die ungültige Eingabe **nicht** verlängert.

Die Sperrzeit ist ein App-Parameter und steht in `app_settings.json` neben
der `.exe`:

```json
{
    "lockout_seconds": 2.0,
    "enable_keyboard": false
}
```

- `lockout_seconds`: Sperrzeit in Sekunden.
- `enable_keyboard`: systemweite Hotkeys aus der Konfiguration aktivieren.

Änderungen werden erst nach einem Neustart der Anwendung wirksam.

> **Hinweis:** Läuft die Anwendung als Administrator, werden die
> systemweiten Hotkeys automatisch aktiviert – unabhängig davon, ob
> `enable_keyboard` auf `false` steht. Das ist bewusst so umgesetzt, damit
> ein Admin-Start ohne zusätzliche Konfiguration funktioniert.

Wenn die JSON-Datei beschädigt ist, startet die Anwendung mit den
Standardwerten. Ein Hinweis steht in `gui_startup.log`.

### 9.2 Ungültige Eingaben

Folgende Eingaben werden als `INVALID` protokolliert:

- Passage außerhalb der Phasen `ACTIVE`/`FINISHING`,
- Passage vor dem individuellen Start der Startreihe,
- Passage nach dem Beenden der Klasse,
- Passage innerhalb der Sperrzeit.

Die Eingabe erscheint rot im Ereignis-Feed und wird in der Blackbox
gespeichert. Sie beeinflusst die Wertung nicht.

### 9.3 Manuelle Korrektur +1

Wenn eine Passage nachweislich fehlt, kann eine Runde manuell ergänzt
werden:

1. Im Panel **Manuell +1 Runde** das betroffene Boot wählen.
2. **+1 RUNDE** drücken.
3. Die Anwendung fügt eine weitere Runde hinzu. Der Zeitpunkt ist der
   Zeitpunkt des Klicks.
4. Das Ereignis `CORRECTION_PLUS` wird protokolliert.

**Wichtig:**

- Die Korrektur ersetzt keine echte Passage. Sie sollte nur verwendet
  werden, wenn die fehlende Passage eindeutig belegt ist.
- Die Korrektur ist nur während des Rennens sinnvoll (`ACTIVE` oder
  `FINISHING`).
- Eine Korrektur um −1 Runde ist in Version 0.5.0 **nicht** umgesetzt.
- Die Korrektur wird im Renn-Log und in der Blackbox dokumentiert.

### 9.4 Typische Bedienfehler

| Fehler | Auswirkung | Empfehlung |
|---|---|---|
| Taste zu früh gedrückt | `INVALID`, keine Runde | Passage nachholen, wenn möglich |
| Taste doppelt gedrückt | Zweite Eingabe `INVALID` | Keine Aktion nötig |
| Falsches Boot erwischt | Runde beim falschen Boot | Vor dem Rennen Boot-Keys prüfen; im Zweifel Rennleitung informieren |
| Klasse zu früh beendet | Ergebnis steht fest, keine weiteren Passagen | Nur nach Ablauf der Renndauer beenden |
| Rennen versehentlich neu gestartet | Aktueller Fortschritt gelöscht | Sicherheitsabfrage beachten |
| Falsche Datenquelle bestätigt | Falsche Starter/Rennen | Anwendung neu starten oder Daten aktualisieren |

---

## 10. Crash-Recovery und Stromausfall

### 10.1 Zweck

Die Anwendung schreibt während des Rennens regelmäßig einen Zwischenstand
in die Datei `race_state.json`. Nach einem Absturz, einem Windows-Neustart
oder einem Stromausfall kann das Rennen damit fortgesetzt werden.

### 10.2 Was gespeichert wird

- Rennnummer und Phase,
- offizieller Rennstart und Rennende,
- Countdown-Zustand,
- Zustand jedes Boots,
- vollständige Runden mit Start- und Endzeit,
- alle Ereignisse,
- Klassenstatus,
- bereits gestartete Startreihen,
- Zeitpunkt der Speicherung,
- Schema-Version,
- Fingerabdruck der Datenquelle.

### 10.3 Wann ein State übernommen wird

Beim Start wird `race_state.json` nur übernommen, wenn:

1. die Datei gültig und lesbar ist,
2. die Schema-Version passt,
3. der State höchstens **12 Stunden** alt ist,
4. die Rennnummer zur geladenen Konfiguration passt,
5. der Fingerabdruck der Datenquelle zur aktuellen Datei passt.

Andernfalls wird der State verworfen und gelöscht. Die Anwendung startet
dann mit den normalen Renndaten.

Der Fingerabdruck besteht aus Pfad, Dateigröße und Änderungszeit der
geladenen `IMPORT.json` beziehungsweise Excel-Datei. Dadurch wird
verhindert, dass ein Zwischenstand von einer anderen Veranstaltung oder
einer anderen Datei wiederhergestellt wird.

### 10.4 Wie geschrieben wird

- Das Schreiben erfolgt **atomar**: zuerst in eine temporäre Datei, dann
  per `os.replace` an den endgültigen Platz. Ein Absturz während des
  Schreibens hinterlässt keine halbe JSON-Datei.
- Unveränderte Zustände werden höchstens alle **30 Sekunden** erneut
  geschrieben (Heartbeat). Das schont die Festplatte, hält aber die
  Altersprüfung frisch.
- Bei jeder Änderung wird sofort geschrieben.

### 10.5 Was nach einem Absturz zu tun ist

1. Anwendung neu starten.
2. Die Meldung im Ereignis-Feed prüfen:
   **„Crash-Recovery: Rennen N wiederhergestellt (Phase: …)“**.
3. Die angezeigten Runden, Zeiten und Klassenstatus mit dem letzten
   bekannten Stand vergleichen.
4. Wenn alles passt: Rennen fortsetzen.
5. Wenn nicht: **NEUSTART** drücken und das Rennen neu durchführen.

### 10.6 Wichtige Einschränkungen

- Ein Absturz **während des Vorstart-Countdowns**, bevor das `START`-Ereignis
  geschrieben wurde, wird nicht als laufendes Rennen wiederhergestellt.
- Wird `IMPORT.json` während eines laufenden Rennens verändert, passt der
  Fingerabdruck nicht mehr. Der State wird beim nächsten Start verworfen.
  Deshalb: `IMPORT.json` während eines Rennens nicht überschreiben.
- Die Crash-Recovery speichert nur das **aktuelle** Rennen. Bereits
  beendete Rennen liegen im Arbeitsspeicher und müssen exportiert werden,
  bevor die Anwendung geschlossen wird.
- Rundenzeiten werden nicht geschätzt. Fehlen in einem alten State die
  Runden-Details, bleibt die Rundenliste leer. Das ist bewusst so: lieber
  keine Daten als falsche Zeiten.

### 10.7 Blackbox als unabhängige Sicherung

Die Blackbox wird unabhängig vom Race-State fortlaufend geschrieben. Nach
jedem Eintrag werden `flush()` und `fsync()` aufgerufen. Damit liegen die
Daten auch bei einem Stromausfall auf dem Datenträger.

Die Blackbox ist **append-only**: Vorhandene Zeilen werden nie verändert
oder gelöscht. Ab 10 MB wird die Datei mit einem Zeitstempel archiviert und
eine neue begonnen.

---

## 11. Ergebnis-Export

### 11.1 Wann exportieren?

Exportieren Sie:

- nach jedem abgeschlossenen Rennen,
- spätestens nach dem letzten Rennen des Tages,
- **immer bevor Sie die Anwendung schließen**.

Der Export-Button ist nach dem ersten Anzeige-Takt immer aktiv. Er ist
unabhängig vom aktuell ausgewählten Rennen, weil er alle fertigen Rennen
auf einmal exportiert.

### 11.2 Was wird exportiert?

Der Export enthält:

- die Veranstaltungsdaten (Event),
- alle fertigen Rennen, sortiert nach Rennnummer,
- innerhalb jedes Rennens die Ergebnisse gruppiert nach Klasse,
- je Klasse die Platzierungen,
- je Boot: Platz, Boot-Nummer, Klasse, Fahrer, Team, Verein, Rennnummer,
  Rundenzahl, Gesamtzeit, beste Runde, Distanz, Durchschnittsgeschwindigkeit,
  Rennzeit sowie die Platzhalter für Strafen und Punkte,
- das vollständige Renn-Log des jeweiligen Rennens.

Wenn noch kein Rennen beendet wurde, wird trotzdem eine Datei erzeugt. Sie
enthält dann nur die Veranstaltungsdaten und eine leere Rennliste. Es
erscheint keine Fehlermeldung.

### 11.3 Dateiname und Ablage

Der Export heißt:

```text
RESULT_YYYYMMDD_HHMMSS.json
```

Beispiel:

```text
RESULT_20261108_143022.json
```

Die Datei liegt im Laufzeitordner:

- bei der fertigen `.exe`: im Ordner der `.exe`,
- in der Entwicklung: im Projektordner.

Bei jedem Export wird eine **neue** Datei erzeugt. Vorhandene Dateien
werden nicht überschrieben.

### 11.4 Aufbau der Ergebnisdatei

```json
{
  "event": {
    "title": "Erstes Testrennen",
    "date": "2026-08-20",
    "organizer": "Verein A"
  },
  "generated_at": "2026-11-08T14:30:22",
  "races": [
    {
      "race_number": 1,
      "race_duration_min": 2,
      "classes": [
        {
          "klasse": "Herren",
          "results": [
            {
              "place": 1,
              "boat_nr": "173",
              "klasse": "Herren",
              "skier": "Pfenningbauer, Paul",
              "team": "Team A",
              "club": "WSC Beispiel",
              "race_number": 1,
              "laps": 5,
              "total_time": "12:45.3",
              "best_lap": "02:28.1",
              "distance": 16.5,
              "avg_speed": 77.6,
              "race_time": "12:45.3",
              "penalties": null,
              "points": null
            }
          ]
        }
      ],
      "log": [
        "[2026-11-08 14:30:00.123] START: Race=1 STATUS: VALID",
        "[2026-11-08 14:30:00.125] STARTLINE: Race=1;Line=1 STATUS: VALID"
      ]
    }
  ]
}
```

**Hinweise zum Format:**

- Zeiten sind **formatierte Strings** im Format `MM:SS.t`, keine
  Sekundenzahlen.
- `distance` ist die gefahrene Strecke in **Kilometern**:
  `Länge R1 + (Runden - 1) × Länge R2+`.
- `avg_speed` ist die Durchschnittsgeschwindigkeit in **km/h**, berechnet
  aus gefahrener Distanz und **eigener Gesamtzeit** (Zahl mit einer
  Nachkommastelle).
- `race_time` ist die Zeit, die das Boot mit seiner
  Durchschnittsgeschwindigkeit für die **beste Strecke seiner Klasse im
  Rennen** gebraucht hätte: `eigene Zeit ÷ eigene Distanz × beste Distanz`.
  Für das Boot mit der größten Distanz entspricht sie der eigenen
  Gesamtzeit.
- `penalties` (Strafprozente) und `points` (Punkte) sind derzeit
  Platzhalter mit `null`; sie werden weiterhin außerhalb der Anwendung
  gepflegt.
- Das Renn-Log enthält Zeitstempel mit Millisekunden.
- Die Reihenfolge der Klassen entspricht der Reihenfolge im Rennen.
- Boote ohne Runde erscheinen mit `"place": 0`.

### 11.5 Export Status

Nach dem Export erscheint im Kopfbereich ein Status:

- grün: `Gespeichert: RESULT_...json`
- rot: Fehlermeldung, zum Beispiel wenn die Zieldatei gesperrt ist.

Zusätzlich steht eine Meldung im Ereignis-Feed.

### 11.6 Optionale Rückgabe nach Excel

Die Ergebnisdatei kann optional über das VBA-Makro **`MainJsonImport`** in
die Excel-Vorlage zurückgeschrieben werden. Dabei werden die Blätter
`results` und `log` befüllt. Ob dieses Makro in Ihrer Vorlage vorhanden ist,
hängt von der ausgelieferten Excel-Datei ab.

Der Rückimport ist **nicht** erforderlich, um ein Rennen zu fahren. Die
JSON-Datei ist das primäre Ergebnisformat.

> **Bildplatzhalter B12 – Ergebnis-Rückimport in Excel**
>
> Datei: `bilder/12_importergebnis_excel.png`
>
> Motiv: Excel-Blatt `results` nach dem Rückimport.
>
> Zu sehen: Platzierungen, Boot-Nummern, Klassen, Runden und Zeiten.

### 11.7 Ergebnisdatei sichern

Nach dem Export:

1. Die Datei `RESULT_<Zeitstempel>.json` auf einen zweiten Datenträger
   kopieren.
2. Die `blackbox.log` ebenfalls kopieren.
3. Beide Dateien zusammen mit der `IMPORT.json` archivieren.
4. Die Dateien nicht während des Rennens umbenennen oder verschieben.

---

## 12. Datenfluss, Ablage und Datensicherung

### 12.1 Datenfluss

```text
+---------------------------+
| Excel-Datei (.xlsm)       |
| _EXP_INFO                 |
| _EXP_STARTER              |
| _EXP_RACES                |
+-------------+-------------+
              |
              | VBA-Makro ExportExpRangesToJSON
              v
+---------------------------+
| IMPORT.json               |
+-------------+-------------+
              |
              | JsonRaceStore
              v
+---------------------------+
| Python-Anwendung          |
| RaceEngine + GUI          |
+------+------+------+------+
       |      |      |
       |      |      +--------------------> gui_startup.log
       |      +---------------------------> blackbox.log
       +----------------------------------> race_state.json
       |
       | Ergebnis-Export
       v
+---------------------------+
| RESULT_<Zeitstempel>.json |
+-------------+-------------+
              |
              | optional: VBA-Makro MainJsonImport
              v
+---------------------------+
| Excel-Blätter results/log |
+---------------------------+
```

### 12.2 Wer schreibt welche Datei?

| Datei | Schreiber | Leser |
|---|---|---|
| `IMPORT.json` | VBA-Makro in Excel | Python-App |
| `RESULT_*.json` | Python-App | Excel (optional), Archiv |
| `blackbox.log` | Python-App | Support, Beweisführung |
| `race_state.json` | Python-App | Python-App beim nächsten Start |
| `gui_startup.log` | Python-App | Support |
| `app_settings.json` | Bediener / Python-App | Python-App |

### 12.3 Datensicherung

Empfohlenes Vorgehen nach jeder Veranstaltung:

1. Programmordner schließen.
2. Den gesamten Ordner auf einen zweiten Datenträger kopieren.
3. Mindestens sichern:
   - `IMPORT.json`,
   - alle `RESULT_*.json`,
   - `blackbox.log` und gegebenenfalls archivierte Blackbox-Dateien,
   - `gui_startup.log` bei Problemen,
   - die verwendete Excel-Datei.
4. Die Sicherung mit Datum und Veranstaltungsname beschriften.

### 12.4 Aufbewahrung

- Die Blackbox ist das Beweisprotokoll und sollte mindestens so lange
  aufbewahrt werden, wie Ergebnisse angefochten werden können.
- Ergebnisdateien und Blackbox gehören zusammen.
- Die Excel-Datei und die `IMPORT.json` dokumentieren die
  Rennkonfiguration.

---

## 13. Technische Referenz: Excel-Schnittstelle

Dieser Abschnitt richtet sich an die technische Betreuung und an Personen,
die die Excel-Vorlage pflegen.

### 13.1 `INFO`-Bereich

| CODE | Bedeutung | Beispiel |
|---|---|---|
| `PAR_EVENT` | Veranstaltungsname | `Erstes Testrennen` |
| `PAR_DATE` | Veranstaltungsdatum | `2026-08-20` |
| `PAR_ORG` | Organisator | `Verein A` |

### 13.2 `RACES`-Bereich

| Feld | Typ | Einheit | Pflicht | Bedeutung |
|---|---|---|---|---|
| `FLD_RACE` | Ganzzahl | – | Ja | Rennnummer |
| `FLD_RACEDUR` | Ganzzahl | Minuten | Ja | Renndauer |
| `FLD_STARTINT` | Ganzzahl | Sekunden | Ja | Startintervall / Vorlaufzeit |
| `FLD_GRIDTIME` | Ganzzahl | Sekunden | Ja | Zeit zwischen Startreihen |
| `FLD_ROUND1` | Dezimalzahl | Kilometer | Ja | Länge der ersten Runde |
| `FLD_ROUND` | Dezimalzahl | Kilometer | Ja | Länge der Standardrunde |
| `FLD_STARTTIME` | – | – | Nein | Wird exportiert, aber nicht verwendet |

Die Anwendung rechnet `FLD_ROUND1` und `FLD_ROUND` von Kilometern in Meter
um und speichert sie als `lap1_length_m` und `standard_lap_length_m`.

### 13.3 `STARTER`-Bereich

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `FLD_BOATNR` | Text/Zahl | Ja | Boot-Nummer |
| `FLD_SKIER` | Text | Ja | Fahrer-Name |
| `FLD_CLASS` | Text | Ja | Rennklasse |
| `FLD_RACE` | Ganzzahl | Ja | Rennnummer |
| `FLD_LINE` | Ganzzahl | Ja | Startreihe, muss > 0 sein |
| `FLD_HOTKEY` | Buchstabe A–Z | Nein | Boot-Key; wird sonst automatisch vergeben |
| `FLD_TEAM` | Text | Nein | Team |
| `FLD_DRIVER` | Text | Nein | Fahrer des Boots |
| `FLD_OBSERVER` | Text | Nein | Beobachter |
| `FLC_CLUB` | Text | Nein | Verein |
| `FLD_FED` | Text | Nein | Verband |

### 13.4 JSON-Struktur von `IMPORT.json`

```json
{
  "info": [
    { "CODE": "PAR_EVENT", "Parameter": "Veranstaltung", "Wert": "Erstes Testrennen" },
    { "CODE": "PAR_DATE", "Parameter": "Datum", "Wert": "2026-08-20" },
    { "CODE": "PAR_ORG", "Parameter": "Organisator", "Wert": "Verein A" }
  ],
  "races": [
    {
      "FLD_RACE": 1,
      "FLD_STARTINT": 5,
      "FLD_RACEDUR": 2,
      "FLD_ROUND": 3.5,
      "FLD_ROUND1": 2,
      "FLD_GRIDTIME": 30
    }
  ],
  "starter": [
    {
      "FLD_BOATNR": 173,
      "FLD_CLASS": "Herren",
      "FLD_TEAM": "Speedhunter",
      "FLD_SKIER": "Martin Praschinger",
      "FLD_DRIVER": "Seppi Coeto",
      "FLD_OBSERVER": "Mikel Praschinger",
      "FLC_CLUB": "WSC Redshark",
      "FLD_FED": "",
      "FLD_HOTKEY": "A",
      "FLD_RACE": 1,
      "FLD_LINE": 1
    }
  ]
}
```

### 13.5 Alte JSON-Formate

Die Anwendung erkennt das alte deutsche Feldformat ohne `FLD_`/`CODE` und
lehnt es mit einer klaren Meldung ab:

> „IMPORT.json verwendet das alte Feldformat (ohne FLD_/CODE). Bitte die
> Excel-Datei mit der aktuellen Vorlage neu exportieren.“

In diesem Fall die Excel-Datei mit der aktuellen Vorlage öffnen und
`ExportExpRangesToJSON` erneut ausführen.

### 13.6 Grenzen und Besonderheiten

- Pro Rennen maximal 26 Boote (A–Z).
- Boot-Keys müssen innerhalb eines Rennens eindeutig sein.
- Derselbe Key darf in verschiedenen Rennen vorkommen.
- Startreihen werden aus `FLD_LINE` abgeleitet; es gibt keine separate
  Klassen-Zuordnungstabelle.
- Klassen werden aus `FLD_CLASS` der Starter abgeleitet.
- Rundenlängen sind pro Rennen, nicht global pro Veranstaltung.
- Fehlende oder ungültige Pflichtfelder blockieren den Rennstart über die
  Validierung.

---

## 14. Renn-Log und Ereignistypen

### 14.1 Zweck

Das Renn-Log ist ein vollständiges Ereignisprotokoll. Es wird mit dem
Ergebnis exportiert und kann optional nach Excel zurückgeschrieben werden.
Es ist so aufgebaut, als wäre ein Zeilendrucker angeschlossen.

### 14.2 Zeilenformat

```text
[YYYY-MM-DD HH:MM:SS.mmm] EVENT: Daten STATUS: VALID|INVALID
```

Beispiele:

```text
[2026-08-20 14:30:00.123] START: Race=1 STATUS: VALID
[2026-08-20 14:30:00.125] STARTLINE: Race=1;Line=1 STATUS: VALID
[2026-08-20 14:30:30.200] STARTLINE: Race=1;Line=2 STATUS: VALID
[2026-08-20 14:31:05.445] PASSAGE: Boot=A STATUS: VALID
[2026-08-20 14:31:08.112] INVALID: Boot=B STATUS: INVALID
[2026-08-20 14:33:22.890] FINISH: Boot=A STATUS: VALID
```

### 14.3 Ereignistypen

| Ereignis | Wann | Daten | Beispiel |
|---|---|---|---|
| `START` | Rennstart nach dem Countdown | `Race={Nr}` | `START: Race=1 STATUS: VALID` |
| `STARTLINE` | Start einer Startreihe | `Race={Nr};Line={Nr}` | `STARTLINE: Race=1;Line=2 STATUS: VALID` |
| `PASSAGE` | Gültige Rundenpassage | `Boot={Key}` | `PASSAGE: Boot=A STATUS: VALID` |
| `FINISH` | Klasse beendet, je Boot | `Boot={Key}` | `FINISH: Boot=A STATUS: VALID` |
| `CORRECTION_PLUS` | Manuelle +1-Korrektur | `Boot={Key};Delta=+1` | `CORRECTION_PLUS: Boot=A;Delta=+1 STATUS: VALID` |
| `CORRECTION_MINUS` | Im Datenmodell vorgesehen, derzeit nicht erzeugt | `Boot={Key};Delta=-1` | – |
| `INVALID` | Sperrzeit, falsche Phase, Boot noch nicht gestartet oder bereits fertig | `Boot={Key}` | `INVALID: Boot=B STATUS: INVALID` |

**Regeln:**

- Der Ereignistyp ist immer in Großbuchstaben.
- `VALID` bedeutet: für die Wertung berücksichtigt.
- `INVALID` bedeutet: protokolliert, aber nicht gewertet.
- `PAUSE`, `RESUME` und `ENDRACE` sind **keine** eigenen Log-Ereignisse.
  Pause und Weiter steuern nur den Countdown. Das Rennende wird über
  `FINISH` je Boot abgebildet.
- `CORRECTION_MINUS` ist im Datenmodell vorhanden, wird in Version 0.5.0
  aber nicht ausgelöst.

### 14.4 Blackbox-Zeilen

Die Blackbox verwendet ein ähnliches, aber eigenständiges Format:

```text
[2026-08-20 14:31:05,445] TASTE: 'a' EVENT: PASSAGE STATUS: VALID
[2026-08-20 14:31:08,112] TASTE: 'b' EVENT: INVALID STATUS: INVALID
[2026-08-20 14:31:08,113] TASTE: 'b'
```

Die letzte Zeile ist der **Rohdruck** der Taste, bevor die Verarbeitung
das Ergebnis kennt. Dadurch bleibt die Beweiskette lückenlos.

---

## 15. Störungshilfe und häufige Fragen

### 15.1 Start und Datenquelle

| Problem | Mögliche Ursache | Lösung |
|---|---|---|
| „Keine Renndaten gefunden in …“ | Keine `IMPORT.json` und keine Excel-Datei im Programmordner | `IMPORT.json` neben die `.exe` legen oder Excel-Datei in den Ordner kopieren |
| „Datenquelle wurde nicht bestätigt“ | Dialog mit **Nein** beantwortet | Anwendung neu starten und Dialog bestätigen |
| „IMPORT.json verwendet das alte Feldformat“ | Excel wurde mit einer alten Vorlage exportiert | Mit aktueller Vorlage neu exportieren (`FLD_`/`CODE`) |
| „IMPORT.json enthält keine gültigen Rennen“ | `FLD_RACE` fehlt oder ist ungültig | Rennnummer in Excel prüfen |
| „IMPORT.json enthält keine gültigen Starter“ | `FLD_BOATNR`/`FLD_SKIER` fehlen | Starterdaten prüfen |
| App startet nicht | Fehler beim Laden oder in der GUI | `gui_startup.log` im Programmordner prüfen |

### 15.2 Rennen und Validierung

| Problem | Mögliche Ursache | Lösung |
|---|---|---|
| „Rennen nicht freigegeben“ | Pflichtfeld fehlt oder ist 0 | Meldung im Dialog lesen, Excel korrigieren, `IMPORT.json` neu erzeugen, **Daten aktualisieren** |
| START-Button grau | Rennen ist bereits beendet | Anderes Rennen wählen oder Ergebnis exportieren |
| Rennen-Dropdown grau | Rennen läuft noch | Rennen zuerst beenden oder NEUSTART |
| „Rennen N: Keine Starter“ | Kein Starter mit dieser Rennnummer | `FLD_RACE` der Starter prüfen |
| „Boot …: Startreihe muss > 0 sein“ | `FLD_LINE` fehlt oder ist 0 | Startreihe in Excel eintragen |
| „Boot …: Keine Klasse zugewiesen“ | `FLD_CLASS` fehlt | Klasse eintragen |
| „Doppelter Boot-Key …“ | Zwei Boote mit demselben Key im selben Rennen | `FLD_HOTKEY` eindeutig vergeben |
| „Keine freien Boot-Keys mehr verfügbar“ | Mehr als 26 Boote in einem Rennen | Rennen aufteilen oder Starter reduzieren |

### 15.3 Hotkeys

| Problem | Mögliche Ursache | Lösung |
|---|---|---|
| Hotkeys reagieren nicht | Anwendung läuft ohne Administrator-Rechte | Als Administrator starten |
| Hotkey-Status grau | Keine Admin-Rechte oder Hotkeys deaktiviert | Status in der Überschrift prüfen, als Admin starten |
| Nur Klicks auf die virtuelle Tastatur funktionieren | Systemweite Hotkeys inaktiv | Als Administrator starten |
| Hotkey eines Boots ist grau | Startreihe noch nicht gestartet oder Klasse beendet | Status in der Live-Tabelle prüfen |
| Taste wird einem falschen Boot zugeordnet | `FLD_HOTKEY` falsch oder automatisch vergeben | Boot-Keys in Excel prüfen |

### 15.4 Excel und Makros

| Problem | Mögliche Ursache | Lösung |
|---|---|---|
| „VBA-Makro nicht gefunden“ | Modulname weicht ab (`mdlEngl` vs. `mdl_Engl_Export`) | `IMPORT.json` manuell in Excel erzeugen (offener Punkt 1) |
| Makro lässt sich nicht ausführen | Makros in Excel deaktiviert | Makros erlauben, Datei als vertrauenswürdigen Speicherort hinzufügen |
| Excel-Datei gesperrt | Excel hat die Datei geöffnet | Excel schließen, erneut versuchen |
| „pywin32 nicht installiert“ | Python-Umgebung unvollständig | `pip install -r requirements.txt` |
| Export erzeugt keine `IMPORT.json` | Makro meldet keinen Fehler, schreibt aber nicht | Named Ranges und Schreibrechte prüfen |

### 15.5 Anzeige und Ergebnisse

| Problem | Mögliche Ursache | Lösung |
|---|---|---|
| Runden fehlen | Passage wurde nicht erfasst oder war ungültig | Blackbox und Ereignis-Feed prüfen; ggf. +1-Korrektur |
| `SPERRZEIT` bleibt stehen | Anzeige wird erst im nächsten Tick aufgeräumt | Kurz warten; bei Daueranzeige Anwendung neu starten |
| Geschwindigkeit `–/–` | Noch keine Runde oder Rundenlängen 0 | Rundenlängen in Excel prüfen |
| Platzierung erscheint ungewohnt | Live-Tabelle zeigt Gesamtreihenfolge, nicht Klassenwertung | Export prüfen; dort ist die Platzierung pro Klasse |
| Ergebnisse nach Neustart weg | Fertige Rennen liegen nur im Arbeitsspeicher | Vor dem Schließen exportieren |
| Export-Datei fehlt | Export nicht ausgeführt oder Fehler | Status im Kopfbereich und Ereignis-Feed prüfen |

### 15.6 Crash-Recovery

| Problem | Mögliche Ursache | Lösung |
|---|---|---|
| Rennen wird nach Absturz nicht fortgesetzt | State zu alt, falsche Rennnummer oder andere Datenquelle | `gui_startup.log` prüfen; Rennen neu starten |
| „Crash-Recovery: State passt nicht zur Datenquelle“ | `IMPORT.json` wurde verändert | State wird verworfen; Rennen neu starten |
| Runden fehlen nach Recovery | Alter State ohne Runden-Details | Bewusst keine Schätzung; Rennen ggf. neu starten |
| `race_state.json` lässt sich nicht löschen | Datei von einem Prozess gesperrt | Anwendung schließen, Datei löschen |

### 15.7 Häufige Fragen

**Kann ich die Anwendung ohne Excel betreiben?**

Ja, für den reinen Rennbetrieb genügt eine vorhandene `IMPORT.json`. Excel
wird für die Datenaufbereitung und den Export der JSON-Datei benötigt.

**Kann ich während eines Rennens das Rennen wechseln?**

Nein. Das Dropdown ist während eines laufenden Rennens deaktiviert.

**Kann ich ein beendetes Rennen erneut starten?**

Nein. Ein bereits beendetes Rennen hat einen grauen START-Button. Es kann
nur angesehen oder exportiert werden. Für einen neuen Durchgang müsste das
Rennen über einen entsprechenden neuen Datensatz neu geladen werden.

**Werden die Ergebnisse automatisch in Excel geschrieben?**

Nein. Die Anwendung schreibt eine JSON-Datei. Der Rückimport nach Excel ist
optional über das Makro `MainJsonImport` möglich.

**Was passiert, wenn ich die Anwendung ohne Administrator starte?**

Die Bedienung über die virtuelle Tastatur funktioniert. Die systemweiten
Hotkeys bleiben inaktiv.

**Wie viele Boote kann ein Rennen haben?**

Maximal 26, weil die Boot-Keys auf die Buchstaben A–Z beschränkt sind.

**Kann ich eine Runde abziehen?**

In Version 0.5.0 nicht. Es gibt nur `+1`. Eine falsche Runde muss
dokumentiert und gegebenenfalls nachträglich in der Rennleitung geklärt
werden.

**Was ist die wichtigste Datei nach dem Rennen?**

Die `blackbox.log` und die Ergebnisdatei `RESULT_*.json`. Beide sollten
gesichert und gemeinsam archiviert werden.

---

## 16. Abgleich mit dem Pflichtenheft

Das Pflichtenheft V1.0 vom 17.06.2026 beschreibt den geplanten
Lieferumfang. Die folgende Tabelle stellt die Anforderungen dem tatsächlichen
Stand von Version 0.5.0 gegenüber.

| Pflichtenheft | Umsetzung in Version 0.5.0 | Bewertung |
|---|---|---|
| Excel-Datei mit Blättern Renndaten, Starter, Rennkonfiguration, Templates | Excel-Vorlage mit Named Ranges `_EXP_INFO`, `_EXP_STARTER`, `_EXP_RACES`; Export über VBA-Makro | Erfüllt, technisch über Named Ranges statt fester Blattnamen |
| Renndaten: Event-Titel, Datum, Veranstalter | `INFO`-Bereich mit `PAR_EVENT`, `PAR_DATE`, `PAR_ORG` | Erfüllt |
| Renndaten: Länge Runde 1 und Standard-Runde | Pro Rennen in `RACES` (`FLD_ROUND1`, `FLD_ROUND`), in Excel in Kilometern | Erfüllt mit Einheitenhinweis |
| Starter: Boot-Key, Boot-Name, Klasse | `STARTER` mit `FLD_HOTKEY`, `FLD_BOATNR`, `FLD_SKIER`, `FLD_CLASS` und weiteren Feldern | Erfüllt und erweitert |
| Rennkonfiguration: Rennnummer, Renndauer, Vorlaufzeit, Startlinien mit Offset, Klassen-Zuordnung | `FLD_RACE`, `FLD_RACEDUR`, `FLD_STARTINT`, `FLD_GRIDTIME`; Startreihen aus `FLD_LINE`; Klassen aus `FLD_CLASS` | Erfüllt, Startlinien-Offset durch Grid Time ersetzt |
| Datenquelle nach Start suchen und bestätigen lassen | Auto-Suche mit Bestätigungsdialog; bei `--json`/`--excel` und Crash-Recovery keine Nachfrage | Teilweise erfüllt, bewusste Abweichung |
| Validierung vor Rennfreigabe | `DataValidator` prüft Pflichtfelder, Rundenlängen, Startintervall, Grid Time, Starter, Klassen, Startreihen | Erfüllt |
| Erste Runde aus Startzeit und erster Zielpassage | Erste Runde ab individuellem Startzeitpunkt der Startreihe | Erfüllt und um Startreihen erweitert |
| Weitere Runden aus Differenz aufeinanderfolgender Passagen | `ResultCalculator.add_lap` | Erfüllt |
| Konfigurierbare Sperrzeit | `lockout_seconds` in `app_settings.json`, Standard 2,0 s | Erfüllt, Konfiguration über Datei statt GUI |
| Ereignismodell mit Zeitstempel, Bootskennung, Eventtyp | `RaceEvent` (frozen) mit Zeitstempel, Boot-Key, EventType, `valid`, `source`, `detail` | Erfüllt |
| Platzierung primär Runden, sekundär Gesamtzeit | `ResultCalculator.compute_results` | Erfüllt |
| Platzierung pro Klasse | Jede Klasse hat einen Ersten, Zweiten, … | Erfüllt und erweitert (Kundenentscheidung 2026-09-04) |
| Letzte Runde nach Renndauer: erste Zielpassage markiert das Klassenende, weitere Boote beenden die begonnene Runde | **Nicht umgesetzt.** Stattdessen manuelle Klassen-Beendigung über „Beenden“ | Bewusste Abweichung (Kundenentscheidung 2026-09-03), dokumentiert |
| Rennstart nach Countdown automatisch | Countdown startet das Rennen bei 0 automatisch; kein separates Startsignal | Erfüllt (Q8, 2026-08-14) |
| GUI: Start-Button, Countdown, Live-Tabelle, Manuell +1 | Alle vorhanden, zusätzlich Renninformationen, Hotkey-Panel, Ereignis-Feed, Rennende-Status, Export | Erfüllt und erweitert |
| Sperrzeit visualisieren | Status `SPERRZEIT (Ns)` in der Live-Tabelle | Erfüllt |
| Fehlermeldungen kurz und handlungsorientiert | Validierungsdialog und Log-Feed | Erfüllt |
| TXT-Blackbox, unveränderlich | `blackbox.log`, append-only, `flush` + `fsync`, Rotation ab 10 MB | Erfüllt |
| Excel-Log, strukturierte Erfassung | Ergebnis-JSON mit Renn-Log; optionaler Rückimport nach Excel | Teilweise erfüllt, JSON ist primäres Format |
| Error-Log | `gui_startup.log` (Diagnose); keine separaten `error.log`/`current.log` im Produktivpfad | Teilweise erfüllt |
| Fehlertoleranz bei Absturz/Stromausfall | `race_state.json` mit 12-Stunden-Prüfung, Rennnummer, Quell-Fingerprint, atomarem Schreiben | Erfüllt |
| Offline-First | Keine Netzwerkabhängigkeit | Erfüllt |
| Reaktionszeit unter 100 ms | GUI-Polling alle 50 ms | Erfüllt (Zielwert) |
| Stabilität über eine Veranstaltung | Dauerbetrieb vorgesehen; Crash-Recovery und Blackbox als Sicherung | Erfüllt im Rahmen des Releases |
| Auslieferung als eine `.exe` | PyInstaller-Spezifikation `Wasserski-Zeitnehmung.spec` | Vorhanden, Release 0.4.0 |
| Windows und Excel erforderlich | Windows 10/11; Excel für Datenaufbereitung und optionalen Rückimport | Erfüllt; reiner Rennbetrieb benötigt nur `IMPORT.json` |
| Ausschließlich deutsch | Oberfläche und Dokumentation deutsch | Erfüllt |
| Benutzerverwaltung, zentrale DB, mobile Geräte, Hardware | Nicht enthalten | Bewusst außerhalb des MVP |
| Administrator-Rechte für Hotkeys | Systemweite Hotkeys benötigen Admin-Rechte | Zusatzanforderung, in der Doku berücksichtigt |
| Ergebnis-Persistenz beim Rennwechsel | `finished_races` im Arbeitsspeicher | Erweiterung, nicht über Programmneustart hinweg |
| Export aller fertigen Rennen in eine Datei | `RESULT_<Zeitstempel>.json`, gruppiert nach Rennen und Klasse | Erweiterung (Kundenwunsch 2026-09-03) |

### 16.1 Besonders wichtige Abweichungen

**1. Manuelle Klassen-Beendigung statt automatischer letzter Runde**

Das Pflichtenheft beschreibt in §5.3 eine automatische Endlogik: Die erste
Zielpassage nach Ablauf der Renndauer markiert die letzte Runde der Klasse,
weitere Boote beenden die begonnene Runde regulär. Diese Logik wurde auf
Kundenwunsch am 03.09.2026 entfernt. Stattdessen beendet der Bediener jede
Klasse manuell über den Button **Beenden**. Damit steht das Ergebnis fest,
sobald die Klasse beendet ist.

**2. Startreihen-Offset über Grid Time**

Das Pflichtenheft nennt „Startlinien einschließlich Zeitoffset“. In der
aktuellen Umsetzung kommt der Offset ausschließlich aus der Grid Time pro
Rennen. Die Startreihen selbst werden aus `FLD_LINE` der Starter abgeleitet.
Eine separate Klassen-Zuordnungstabelle gibt es nicht.

**3. Datenquellen-Bestätigung**

Das Pflichtenheft fordert eine Bestätigung der Datenquelle. Die Anwendung
zeigt diese Bestätigung bei der Auto-Suche. Bei explizit übergebenen
Dateien (`--json`, `--excel`) und bei der Crash-Recovery wird bewusst ohne
Nachfrage geladen, um Zeit zu sparen.

**4. Excel-Log**

Das Pflichtenheft nennt ein „Excel-Log“. Die Anwendung schreibt das
Renn-Log in die Ergebnis-JSON. Ein Rückimport in die Excel-Blätter
`results` und `log` ist optional über das Makro `MainJsonImport` möglich.
Die JSON-Datei ist das primäre und vollständige Ergebnisformat.

---

## 17. Offene Punkte und bekannte Einschränkungen

### 17.1 Offene Punkte

| Punkt | Beschreibung | Auswirkung |
|---|---|---|
| Excel-Direktstart | Python ruft das VBA-Modul `mdlEngl` auf; die aktuelle Vorlage nutzt `mdl_Engl_Export` | Direkter Excel-Start aus der App ist nicht freigegeben; `IMPORT.json` manuell erzeugen |
| `ENDRACE`-Event | Es gibt kein eigenes Rennende-Ereignis; das Rennen endet über `FINISH` je Boot | Für die Auswertung ausreichend, für die Langzeitarchivierung diskutabel |
| VBA-Export bereinigen | `Starttimer`/`Startzeit` werden noch exportiert, aber nicht verwendet | Keine funktionale Auswirkung; Export ist unnötig groß |
| `CORRECTION_MINUS` | Im Datenmodell vorhanden, aber nicht implementiert | Keine −1-Korrektur möglich |
| Ergebnis-Persistenz | Fertige Rennen liegen nur im Arbeitsspeicher | Vor dem Schließen exportieren |
| Live-Platzierung | Live-Tabelle zeigt Gesamtreihenfolge, nicht Klassenwertung | Nur Orientierung; endgültige Platzierung im Export |
| Sperrzeit-Konfiguration | Nur über `app_settings.json`, nicht über die GUI | Änderung erfordert Dateibearbeitung und Neustart |
| PyInstaller-Build | Release 0.4.0 vorhanden | Test auf sauberem Windows-System ohne Python erforderlich |

### 17.2 Bekannte Einschränkungen im Betrieb

- Die Anwendung ist auf Windows 10/11 und deutsche Sprache ausgelegt.
- Systemweite Hotkeys benötigen Administrator-Rechte.
- Pro Rennen sind maximal 26 Boote möglich.
- Die Runner-Spalte zeigt Boot-Nummer und Team (ohne Klasse) und kürzt lange Namen nach 18 Zeichen.
- Ein Rennen kann nicht gewechselt werden, solange es läuft.
- Ein beendetes Rennen kann nicht erneut gestartet werden.
- Die Crash-Recovery stellt nur das aktuelle Rennen wieder her.
- Die Anwendung schreibt keine Excel-Datei während des Rennens.
- Die Rundenlängen werden in Excel in Kilometern gepflegt.

---

## 18. Glossar

| Begriff | Bedeutung |
|---|---|
| **Blackbox** | Append-only TXT-Datei mit allen Tastendrücken und Verarbeitungsergebnissen. Beweisfunktion. |
| **Boot-Key** | Buchstabe A–Z, der einem Boot zugeordnet ist und als Hotkey dient. |
| **Countdown** | Vorlaufzeit vor dem Rennstart. Wird aus dem Startintervall berechnet. |
| **Crash-Recovery** | Automatische Wiederherstellung des Rennzustands nach einem Absturz über `race_state.json`. |
| **Event** | Veranstaltung mit Titel, Datum und Organisator. |
| **Grid Time** | Zeit zwischen dem Start aufeinanderfolgender Startreihen. |
| **Hotkey** | Systemweite Taste, die eine Rundenpassage auslöst. |
| **IMPORT.json** | Von Excel erzeugte Datei mit allen Renndaten. Zentrale Eingabedatei der App. |
| **Klasse** | Rennklasse, zum Beispiel Herren, Junioren oder F1. |
| **Lockout / Sperrzeit** | Zeitfenster nach einer gültigen Passage, in dem weitere Eingaben verworfen werden. |
| **Passage** | Überqueren der Start-/Ziellinie; schließt eine Runde ab. |
| **Race-State** | Zwischenstand des laufenden Rennens in `race_state.json`. |
| **RESULT-Datei** | Ergebnis-Export mit allen fertigen Rennen. |
| **Renn-Log** | Chronologisches Ereignisprotokoll eines Rennens. |
| **Startintervall** | Vorlaufzeit bis zum Rennstart in Sekunden. |
| **Startreihe** | Gruppe von Booten, die gemeinsam zeitversetzt startet. |
| **VALID / INVALID** | Gültig / ungültig für die Wertung. Ungültige Ereignisse bleiben protokolliert. |

---

## 19. Bildplatzhalter und Screenshot-Liste

Die folgenden Screenshots sollten für die finale Kundenversion erstellt und
im Ordner `bilder/` abgelegt werden. Die Dateinamen entsprechen den
Platzhaltern in diesem Dokument.

| Nr. | Datei | Motiv | Priorität |
|---|---|---|---|
| B1 | `bilder/01_hauptfenster.png` | Gesamtes Hauptfenster nach dem Laden eines Rennens | Hoch |
| B2 | `bilder/02_kopfbereich.png` | Kopfbereich mit Datenquelle und Buttons | Hoch |
| B3 | `bilder/03_renninformationen.png` | Panel Renninformationen | Mittel |
| B4 | `bilder/04_countdown_vorstart.png` | Vorstart-Countdown mit PAUSE/NEUSTART | Hoch |
| B5 | `bilder/05_startreihe_countdown.png` | Startreihen-Countdown nach dem Rennstart | Hoch |
| B6 | `bilder/06_live_tabelle.png` | Live-Tabelle mit Runden, Geschwindigkeiten und Status | Hoch |
| B7 | `bilder/07_hotkeys.png` | Virtuelle Tastatur mit aktiven und inaktiven Keys | Hoch |
| B8 | `bilder/08_ereignisfeed.png` | Ereignis-Feed mit gültigen und ungültigen Zeilen | Mittel |
| B9 | `bilder/09_rennende_status.png` | Rennende-Status mit WARTEND und FERTIG | Hoch |
| B10 | `bilder/10_manuell_plus1.png` | Manuelle +1-Korrektur | Mittel |
| B11 | `bilder/11_excel_export_makro.png` | Excel-Makro `ExportExpRangesToJSON` | Hoch |
| B12 | `bilder/12_importergebnis_excel.png` | Excel-Ergebnisblatt nach optionalem Rückimport | Niedrig |
| B13 | `bilder/13_dateien_programmordner.png` | Dateien im Programmordner | Mittel |
| B14 | `bilder/14_fehlerdialog.png` | Fehlermeldung bei fehlenden Renndaten | Niedrig |

### 19.1 Hinweise für Screenshots

- Keine echten Teilnehmerdaten, Telefonnummern oder sonstigen
  personenbezogenen Daten verwenden.
- Ein neutrales Testrennen mit fiktiven Namen verwenden.
- Die Fenstergröße auf 1440 × 900 oder größer einstellen.
- Den Mauszeiger möglichst nicht im Bild haben.
- Bei dunklem Theme auf ausreichenden Kontrast achten.
- Screenshots als PNG ablegen, nicht als JPG.
- Die Dateinamen exakt wie in der Tabelle verwenden.

### 19.2 Ordnerstruktur

```text
Wasserski/
├── Manual.md
├── bilder/
│   ├── 01_hauptfenster.png
│   ├── 02_kopfbereich.png
│   ├── 03_renninformationen.png
│   ├── 04_countdown_vorstart.png
│   ├── 05_startreihe_countdown.png
│   ├── 06_live_tabelle.png
│   ├── 07_hotkeys.png
│   ├── 08_ereignisfeed.png
│   ├── 09_rennende_status.png
│   ├── 10_manuell_plus1.png
│   ├── 11_excel_export_makro.png
│   ├── 12_importergebnis_excel.png
│   ├── 13_dateien_programmordner.png
│   └── 14_fehlerdialog.png
└── ...
```

---

## 20. Dokumentenhistorie

| Datum | Version | Änderung |
|---|---|---|
| 10.11.2026 | 0.5.0 | Release: Rennende-Ampel in der Live-Tabelle (grün/roter Punkt) und klickbare Hotkey-Taste im Panel Tastaturbedienung (rot/weiß); Runner-Spalte ohne Klasse; Handbuch aktualisiert |
| 09.11.2026 | 0.4.0 | Release: Renndauer-Uhr, Ergebnis-Export um Distanz, Durchschnittsgeschwindigkeit und Rennzeit erweitert, Build-Fix, Handbuch aktualisiert |
| 08.11.2026 | 0.3.0 | Vollständige Überarbeitung als Endanwender-Handbuch; Abgleich mit Code und Pflichtenheft; Bildplatzhalter ergänzt; neue Abschnitte zu Bedienung, Datenfluss, Fehlerhilfe und Abweichungen |
| 06.11.2026 | 0.3.0 | Crash-Recovery-Details, Dateikonvention `RESULT_*`, Event-Types, Laufzeitdateien, offene Punkte |
| 04.09.2026 | 0.2.0 | Platzierung pro Klasse, Export aller fertigen Rennen |
| 03.09.2026 | 0.2.0 | Manuelle Ziellogik, Startreihen, Hotkey-Status, Live-Tabelle |
| 14.08.2026 | 0.1.0 | Erste Fassung: Architektur, Rennlogik, GUI-Grundlagen |

---

*Ende des Benutzerhandbuchs*
