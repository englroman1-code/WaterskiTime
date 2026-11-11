Option Explicit

Type logrec
    Eventtime As Date
    Action As String
    BoatHotKey As String
    Status As String
End Type

Private Enum ResultFieldType
    rftInteger = 1
    rftDecimal2 = 2
    rftText = 3
    rftDuration = 4
    rftPercent = 5
End Enum


Sub MainJsonImport()

    Dim jsonFile As String, jsonText As String
    Dim wsResults As Worksheet, wsLog As Worksheet

    ' --- JSON-Datei über Dialog auswählen (startet im Excel-Ordner) ---
    With Application.FileDialog(msoFileDialogFilePicker)
        .Title = "Bitte die JSON-Ergebnisdatei auswählen"
        .Filters.Clear
        .Filters.Add "JSON-Dateien", "*.json"
        .InitialFileName = GetLocalPath(ThisWorkbook.Path & "\")
        If .Show = False Then Exit Sub
        jsonFile = .SelectedItems(1)
    End With

    jsonText = ReadUtf8TextFile(jsonFile)

    ' --- JSON PARSEN ---
    Dim json As Object
    Set json = JsonConverter.ParseJson(jsonText)

    ' --- Blätter vorbereiten und alte Daten löschen ---
    On Error Resume Next
    Set wsResults = ThisWorkbook.Sheets("results")
    If wsResults Is Nothing Then
        Set wsResults = ThisWorkbook.Sheets.Add(Before:=ThisWorkbook.Sheets(1))
        wsResults.Name = "results"
    End If
    
    Set wsLog = ThisWorkbook.Sheets("log")
    If wsLog Is Nothing Then
        Set wsLog = ThisWorkbook.Sheets.Add(After:=wsResults)
        wsLog.Name = "log"
    End If
    On Error GoTo 0

    wsResults.Cells.Clear
    wsLog.Cells.Clear

    ' Überschriften schreiben & Tabellen leeren
    wsResults.Range("A1:O1").Value = Array( _
        "Platz", "Boot-Nr", "Klasse", "Läufer (Skier)", "Team", "Club", _
        "Renn-Nr", "Runden", "Gesamtzeit", "Beste Runde", "Distanz [km]", _
        "Ø Speed [km/h]", "Rennzeit", "Strafen", "Punkte")

    wsLog.Range("A1:H1").Value = Array( _
        "Renn-Nr", "Eintrag-Nr", "Log-Eintrag", "Zeitpunkt", "Aktion", "Boot", "Status", "Detail")

    ' Neues Format (write_all_races): event + races[] mit classes[]/results[]
    If HasKey(json, "races") Then
        ImportResultFromRaces json("races"), wsResults
        ImportLogFromRaces json("races"), wsLog
    Else
        ' Legacy-Format (write): race_number + results[] + log[]
        ImportResultLegacy json, wsResults
        ImportLogLegacy json, wsLog
    End If

    ApplyPointsFormulas wsResults

    wsResults.Columns.AutoFit
    wsLog.Columns.AutoFit

    MsgBox "Import erfolgreich abgeschlossen!", vbInformation, "JSON-Import"
End Sub

' --- Neues Format: races[] -> classes[] -> results[] ---
Sub ImportResultFromRaces(ByRef races As Object, ByVal ws As Worksheet)
    Dim raceItem As Object
    Dim classItem As Object
    Dim resultItem As Object
    Dim row As Long

    row = 2

    For Each raceItem In races
        If HasKey(raceItem, "classes") Then
            For Each classItem In raceItem("classes")
                If HasKey(classItem, "results") Then
                    For Each resultItem In classItem("results")
                        WriteResultRow ws, row, resultItem, GetVariantSafe(raceItem, "race_number")
                        row = row + 1
                    Next resultItem
                End If
            Next classItem
        End If
    Next raceItem
End Sub

' --- Legacy-Format: results[] direkt auf Root-Ebene ---
Sub ImportResultLegacy(ByRef json As Object, ByVal ws As Worksheet)
    Dim resultItem As Object
    Dim row As Long

    row = 2

    If Not HasKey(json, "results") Then Exit Sub

    For Each resultItem In json("results")
        WriteResultRow ws, row, resultItem, GetVariantSafe(json, "race_number")
        row = row + 1
    Next resultItem
End Sub

Private Sub WriteResultRow(ByVal ws As Worksheet, ByVal row As Long, ByVal resultItem As Object, ByVal defaultRaceNumber As Variant)
    Static fieldMap As Collection
    Dim spec As Variant
    Dim rawValue As Variant

    If fieldMap Is Nothing Then
        Set fieldMap = BuildResultFieldMap()
    End If

    For Each spec In fieldMap
        rawValue = ResolveResultValue(resultItem, CStr(spec(0)), defaultRaceNumber)
        WriteResultCell ws.Cells(row, CLng(spec(1))), rawValue, CLng(spec(2)), CStr(spec(3))
    Next spec
End Sub

Private Function BuildResultFieldMap() As Collection
    Dim fieldMap As Collection
    Set fieldMap = New Collection

    ' Spezifikation: Array(JsonKey, ExcelSpalte, ResultFieldType, NumberFormat)
    fieldMap.Add Array("place", 1, rftInteger, "0")
    fieldMap.Add Array("boat_nr", 2, rftInteger, "0")
    fieldMap.Add Array("klasse", 3, rftText, "@")
    fieldMap.Add Array("skier", 4, rftText, "@")
    fieldMap.Add Array("team", 5, rftText, "@")
    fieldMap.Add Array("club", 6, rftText, "@")
    fieldMap.Add Array("race_number", 7, rftInteger, "0")
    fieldMap.Add Array("laps", 8, rftInteger, "0")
    fieldMap.Add Array("total_time", 9, rftDuration, GetDurationNumberFormat())
    fieldMap.Add Array("best_lap", 10, rftDuration, GetDurationNumberFormat())
    fieldMap.Add Array("distance", 11, rftDecimal2, "0.00")
    fieldMap.Add Array("avg_speed", 12, rftDecimal2, "0.00")
    fieldMap.Add Array("race_time", 13, rftDuration, GetDurationNumberFormat())
    fieldMap.Add Array("penalties", 14, rftPercent, "0.00%")
    fieldMap.Add Array("points", 15, rftInteger, "0")

    Set BuildResultFieldMap = fieldMap
End Function

Private Sub ApplyPointsFormulas(ByVal ws As Worksheet)
    Dim lastRow As Long
    Dim row As Long

    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).row
    If lastRow < 2 Then Exit Sub

    For row = 2 To lastRow
        ws.Cells(row, 15).NumberFormat = "0"
        ws.Cells(row, 15).Formula = BuildPointsFormula(row, lastRow)
    Next row
End Sub

Private Function BuildPointsFormula(ByVal row As Long, ByVal lastRow As Long) As String
    ' Punkte = (Bestzeit der Klasse+Rennen / eigene Rennzeit) * (1 - penalty) * 1000
    ' Optimierung: LET vermeidet doppelte MINIFS-Berechnung.
    BuildPointsFormula = "=LET(best,MINIFS($M$2:$M$" & lastRow & ",$C$2:$C$" & lastRow & ",C" & row & ",$G$2:$G$" & lastRow & ",G" & row & "),pen,IFERROR(N" & row & ",0),base,IFERROR(best/M" & row & ",0),ROUND(base*(1-pen)*1000,0))"
End Function

Private Function ResolveResultValue(ByVal resultItem As Object, ByVal jsonKey As String, ByVal defaultRaceNumber As Variant) As Variant
    If jsonKey = "race_number" Then
        If HasKey(resultItem, "race_number") Then
            ResolveResultValue = GetVariantSafe(resultItem, "race_number")
        Else
            ResolveResultValue = defaultRaceNumber
        End If
        Exit Function
    End If

    ResolveResultValue = GetVariantSafe(resultItem, jsonKey)
End Function

Private Sub WriteResultCell(ByVal target As Range, ByVal rawValue As Variant, ByVal fieldType As ResultFieldType, ByVal numberFormat As String)
    Dim parsedValue As Variant

    target.NumberFormat = numberFormat

    Select Case fieldType
        Case rftText
            If IsValueMissing(rawValue) Then
                target.Value = ""
            Else
                target.Value = CStr(rawValue)
            End If

        Case rftInteger
            parsedValue = TryParseLong(rawValue)
            If IsEmpty(parsedValue) Then
                target.Value = ""
            Else
                target.Value = parsedValue
            End If

        Case rftDecimal2
            parsedValue = TryParseDouble(rawValue)
            If IsEmpty(parsedValue) Then
                target.Value = ""
            Else
                target.Value = parsedValue
            End If

        Case rftDuration
            parsedValue = ParseDurationToExcelSerial(rawValue)
            If IsEmpty(parsedValue) Then
                target.Value = ""
            Else
                target.Value = parsedValue
            End If

        Case rftPercent
            parsedValue = TryParseDouble(rawValue)
            If IsEmpty(parsedValue) Then
                target.Value = ""
            Else
                ' Falls 5 statt 0.05 geliefert wird, auf Prozentwert normalisieren.
                If parsedValue > 1# Then parsedValue = parsedValue / 100#
                target.Value = parsedValue
            End If

        Case Else
            target.Value = ToCellValue(rawValue)
    End Select
End Sub

Private Function GetDurationNumberFormat() As String
    ' Invariantes Format; Excel zeigt je Region automatisch den passenden Trenner.
    GetDurationNumberFormat = "[m]:ss.00"
End Function

Private Function ParseDurationToExcelSerial(ByVal rawValue As Variant) As Variant
    Dim txt As String
    Dim parts() As String
    Dim h As Long
    Dim m As Long
    Dim s As Double
    Dim totalSeconds As Double

    If IsValueMissing(rawValue) Then
        ParseDurationToExcelSerial = Empty
        Exit Function
    End If

    txt = Trim(CStr(rawValue))
    If Len(txt) = 0 Then
        ParseDurationToExcelSerial = Empty
        Exit Function
    End If

    parts = Split(txt, ":")
    On Error GoTo Fehler

    Select Case UBound(parts)
        Case 1
            m = CLng(parts(0))
            s = ParseInvariantDouble(parts(1))
            totalSeconds = (m * 60#) + s
        Case 2
            h = CLng(parts(0))
            m = CLng(parts(1))
            s = ParseInvariantDouble(parts(2))
            totalSeconds = (h * 3600#) + (m * 60#) + s
        Case Else
            GoTo Fehler
    End Select

    ParseDurationToExcelSerial = totalSeconds / 86400#
    Exit Function

Fehler:
    ParseDurationToExcelSerial = Empty
End Function

Private Function TryParseLong(ByVal rawValue As Variant) As Variant
    Dim txt As String

    If IsValueMissing(rawValue) Then
        TryParseLong = Empty
        Exit Function
    End If

    txt = Trim(CStr(rawValue))
    If Len(txt) = 0 Then
        TryParseLong = Empty
        Exit Function
    End If

    On Error GoTo Fehler
    TryParseLong = CLng(ParseInvariantDouble(txt))
    Exit Function

Fehler:
    TryParseLong = Empty
End Function

Private Function TryParseDouble(ByVal rawValue As Variant) As Variant
    Dim txt As String

    If IsValueMissing(rawValue) Then
        TryParseDouble = Empty
        Exit Function
    End If

    txt = Trim(CStr(rawValue))
    If Len(txt) = 0 Then
        TryParseDouble = Empty
        Exit Function
    End If

    On Error GoTo Fehler
    TryParseDouble = ParseInvariantDouble(txt)
    Exit Function

Fehler:
    TryParseDouble = Empty
End Function

Private Function ParseInvariantDouble(ByVal txt As String) As Double
    Dim normalized As String

    normalized = Trim$(txt)
    normalized = Replace(normalized, ",", ".")

    ' Val ist locale-unabhängig und interpretiert den Punkt als Dezimaltrenner.
    ParseInvariantDouble = Val(normalized)
End Function

Private Function IsValueMissing(ByVal rawValue As Variant) As Boolean
    If IsEmpty(rawValue) Then
        IsValueMissing = True
        Exit Function
    End If

    If IsNull(rawValue) Then
        IsValueMissing = True
        Exit Function
    End If

    IsValueMissing = (Trim(CStr(rawValue)) = "")
End Function

' --- Neues Format: races[] -> log[] ---
Sub ImportLogFromRaces(ByRef races As Object, ByVal ws As Worksheet)
    Dim raceItem As Object
    Dim logEntry As Variant
    Dim row As Long
    Dim logCounter As Long
    Dim v_logrec As logrec

    row = 2

    For Each raceItem In races
        logCounter = 1

        If HasKey(raceItem, "log") Then
            For Each logEntry In raceItem("log")
                v_logrec = ParseLogLine(CStr(logEntry))

                ws.Cells(row, 1).Value = ToCellValue(GetVariantSafe(raceItem, "race_number"))
                ws.Cells(row, 2).Value = logCounter
                ws.Cells(row, 3).Value = CStr(logEntry)
                ws.Cells(row, 4).Value = v_logrec.Eventtime
                ws.Cells(row, 5).Value = v_logrec.Action
                ws.Cells(row, 6).Value = v_logrec.BoatHotKey
                ws.Cells(row, 7).Value = v_logrec.Status
                ws.Cells(row, 8).Value = ExtractLogDetail(CStr(logEntry))

                logCounter = logCounter + 1
                row = row + 1
            Next logEntry
        End If
    Next raceItem
End Sub

' --- Legacy-Format: log[] direkt auf Root-Ebene ---
Sub ImportLogLegacy(ByRef json As Object, ByVal ws As Worksheet)
    Dim logEntry As Variant
    Dim row As Long
    Dim logCounter As Long
    Dim v_logrec As logrec
    Dim raceNr As Variant

    row = 2
    logCounter = 1
    raceNr = GetVariantSafe(json, "race_number")

    If Not HasKey(json, "log") Then Exit Sub

    For Each logEntry In json("log")
        v_logrec = ParseLogLine(CStr(logEntry))

        ws.Cells(row, 1).Value = ToCellValue(raceNr)
        ws.Cells(row, 2).Value = logCounter
        ws.Cells(row, 3).Value = CStr(logEntry)
        ws.Cells(row, 4).Value = v_logrec.Eventtime
        ws.Cells(row, 5).Value = v_logrec.Action
        ws.Cells(row, 6).Value = v_logrec.BoatHotKey
        ws.Cells(row, 7).Value = v_logrec.Status
        ws.Cells(row, 8).Value = ExtractLogDetail(CStr(logEntry))

        logCounter = logCounter + 1
        row = row + 1
    Next logEntry
End Sub

Function ParseLogLine(ByVal logString As String) As logrec
    Dim result As logrec
    Dim tempTime As String

    Dim v_start As Long
    Dim v_end As Long

    On Error GoTo FehlerHandler

    ' 1. Zeitpunkt extrahieren und in ein echtes Datum konvertieren
    v_start = InStr(1, logString, "[")
    v_end = InStr(1, logString, "]")
    If v_start > 0 And v_end > v_start Then
        tempTime = Mid(logString, v_start + 1, v_end - v_start - 1)
        If Len(tempTime) >= 19 Then
            result.Eventtime = CDate(Left(tempTime, 19))
        End If
    End If

    ' 2. Aktion extrahieren
    v_start = InStr(1, logString, "]")
    If v_start > 0 Then
        v_end = InStr(v_start, logString, ":")
        If v_end > v_start Then
            result.Action = Trim(Mid(logString, v_start + 1, v_end - v_start - 1))
        End If
    End If

    ' 3. Boot extrahieren (falls vorhanden)
    v_start = InStr(1, logString, "Boot=")
    If v_start > 0 Then
        v_start = v_start + 5
        v_end = InStr(v_start, logString, ";")
        If v_end = 0 Then v_end = InStr(v_start, logString, " ")
        If v_end = 0 Then v_end = Len(logString) + 1
        result.BoatHotKey = Mid(logString, v_start, v_end - v_start)
    Else
        result.BoatHotKey = ""
    End If

    ' 4. Status extrahieren
    v_start = InStr(1, logString, "STATUS:")
    If v_start > 0 Then
        result.Status = Trim(Mid(logString, v_start + 7))
    Else
        result.Status = ""
    End If

    ParseLogLine = result
    Exit Function

FehlerHandler:
    ' Im Fehlerfall wird ein leerer Record zurückgegeben (kein Abbruch)
    ParseLogLine = result
End Function

Private Function ExtractLogDetail(ByVal logString As String) As String
    Dim closeBracketPos As Long
    Dim colonPos As Long
    Dim statusPos As Long
    Dim detailText As String

    closeBracketPos = InStr(1, logString, "]")
    If closeBracketPos = 0 Then
        ExtractLogDetail = ""
        Exit Function
    End If

    ' Das Detail beginnt nach dem Aktions-Doppelpunkt, nicht nach der Uhrzeit.
    colonPos = InStr(closeBracketPos + 1, logString, ":")
    If colonPos = 0 Then
        ExtractLogDetail = ""
        Exit Function
    End If

    statusPos = InStr(colonPos + 1, logString, "STATUS:")
    If statusPos > 0 Then
        detailText = Trim(Mid(logString, colonPos + 1, statusPos - colonPos - 1))
    Else
        detailText = Trim(Mid(logString, colonPos + 1))
    End If

    ExtractLogDetail = detailText
End Function

Private Function ReadUtf8TextFile(ByVal filePath As String) As String
    Dim stream As Object

    Set stream = CreateObject("ADODB.Stream")
    stream.Type = 2
    stream.Charset = "UTF-8"
    stream.Open
    stream.LoadFromFile filePath
    ReadUtf8TextFile = stream.ReadText
    stream.Close
End Function

Private Function HasKey(ByVal dictObj As Object, ByVal key As String) As Boolean
    On Error GoTo Fehler
    HasKey = CBool(CallByName(dictObj, "Exists", VbMethod, key))
    Exit Function
Fehler:
    HasKey = False
End Function

Private Function GetVariantSafe(ByVal dictObj As Object, ByVal key As String) As Variant
    If HasKey(dictObj, key) Then
        GetVariantSafe = dictObj(key)
    Else
        GetVariantSafe = Empty
    End If
End Function

Private Function ToCellValue(ByVal value As Variant) As Variant
    If IsEmpty(value) Or IsNull(value) Then
        ToCellValue = ""
    Else
        ToCellValue = value
    End If
End Function

