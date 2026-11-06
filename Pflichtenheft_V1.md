Pflichtenheft – Zeitnehmungs-System Wasserski-Racing Seite **1** von **8** 

## **EDV Engl Roman** 

Norbert Mayerstraße 15 3370 Ybbs/Donau 0677/633 82903 edv@engl.biz | www.engl.biz | ATU66927258 

## **Pflichtenheft** 

## _**Zeitnehmungs-System für Wasserski-Racing**_ 

_Technische Spezifikation und Projektgrundlage_ 

|**Version**|1.0|
|---|---|
|**Kunde**|Wolfram Kittl|
|**Erstellt durch**|EDV Engl Roman|
|**Datum**|17.06.2026|
|**Dokumentstatus**|Entwurf / Freigabe|

## **Inhalt** 

Dokumentenhistorie....................................................................................................................................................3 1. Einleitung....................................................................................................................................................................3 1.1 Zielsetzung............................................................................................................................................................3 1.2 Einsatzbereich....................................................................................................................................................3 1.3 Ziel des Dokuments...........................................................................................................................................3 1.4 Abgrenzung..........................................................................................................................................................3 2. Systemarchitektur....................................................................................................................................................3 2.1 Architekturprinzipien......................................................................................................................................3 3. Datenstruktur Excel................................................................................................................................................4 3.1 Renndaten............................................................................................................................................................4 3.2 Starter....................................................................................................................................................................4 3.3 Rennkonfiguration...........................................................................................................................................4 4. Rennablauf.................................................................................................................................................................4 5. Rennlogik (Detail)....................................................................................................................................................5 5.1 Ereignismodell....................................................................................................................................................5 5.2 Sperrzeit und Fehlbedienungsschutz.........................................................................................................5 5.3 Platzierung und Wertungslogik...................................................................................................................5 6. Benutzeroberfläche (GUI).....................................................................................................................................5 6.1 Bedienkonzept....................................................................................................................................................6 7. Logging & Sicherheit...............................................................................................................................................6 8. Fehlertoleranz...........................................................................................................................................................6 9. Nicht-funktionale Anforderungen.....................................................................................................................6 9.1 Stabilität................................................................................................................................................................6 9.2 Performance........................................................................................................................................................6 9.3 Offlinefähigkeit..................................................................................................................................................6 10. Projektablauf & Versionierung..........................................................................................................................6 11. Auslieferung..............................................................................................................................................................6 12. Zusammenfassung.................................................................................................................................................7 

## **Dokumentenhistorie** 

|**Version**|**Datum**|**Beschreibung**|**Autor**|
|---|---|---|---|
|1.0|17.06.2026|Initiale Erstellung|Engl Roman|


## **1. Einleitung** 

## **1.1 Zielsetzung** 

Ziel des Projekts ist die digitale Durchführung, präzise Zeitmessung und nachvollziehbare Auswertung von Wasserski-Rennen unter realen Wettkampfbedingungen. Das System soll eine verlässliche Bedienung auch unter Zeitdruck ermöglichen, Fehlbedienungen reduzieren und eine belastbare Grundlage für Ergebnislisten, Korrekturen und spätere Abnahmen schaffen. 

## **1.2 Einsatzbereich** 

Der Einsatzbereich umfasst regionale und überregionale Rennveranstaltungen, bei denen mehrere Klassen, Startlinien und Teilnehmer parallel verwaltet werden müssen. Das System ist für die Bedienung durch geschultes Personal am Veranstaltungsort vorgesehen und wird auf lokal verfügbaren Rechnern ohne permanente Netzwerkverbindung betrieben. 

## **1.3 Ziel des Dokuments** 

Dieses Pflichtenheft beschreibt die funktionalen und nicht-funktionalen Anforderungen an ein digitales Zeitnehmungs-System für Wasserski-Racing. Es dient als verbindliche Grundlage für Entwicklung, fachliche Abstimmung, Test, Abnahme und spätere Erweiterungen des Systems. 

## **1.4 Abgrenzung** 

Nicht Bestandteil des initialen Lieferumfangs (MVP) sind eine zentrale Datenbank über mehrere Veranstaltungen, mobile Endgeräte, direkte Hardwareanbindungen wie Lichtschranken, automatisierte externe Schnittstellen sowie eine Benutzerverwaltung mit Rollen- oder Rechtemanagement. Diese Punkte können in späteren Versionen berücksichtigt werden. 

## **2. Systemarchitektur** 

Das System besteht aus zwei klar getrennten Komponenten 

- einer Excel-Datei zur Pflege von Stammdaten, Rennkonfiguration und Ausgabelayouts 

- sowie einer ausführbaren Python-Applikation zur Laufzeitsteuerung, Zeitmessung, Ereignisverarbeitung und Protokollierung 

Diese Trennung unterstützt Wartbarkeit, Nachvollziehbarkeit und flexible Anpassungen an unterschiedliche Rennveranstaltungen. 

## **2.1 Architekturprinzipien** 

- Trennung von Datenhaltung und Anwendungslogik 

- Offline-First-Betrieb ohne Internetabhängigkeit 

- Ereignisbasierte Verarbeitung aller Eingaben 

- Manipulationsarme, nachvollziehbare Protokollierung 

- Robuste Bedienbarkeit unter Wettkampfbedingungen 

## **3. Datenstruktur Excel** 

Die Excel-Datei enthält mindestens folgende Blätter: 

|**Tabellenblatt**|**Beschreibung**|
|---|---|
|Renndaten|Eventinformationen,Streckenlängen|
|Starter|Boote und Klassen|
|Rennkonfiguration|Startlinien und Rennen|
|Templates|Startliste und Ergebnislayout|



## **3.1 Renndaten** 

|**3.1 Renndaten**||
|---|---|
|**Feld**|**Beschreibung**|
|Event-Titel|Name der Veranstaltung|
|Datum|Veranstaltungsdatum|
|Veranstalter|Ausrichtender Verein oder Verband|
|Länge Runde 1|Streckenlänge der ersten Runde in Metern|
|Länge Standard-Runde|Streckenlänge aller weiteren Runden in Metern|



## **3.2 Starter** 

|**3.2 Starter**||
|---|---|
|**Und**|**Beschreibung**|
|Boot-Key|Eindeutige Tastenzuordnungvon A bis Z|
|Boot-Name|Name,Nummer oder Kennzeichen des Boots|
|Klasse|Zugehörige Rennklasse|



## **3.3 Rennkonfiguration** 

|**3.3 Rennkonfguraton**||
|---|---|
|**Feld**|**Beschreibung**|
|Rennnummer|Eindeutige Identifikation des Rennens|
|Renndauer|Gesamtdauer in Minuten|
|Vorlaufzeit|Countdown vor Rennstart in Sekunden|
|Startlinien|Bezeichnungder Startlinie einschließlich Zeitoffset|
|Klassen-Zuordnung|Zuordnungvon Startlinien zu Rennklassen|



Die Excel-Struktur ist so aufzubauen, dass fachliche Daten ohne Eingriff in die Programmlogik gepflegt werden können. Pflichtfelder müssen vollständig befüllt sein, Wertebereiche eindeutig definiert werden und Zuordnungen zwischen Klassen, Startlinien und Rennen widerspruchsfrei vorliegen. Fehlerhafte oder unvollständige Konfigurationsdaten sind beim Einlesen zu erkennen und dem Benutzer verständlich anzuzeigen. 

## **4. Rennablauf** 

Nach dem Start der Applikation sucht das System nach einer geeigneten Excel-Datei und fordert den Benutzer zur Bestätigung der zu verwendenden Datenquelle auf. Anschließend werden die 
relevanten Konfigurations- und Stammdaten eingelesen, validiert und für die Rennsteuerung vorbereitet. Erst nach erfolgreicher Prüfung aller erforderlichen Daten darf ein Rennen zur Durchführung freigegeben werden. 

1. Auswahl des Rennens 

2. Start des Countdowns 

3. Freigabe des Rennstarts 

4. Erfassung der Rundenereignisse 

5. Einleitung und Verarbeitung des Rennendes 

Während der Vorstartphase werden Rennparameter, Startreihenfolge und zugehörige Klassen angezeigt, damit der Bediener letzte Plausibilitätsprüfungen durchführen kann. In der aktiven Rennphase werden alle Eingaben unmittelbar verarbeitet, visuell bestätigt und protokolliert. Nach Ablauf der regulären Renndauer wird in eine kontrollierte Abschlussphase gewechselt, in der die klassenweise Endlogik abgearbeitet und das finale Ergebnis vorbereitet wird. 

## **5. Rennlogik (Detail)** 

Jedes Boot erhält innerhalb eines Rennens einen eindeutigen Hotkey im Bereich von A bis Z. 

Die erste Runde wird aus der Differenz zwischen Startzeit und erster Zielpassage berechnet. 

Alle weiteren Runden werden auf Basis der Differenz zwischen zwei aufeinanderfolgenden Passagen ermittelt. 

Eine konfigurierbare Sperrzeit reduziert das Risiko von Doppelerfassungen und Fehlbedienungen. 

## **5.1 Ereignismodell** 

Jedes registrierte Ereignis besteht aus einem präzisen Zeitstempel, der zugeordneten Bootskennung sowie einem Eventtyp. Relevante Eventtypen sind insbesondere Start, Rundenpassage, Zieleinlauf und manuelle Korrektur. Alle Ereignisse werden in zeitlicher Reihenfolge gespeichert und für die spätere Auswertung herangezogen. 

## **5.2 Sperrzeit und Fehlbedienungsschutz** 

Zur Vermeidung unbeabsichtigter Doppelerfassungen wird nach jeder gültigen Eingabe eine konfigurierbare Sperrzeit je Boot aktiviert. Eingaben innerhalb dieses Zeitfensters werden als ungültig markiert, protokolliert und nicht für die Wertung berücksichtigt. 

Nach dem Rennstart wechselt das System in einen aktiven Betriebszustand. In diesem Zustand wird jeder Tastendruck mit einem Zeitstempel erfasst, um auch fehlerhafte oder versehentliche Eingaben vollständig nachvollziehbar zu dokumentieren und eine spätere manuelle Prüfung zu ermöglichen. 


## **5.3 Platzierung und Wertungslogik** 

Die Platzierung erfolgt primär anhand der Anzahl vollständig absolvierter Runden. Bei gleicher Rundenzahl entscheidet die geringere Gesamtzeit. Die letzte Runde einer Klasse wird gemäß Rennende-Logik abgeschlossen und vollständig in die Wertung einbezogen. 

Nach Renndauer beginnt klassenweise Endphase: 

- Die erste Zielpassage nach Ablauf der Renndauer markiert für die jeweilige Klasse die letzte Runde. 

- Alle weiteren Boote dieser Klasse beenden die bereits begonnene Runde regulär. 

## **6. Benutzeroberfläche (GUI)** 

|**Element**|**Beschreibung**|
|---|---|
|Start-Button|Startet das Rennen|
|Countdown-Anzeige|Anzeige der Vorstartzeit|
|Live-Tabelle|Anzeige von Booten,Runden und Zeiten|
|Manuell +1|Manuelle Korrektur einer Runde|



Rundenzeiten werden ausschließlich über entsprechende Hotkeys erfasst. 

## **6.1 Bedienkonzept** 

Die Anwendung ist auf eine schnelle, sichere und möglichst fehlerarme Bedienung ausgelegt. Zentrale Funktionen müssen ohne komplexe Mausinteraktionen erreichbar sein. Die Oberfläche soll auch unter Zeitdruck klar lesbar bleiben und Eingaben unmittelbar visuell bestätigen. 

Die Benutzeroberfläche muss wesentliche Zustände wie Vorstart, aktives Rennen, Sperrzeit, Fehlerhinweise und Rennende eindeutig visualisieren. Kritische Informationen wie verbleibende Renndauer, letzte erfasste Eingabe und aktuelle Platzierung sind so darzustellen, dass sie aus üblicher Bedienentfernung schnell erkennbar bleiben. Fehlermeldungen sind kurz, eindeutig und handlungsorientiert zu formulieren. 

## **7. Logging & Sicherheit** 

|**Typ**|**Beschreibung**|
|---|---|
|TXT-Blackbox|Unveränderliche Protokollierungaller Tastendrücke|
|Excel-Log|Strukturierte Erfassungder Rennereignisse|
|Error-Log|Protokollierungvon Applikationsfehlern|



Das Sicherheits- und Logging-Konzept verfolgt das Ziel, jede relevante Benutzeraktion und jeden Systemzustand nachvollziehbar zu dokumentieren. Rohdaten dürfen nicht unbemerkt verändert werden. Für Prüf- und Streitfälle muss eine eindeutige Rekonstruktion der Eingabereihenfolge, Zeitpunkte und Korrekturen möglich sein. Exportierte Ergebnisdaten sind klar von den ursprünglichen Erfassungsdaten zu trennen. 


## **8. Fehlertoleranz** 

Das System muss typische Störungen wie versehentliche Doppelerfassungen, fehlerhafte Tasteneingaben, unvollständige Konfigurationsdaten sowie unerwartete Unterbrechungen durch Stromausfall oder Programmabsturz beherrschbar machen. Für diese Fälle ist vorzusehen, dass ein Wiederanlauf auf Basis der vorhandenen Protokolle möglich bleibt und der Rennzustand soweit erforderlich nachvollzogen oder manuell fortgeführt werden kann. 

## **9. Nicht-funktionale Anforderungen** 

## **9.1 Stabilität** 

Das System muss über die gesamte Dauer einer Rennveranstaltung stabil ohne Neustart betrieben werden können. 

## **9.2 Performance** 

Die Reaktionszeit zwischen Benutzereingabe und sichtbarer Rückmeldung soll im Normalbetrieb unter 100 Millisekunden liegen. 

## **9.3 Offlinefähigkeit** 

Für den vollständigen Betrieb des Systems darf keine Internetverbindung erforderlich sein. Alle für das Rennen relevanten Daten müssen lokal verfügbar sein. 

## **9.4 Bedienbarkeit und Wartbarkeit** 

## **9.5 Sprach- und Bereitstellungsumfang** 

## **9.6 Plattform- und Softwarevoraussetzungen** 

Für die Ausführung der Anwendung ist ein aktuelles Windows-Betriebssystem erforderlich. Darüber hinaus muss eine installierte und lauffähige Microsoft-Excel-Version vorhanden sein, da Konfigurationsdaten, Vorlagen und ausgaberelevante Strukturen auf Excel basieren. Andere Betriebssysteme oder alternative Tabellenkalkulationsprogramme sind nicht Bestandteil des vorgesehenen Einsatzumfangs. 

Die Anwendung wird ausschließlich in deutscher Sprache ausgeliefert. Eine Mehrsprachigkeit der Benutzeroberfläche, Konfigurationsdateien oder Ausgabedokumente ist nicht Bestandteil des vereinbarten Lieferumfangs. Übersetzungen, sprachabhängige Umschaltfunktionen oder lokalisierte Varianten sind nicht vorgesehen. 

Die Anwendung ist so zu gestalten, dass geschulte Benutzer die Kernfunktionen ohne längere Einarbeitung sicher bedienen können. Konfigurationsänderungen an Rennen, Klassen und Layouts sollen überwiegend über die bereitgestellte Excel-Struktur erfolgen, damit 

Wartungsaufwände an der Programmlogik minimiert werden. Dokumentation, Benennung und Struktur der Datenfelder müssen konsistent und verständlich sein. 


## **10. Projektablauf & Versionierung** 

Der Projektablauf gliedert sich in eine initiale MVP-Umsetzung, eine anschließende Test- und Erprobungsphase im realitätsnahen Umfeld, die Einarbeitung identifizierter Verbesserungen sowie eine stufenweise funktionale Erweiterung. Die Versionierung soll nachvollziehbar dokumentieren, welche fachlichen und technischen Änderungen zwischen einzelnen Ständen vorgenommen wurden. 

## **11. Auslieferung** 

Die Auslieferung des Systems erfolgt als lauffähige ausführbare Anwendung sowie in Form der zugehörigen Excel-Konfigurationsdatei. Bestandteil der Bereitstellung sind die für den Betrieb erforderlichen Vorlagen für Startlisten und Ergebnisdarstellungen sowie eine kurze technische Einweisung in die grundlegende Nutzung. Voraussetzung für den produktiven Einsatz ist ein aktuelles Windows-System sowie eine installierte und betriebsbereite Microsoft-Excel-Version. 

Die Übergabe des Quellcodes kann optional vereinbart werden. Sofern eine Quellcodeübergabe erfolgt, sind Umfang, Nutzungsrechte, Haftungsgrenzen sowie Regelungen zu Wartung, Weiterentwicklung und Support gesondert festzulegen. 

## **12. Zusammenfassung** 

Das beschriebene Zeitnehmungs-System bildet die fachliche und technische Grundlage für eine zuverlässige, nachvollziehbare und praxisnahe Durchführung von Wasserski-Rennen. Durch die Trennung von Konfigurationsdaten und Laufzeitsystem, die robuste Protokollierung sowie die klare Bedienlogik ist das System für den Einsatz unter realen Wettkampfbedingungen geeignet und zugleich gezielt für spätere Erweiterungen vorbereitet. 

