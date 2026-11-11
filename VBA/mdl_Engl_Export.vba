Option Explicit


Sub FullExport()
    Dim v_res As Boolean
    v_res = ExportExpRangesToJSON
End Sub

' Für den externen Aufruf :
Function ExportExpRangesToJSON() As Boolean
    On Error GoTo ErrorHandler
    
    Dim v_file As String
    Dim v_error As String
    
    ExpRangesToJSON v_file, v_error
    
    If (v_error <> "") Then
        'Excel.StatusBar = "ERROR:" & v_error
        ExportExpRangesToJSON = False
        Exit Function
    End If
    
    
    If (v_file <> "") Then
           MsgBox "Export erfolgreich als abgeschlossen!" & vbCrLf & _
                  "Datei gespeichert unter:" & v_file, vbInformation, "JSON Export (UTF-8)"
           ExportExpRangesToJSON = True
        Exit Function
    End If
    
ErrorHandler:
    ExportExpRangesToJSON = False
    ' Fehlermeldung in StatusBar (Python kann es lesen)
    Application.StatusBar = "ERROR: " & Err.Description
End Function

Sub ExpRangesToJSON(ByRef o_file As String, ByRef o_error As String)

    Dim nm As Name
    Dim jsonResult As String
    Dim rangeJson As String
    Dim cleanName As String
    Dim firstItem As Boolean
    Dim filePath As String
    
    ' Start der JSON-Struktur
    jsonResult = "{" & vbCrLf
    firstItem = True
    
    ' Schleife über alle benannten Bereiche der Arbeitsmappe
    For Each nm In ThisWorkbook.Names
        ' Prüfen, ob der Name mit _EXP_ beginnt (Länge von _EXP_ ist 5 Zeichen)
        If UCase(Left(nm.Name, 5)) = "_EXP_" Then
            
            ' Name bereinigen (Präfix weg und in Kleinbuchstaben)
            cleanName = LCase(Mid(nm.Name, 6))
            
            ' Range-Daten in JSON-String konvertieren
            rangeJson = RangeToJSONString(nm.RefersToRange)
            
            ' Komma-Trennung für gültiges JSON setzen
            If Not firstItem Then
                jsonResult = jsonResult & "," & vbCrLf
            Else
                firstItem = False
            End If
            
            ' Key-Value-Paar hinzufügen
            jsonResult = jsonResult & "  """ & cleanName & """: " & rangeJson
        End If
    Next nm
    
    jsonResult = jsonResult & vbCrLf & "}"
    
    ' Speicherpfad definieren (gleicher Ordner wie die Excel-Datei)
    Dim localFolder As String
    localFolder = GetLocalPath(ThisWorkbook.Path)
    filePath = localFolder & "\IMPORT.json"
        
    ' --- NEU: UTF-8 EXPORT VIA ADODB.STREAM ---
    On Error GoTo ErrorHandler
    Dim utf8Stream As Object
    Set utf8Stream = CreateObject("ADODB.Stream")
    
    With utf8Stream
        .Type = 2 ' 2 = adTypeText (Textmodus)
        .Charset = "UTF-8"
        .Open
        .WriteText jsonResult
        .SaveToFile filePath, 2 ' 2 = adSaveCreateOverWrite (Überschreiben falls existiert)
        .Close
    End With
    
    o_error = ""
    o_file = filePath
   
   Exit Sub
   
ErrorHandler:
    o_error = Err.Description
    o_file = ""
    
    
End Sub


' Hilfsfunktion: Konvertiert eine Excel-Range in einen JSON-String
Function RangeToJSONString(rng As Range) As String
    Dim rowData As String
    Dim allRowsData As String
    Dim cellValue As String
    Dim r As Long, c As Long
    Dim cellData As String
    Dim cell As Range
    Dim firstCell As Boolean
    
    ' Fall 1: Eindimensionale Liste (nur 1 Zeile oder nur 1 Spalte) -> Einfaches Array []
    If rng.Rows.Count = 1 Or rng.Columns.Count = 1 Then
        firstCell = True
        allRowsData = "["
        For Each cell In rng
            If Not firstCell Then allRowsData = allRowsData & ", "
            firstCell = False
            allRowsData = allRowsData & FormatValueForJSON(cell.Value)
        Next cell
        allRowsData = allRowsData & "]"
        RangeToJSONString = allRowsData
        Exit Function
    End If
    
    ' Fall 2: Zweidimensionale Tabelle -> Array von Objekten [{ "Header": "Wert" }]
    allRowsData = "[" & vbCrLf
    For r = 2 To rng.Rows.Count
        rowData = "    {"
        For c = 1 To rng.Columns.Count
            Dim headerName As String
            ' Nutzt die erste Zeile der Range als JSON-Schlüssel (Key)
            headerName = CStr(rng.Cells(1, c).Value)
            If headerName = "" Then headerName = "spalte" & c
            
            cellValue = FormatValueForJSON(rng.Cells(r, c).Value)
            cellData = """" & EscapeJSONString(headerName) & """: " & cellValue
            
            If c > 1 Then rowData = rowData & ", "
            rowData = rowData & cellData
        Next c
        rowData = rowData & "}"
        
        If r > 2 Then allRowsData = allRowsData & "," & vbCrLf
        allRowsData = allRowsData & rowData
    Next r
    
    allRowsData = allRowsData & vbCrLf & "  ]"
    RangeToJSONString = allRowsData
End Function

' Hilfsfunktion: Formatiert Datentypen korrekt für JSON (Zahlen ohne Anführungszeichen, Boolean, null)
Function FormatValueForJSON(val As Variant) As String
    If IsEmpty(val) Then
        FormatValueForJSON = "null"
    Else
        Select Case VarType(val)
            Case vbBoolean
                If val Then FormatValueForJSON = "true" Else FormatValueForJSON = "false"
            Case vbInteger, vbLong, vbSingle, vbDouble, vbCurrency
                ' Stellt sicher, dass Punkte statt Kommas für Dezimalzahlen genutzt werden
                FormatValueForJSON = Replace(CStr(val), ",", ".")
            Case vbDate
                FormatValueForJSON = """" & Format(val, "yyyy-mm-dd") & """"
            Case Else
                FormatValueForJSON = """" & EscapeJSONString(CStr(val)) & """"
        End Select
    End If
End Function

' Hilfsfunktion: Maskiert Sonderzeichen und Anführungszeichen innerhalb von Strings
Function EscapeJSONString(str As String) As String
    Dim res As String
    res = Replace(str, "\", "\\")
    res = Replace(res, """", "\""")
    res = Replace(res, vbCrLf, "\n")
    res = Replace(res, vbCr, "\n")
    res = Replace(res, vbLf, "\n")
    res = Replace(res, vbTab, "\t")
    EscapeJSONString = res
End Function


' Hilfsfunktion: Konvertiert eine OneDrive HTTPS-URL in den lokalen Windows-Pfad
Function GetLocalPath(ByVal folderPath As String) As String
    Dim localOneDrive As String
    Dim cleanPath As String
    Dim subPathPos As Long
    
    ' Lokalen OneDrive-Pfad aus den Windows-Umgebungsvariablen auslesen
    ' (Gibt automatisch z.B. "C:\Users\xx\OneDrive" zurück)
    localOneDrive = Environ("OneDrive")
    If localOneDrive = "" Then localOneDrive = Environ("USERPROFILE") & "\OneDrive"
    
    ' Prüfen, ob es sich um einen OneDrive-Weblink handelt
    If InStr(1, folderPath, "https://", vbTextCompare) > 0 Then
        ' Schrägstriche für Windows vereinheitlichen
        cleanPath = Replace(folderPath, "/", "\")
        
        ' Fall 1: d.docs.live.net (Persönliches OneDrive)
        If InStr(1, cleanPath, "d.docs.live.net", vbTextCompare) > 0 Then
            ' Wir müssen die eindeutige ID (die 16 Zeichen nach d.docs.live.net\) überspringen
            ' Beispiel: https:\\d.docs.live.net\0bce81ec0824c784\DEV\Waterski\Excel
            subPathPos = InStr(cleanPath, "d.docs.live.net\") + 16 ' Länge der Domain inkl. Slash
            cleanPath = Mid(cleanPath, subPathPos)
            
            ' Jetzt die hexadezimale ID überspringen (die nächste Ebene nach dem Slash)
            subPathPos = InStr(cleanPath, "\")
            If subPathPos > 0 Then
                cleanPath = Mid(cleanPath, subPathPos) ' Behält "\DEV\Waterski\Excel"
            End If
            
        ' Fall 2: SharePoint oder OneDrive for Business (.sharepoint.com)
        ElseIf InStr(1, cleanPath, ".sharepoint.com", vbTextCompare) > 0 Then
            ' Schneidet den Server-Teil ab und sucht den ersten echten Unterordner
            ' (Häufig "sites" oder "personal")
            subPathPos = InStr(cleanPath, "\personal\")
            If subPathPos = 0 Then subPathPos = InStr(cleanPath, "\sites\")
            
            If subPathPos > 0 Then
                cleanPath = Mid(cleanPath, subPathPos)
                ' Weitere Standard-SharePoint-Ordnerstrukturen überspringen
                ' (Überspringt z.B. den Benutzernamen im Personal-Pfad)
                Dim i As Integer
                For i = 1 To 3
                    subPathPos = InStr(2, cleanPath, "\")
                    If subPathPos > 0 Then cleanPath = Mid(cleanPath, subPathPos)
                Next i
            End If
        End If
        
        ' HTML-Codierungen wie %20 (Leerzeichen) wieder in echten Text umwandeln
        cleanPath = Replace(cleanPath, "%20", " ")
        
        ' Den lokalen Basis-Pfad mit dem extrahierten Unterordner verknüpfen
        GetLocalPath = localOneDrive & cleanPath
    Else
        ' Falls es bereits ein lokaler Pfad war, einfach unverändert zurückgeben
        GetLocalPath = folderPath
    End If
End Function


