# Pflichtenheft – Zeitnehmungs-System Wasserski-Racing

**Version:** 1.0  
**Kunde:** anonym („Kunde“)  
**Datum:** [TT.MM.JJJJ]

---

# Dokumentenhistorie

| Version | Datum       | Beschreibung                         | Autor        |
|--------|------------|-------------------------------------|-------------|
| 1.0    | [TT.MM.JJJJ] | Initiale Erstellung FINAL PRO+       | Projektteam |

---

# Inhaltsverzeichnis
*(wird in Word automatisch erzeugt)*

---

# 1. Einleitung

## 1.1 Ziel des Dokuments
Dieses Dokument beschreibt die vollständigen Anforderungen an ein digitales Zeitnehmungs-System für Wasserski-Rennen.  
Es dient als verbindliche Grundlage für:

- Entwicklung
- Abstimmung mit dem Kunden
- spätere Abnahme und Erweiterung

---

## 1.2 Einsatzbereich
Das System wird von mehreren Vereinen innerhalb eines Verbandes eingesetzt.  
Es dient der Durchführung von Rennveranstaltungen unter realen Wettkampfbedingungen.

---

## 1.3 Zielsetzung
Das System soll:

- eine zuverlässige und präzise Zeitmessung ermöglichen
- einfach bedienbar sein (auch unter Stresssituationen)
- vollständig offline funktionieren
- eine manipulationssichere Protokollierung gewährleisten

---

## 1.4 Abgrenzung

Nicht Bestandteil dieses Projekts (MVP):

- zentrale Datenbank oder Archiv über mehrere Rennen
- mobile Endgeräte
- direkte Hardwareanbindung (z. B. Lichtschranken)
- automatisierte externe Schnittstellen

---

# 2. Systemarchitektur

## 2.1 Überblick

Das System besteht aus zwei klar getrennten Komponenten:

### Excel (.xlsx)
Funktion:
- Stammdatenverwaltung
- Rennkonfiguration
- Layoutdefinition (Startliste / Ergebnis)

### Python-Applikation (.exe)
Funktion:
- Zeitmessung
- Benutzerinteraktion
- Rennlogik
- Logging

---

## 2.2 Architekturprinzipien

- Trennung von Daten und Logik
- Ereignisbasierte Verarbeitung (Event-Driven)
- Offline-first Design
- Append-only Logging (keine Veränderung historischer Daten)

---

# 3. Datenstruktur (Excel)

## 3.1 Tabellenübersicht

| Tabellenblatt           | Beschreibung                          |
|------------------------|--------------------------------------|
| Renndaten              | Allgemeine Eventinformationen         |
| Starter                | Teilnehmer & Klassen                  |
| Rennkonfiguration      | Läufe und Startlogik                 |
| Template_Startliste    | Layout Startliste                     |
| Template_Ergebnis      | Layout Ergebnisliste                  |

---

## 3.2 Renndaten

| Feld                     | Beschreibung                        |
|-------------------------|------------------------------------|
| Event-Titel             | Name des Events                    |
| Datum                   | Veranstaltungsdatum               |
| Veranstalter            | Verein                            |
| Länge Runde 1           | Meter                             |
| Länge Standard-Runde    | Meter                             |

---

## 3.3 Starter

| Feld                | Beschreibung                     |
|---------------------|---------------------------------|
| Boot-Key            | A–Z                             |
| Boot-Name           | Name / Nummer                  |
| Klasse              | Zugehörige Klassen             |

---

## 3.4 Rennkonfiguration

| Feld                  | Beschreibung                    |
|-----------------------|--------------------------------|
| Rennnummer            | Identifikation                 |
| Renndauer             | Minuten                        |
| Vorlaufzeit           | Sekunden                       |
| Startlinien           | Name + Zeitoffset              |
| Klassen-Zuordnung     | Mapping Startlinie → Klassen   |

---

# 4. Ablauf eines Rennens

## 4.1 Vorstartphase

- Auswahl des Rennens in der GUI
- Einlesen aller Daten aus Excel
- Initialisierung der Boote
- Anzeige des Countdowns

---

## 4.2 Startphase

- Start durch Bediener
- globaler Countdown läuft
- Startlinien starten versetzt (Offset)

---

## 4.3 Rennphase

- Eingabe über Hotkeys (A–Z)
- Jeder Tastendruck = Ereignis
- Zeitstempel wird gespeichert
- Live-Tabelle wird aktualisiert

---

## 4.4 Rennende

- Renndauer läuft ab
- System wechselt in Endmodus
- Klassenweise Abschlusslogik wird aktiviert

---

# 5. Rennlogik (detailliert)

## 5.1 Ereignismodell

Jedes Event enthält:
- Zeitpunkt (Millisekunden)
- Boot
- Eventtyp (Start / Runde / Ziel / manuell)

---

## 5.2 Rundenberechnung

| Typ        | Berechnung                                   |
|------------|---------------------------------------------|
| Runde 1    | Startzeit → erste Passage                    |
| weitere    | Differenz vorige Runde → aktuelle            |

---

## 5.3 Sperrzeit

Ziel:
Vermeidung von Fehlbedienung

Regel:
- nach Eingabe wird Boot für x Sekunden gesperrt
- Eingaben innerhalb Sperrzeit werden ignoriert

---

## 5.4 Rennende-Logik (klassenweise)

1. Renndauer erreicht
2. System wartet auf erste Passage je Klasse
3. erste Passage → letzte Runde aktiviert
4. danach:
   - jedes Boot fährt genau eine letzte Runde

---

## 5.5 Platzierung

1. Anzahl Runden  
2. Gesamtzeit  

---

# 6. Benutzeroberfläche (GUI)

## 6.1 Hauptkomponenten

| Element              | Funktion                               |
|---------------------|----------------------------------------|
| Renn-Auswahl        | Auswahl des aktuellen Rennens         |
| Start-Button        | Startet Countdown                     |
| Countdown-Anzeige   | visuelle Startvorbereitung            |
| Live-Tabelle        | Anzeige aller Boote                   |
| Korrektur-Button    | manuelle Rundenkorrektur              |

---

## 6.2 Live-Anzeige (Beispiel)

| Boot | Klasse | Runden | letzte Runde | Gesamtzeit | Geschwindigkeit |
|------|--------|--------|--------------|------------|----------------|

---

## 6.3 Bedienkonzept

- vollständig tastaturfähig
- minimalistische GUI
- klare visuelle Rückmeldungen

---

# 7. Logging & Datensicherheit

## 7.1 Blackbox-Log (TXT)

Format:[HH:MM:SS,mmm] - TASTE: 'X' - STATUS: VALID / INVALID

Eigenschaften:
- unveränderlich
- vollständige Eingabehistorie
- dient als Beweis

---

## 7.2 Excel-Protokoll

| Feld        | Beschreibung                 |
|-------------|-----------------------------|
| Boot        | Identifikation              |
| Zeit        | Timestamp                   |
| Aktion      | Start / Runde / Ziel        |

---

## 7.3 Sicherheitskonzept

- TXT = Original (Beweis)
- Excel = Auswertung
- keine nachträgliche Manipulation der Rohdaten

---

# 8. Fehlertoleranz

## 8.1 Typische Fehler

- doppelte Eingabe
- falsche Eingabe
- verpasste Runde

---

## 8.2 Gegenmaßnahmen

- Sperrzeit
- manuelle Korrektur
- Logging jeder Aktion

---

## 8.3 Wiederherstellung

Im Fehlerfall:
- Einlesen der Logs
- Rekonstruktion des Rennzustands
- Weiterführung möglich

---

# 9. Nicht-funktionale Anforderungen

## 9.1 Stabilität
Dauerbetrieb über gesamte Rennzeit ohne Ausfall

## 9.2 Performance
Reaktionszeit < 100 ms

## 9.3 Offlinefähigkeit
Keine Internetverbindung erforderlich

---

# 10. Projektablauf & Versionierung

## 10.1 Phasen

1. MVP-Auslieferung  
2. Testphase (Fehler & Feedback)  
3. Optimierung  

---

## 10.2 Versionierung

| Version | Inhalt                     |
|--------|---------------------------|
| v1.x   | MVP                       |
| v2.x   | Erweiterungen             |
| v3.x   | Hardwareintegration       |

---

## 10.3 Erwartungsabgrenzung

Das MVP ist:
- funktional vollständig
- bewusst reduziert
- Grundlage zur Weiterentwicklung

---

# 11. Erweiterungen

## Version 2
- Datenimport
- Fehlerkorrektur im Protokoll
- erweiterte Auswertung

## Version 3
- Hardwareintegration
- Zeilendrucker
- Automatisierung

---

# 12. Auslieferung

## 12.1 Bereitstellung
- Lieferung als ausführbare `.exe`

---

## 12.2 Sourcecode (optional)
- Übergabe auf Wunsch möglich
- bei Übergabe:
  - keine Wartung
  - kein Support

---

# 13. Zusammenfassung

Das System stellt eine:

- robuste Zeitmesslösung
- einfache Bedienoberfläche
- vollständige Nachvollziehbarkeit
- flexible Erweiterbarkeit
