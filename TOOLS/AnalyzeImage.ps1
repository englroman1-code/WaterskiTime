# TOOLS\AnalyzeImage.ps1 - Bildanalyse per Vision-Modell (OpenRouter)
#
# Verhalten (kostenoptimiert):
#   1. Zuerst ein KOSTENLOSES Vision-Modell (google/gemma-4-31b-it:free)
#   2. Nur bei Fehler / 429 / leerer Antwort -> Fallback auf kostenpflichtiges
#      google/gemini-2.5-flash (wie im Design-Wizard, ~0.0003 $ je Aufruf)
#
# API-Key: getrennte Konten fuer klare Kosten-Trennung:
#   1. Script-Key aus AI_Usage.md (OpenWork/TOOLS-Konsumation, gitignored)
#   2. Fallback: Umgebungsvariable OPENROUTER_API_KEY
#   3. Fallback: App-Key aus web\.env (tischl.at-Produktionskonsumation) - nur
#      als Notloesung, eine Warnung wird ausgegeben
# NIE einen Key direkt in dieser Datei eintragen!
#
# Aufruf:
#   .\TOOLS\AnalyzeImage.ps1 -ImageName "screenshot.png"
#   .\TOOLS\AnalyzeImage.ps1 -ImageName "skizze.jpg" -Prompt "Beschreibe die Tisch-Planung"
#   .\TOOLS\AnalyzeImage.ps1 -ImageName "bild.png" -ForcePaid   # direkt kostenpflichtig

param(
    [Parameter(Mandatory = $true)][string]$ImageName,
    [string]$Prompt = "",
    [switch]$ForcePaid
)

# --- Pfad-Magie: Skript liegt in TOOLS\, Projekt-Root ist eine Ebene hoeher ---------
$ScriptFolder = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (($ScriptFolder -split '\\' | Select-Object -Last 1) -eq "Tools") {
    $ProjectRoot = Split-Path -Parent $ScriptFolder
} else {
    $ProjectRoot = $ScriptFolder
}

# --- Bild im Projekt-Root suchen ----------------------------------------------------
$ImagePath = Join-Path $ProjectRoot $ImageName
if (-not (Test-Path $ImagePath)) {
    Write-Error "Bild '$ImageName' wurde im Projektordner '$ProjectRoot' nicht gefunden."
    exit 1
}

# --- API-Key: AI_Usage.md -> Umgebungsvariable -> web\.env --------------------------
function Get-KeyFromDotEnvFile {
    param([string]$FilePath, [string]$VarName)
    if (-not (Test-Path $FilePath)) { return $null }
    foreach ($line in Get-Content $FilePath) {
        if ($line -match "^$VarName=(.+)$") { return $matches[1].Trim() }
    }
    return $null
}

function Get-OpenRouterApiKey {
    param([string]$Root)

    # 1) Script-Key aus AI_Usage.md (erste sk-or-v1-Zeile im Code-Block)
    $aiUsage = Join-Path $Root "AI_Usage.md"
    if (Test-Path $aiUsage) {
        $inBlock = $false
        foreach ($line in Get-Content $aiUsage) {
            if ($line -match '^```') { $inBlock = -not $inBlock; continue }
            if ($inBlock -and $line -match '^sk-or-v1-[0-9a-f]+') {
                return @{ Key = $line.Trim(); Source = "AI_Usage.md (Script-Key)" }
            }
        }
    }

    # 2) Umgebungsvariable
    $envKey = $env:OPENROUTER_API_KEY
    if ($envKey) { return @{ Key = $envKey.Trim(); Source = "Umgebungsvariable OPENROUTER_API_KEY" } }

    # 3) App-Key aus web\.env (Notloesung - vermischt die Konsumation!)
    $appKey = Get-KeyFromDotEnvFile -FilePath (Join-Path $Root "web\.env") -VarName "OPENROUTER_API_KEY"
    if ($appKey) {
        Write-Warning "Kein Script-Key in AI_Usage.md gefunden - nutze App-Key aus web\.env (Konsumation auf tischl.at-Konto!)."
        return @{ Key = $appKey; Source = "web\.env (App-Key, Notloesung)" }
    }

    return $null
}

$KeyInfo = Get-OpenRouterApiKey -Root $ProjectRoot
if (-not $KeyInfo) {
    Write-Error "Kein OpenRouter-Key gefunden. Script-Key in AI_Usage.md eintragen oder OPENROUTER_API_KEY als Umgebungsvariable setzen."
    exit 1
}
$ApiKey = $KeyInfo.Key
Write-Host "-> Key-Quelle: $($KeyInfo.Source)"

# --- Bild in Base64 ------------------------------------------------------------------
$Bytes = [System.IO.File]::ReadAllBytes($ImagePath)
$Base64Image = [Convert]::ToBase64String($Bytes)
$MimeType = "image/png"
if ($ImageName -match "\.jpg$|\.jpeg$") { $MimeType = "image/jpeg" }
if ($ImageName -match "\.webp$") { $MimeType = "image/webp" }

# --- Default-Prompt (generisch, per -Prompt uebersteuerbar) ----------------------------
if (-not $Prompt) {
    $Prompt = "Beschreibe das Bild detailliert auf Deutsch. Transkribiere allen sichtbaren Text vollstaendig und korrekt. Nenne die wichtigsten Farben, den Stil und erklaere die Struktur bzw. den Aufbau des Bildes."
}

$Uri = "https://openrouter.ai/api/v1/chat/completions"
$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type"  = "application/json"
}

$FreeModel = "google/gemma-4-31b-it:free"
$PaidModel = "google/gemini-2.5-flash"

function Invoke-VisionRequest {
    param([string]$Model, [string]$PromptText, [string]$DataUrl, [hashtable]$ReqHeaders)

    $Body = @{
        model = $Model
        messages = @(
            @{
                role = "user"
                content = @(
                    @{ type = "text"; text = $PromptText },
                    @{ type = "image_url"; image_url = @{ url = $DataUrl } }
                )
            }
        )
    } | ConvertTo-Json -Depth 10

    $params = @{ Uri = $Uri; Method = "Post"; Headers = $ReqHeaders; Body = $Body }
    # -TimeoutSec gibt es erst ab PowerShell 6
    if ($PSVersionTable.PSVersion.Major -ge 6) { $params.TimeoutSec = 150 }

    try {
        $Response = Invoke-RestMethod @params
        $text = $Response.choices[0].message.content
        if (-not $text) {
            return @{ Ok = $false; Model = $Model; Reason = "leere Antwort" }
        }
        return @{ Ok = $true; Model = $Response.model; Text = $text }
    } catch {
        $status = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        $reason = "HTTP " + $status + " " + $_.Exception.Message
        return @{ Ok = $false; Model = $Model; Reason = $reason }
    }
}

$DataUrl = "data:$MimeType;base64,$Base64Image"

# --- 1. Versuch: kostenloses Modell -----------------------------------------------------
$Result = $null
if (-not $ForcePaid) {
    Write-Host "-> Free-Modell: $FreeModel"
    $Result = Invoke-VisionRequest -Model $FreeModel -PromptText $Prompt -DataUrl $DataUrl -ReqHeaders $Headers
    if ($Result.Ok) {
        Write-Host "   OK ($($Result.Model))"
    } else {
        Write-Host "   Fehlgeschlagen: $($Result.Reason)"
        Write-Host "   -> Fallback auf kostenpflichtiges Modell: $PaidModel"
    }
}

# --- 2. Fallback: kostenpflichtiges Modell ------------------------------------------------
if (-not $Result -or -not $Result.Ok) {
    $Result = Invoke-VisionRequest -Model $PaidModel -PromptText $Prompt -DataUrl $DataUrl -ReqHeaders $Headers
    if ($Result.Ok) {
        Write-Host "   OK ($($Result.Model))"
    }
}

# --- Ergebnis: speichern nach _BOTBRAIN\ + Konsole ---------------------------------------
if (-not $Result.Ok) {
    Write-Error "Bildanalyse fehlgeschlagen (auch kostenpflichtiges Modell): $($Result.Reason)"
    exit 1
}

$BaseName = [System.IO.Path]::GetFileNameWithoutExtension($ImageName)
$BotBrain = Join-Path $ProjectRoot "_BOTBRAIN"
if (-not (Test-Path $BotBrain)) { New-Item -ItemType Directory -Path $BotBrain -Force | Out-Null }
$OutputFile = Join-Path $BotBrain "$BaseName.txt"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($OutputFile, $Result.Text, $Utf8NoBom)

Write-Host ""
Write-Host "Erfolgreich! Modell: $($Result.Model)"
Write-Host "Analyse gespeichert: $OutputFile"
Write-Host "--- Analyse (Auszug) ---"
$Preview = $Result.Text
if ($Preview.Length -gt 800) { $Preview = $Preview.Substring(0, 800) + " [...]" }
Write-Host $Preview
