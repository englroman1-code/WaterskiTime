import os
import glob
import json
from datetime import datetime

def log_event(component, message, level="INFO", context=None):
    """Protokolliert Ereignisse in current.log und Fehler in error.log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} [{level}] [{component}] {message}"
    
    if context:
        entry += f" | {json.dumps(context)}"
    
    # Schreibe in current.log
    with open('current.log', 'a') as f:
        f.write(entry + "\n")
    
    # Schreibe Fehler zusätzlich in error.log
    if level in ["ERROR", "CRITICAL"]:
        with open('error.log', 'a') as f:
            f.write(entry + "\n")

def init_logging(recovery_handler=None):
    """Initialisiert das Logging-System beim App-Start.
    
    Args:
        recovery_handler: Optional callable for recovery decision.
                          Signature: () -> bool (True = attempt recovery).
                          Defaults to interactive input() prompt.
    """
    if recovery_handler is None:
        recovery_handler = lambda: input(
            "Vorhandenes current.log gefunden. Wiederherstellung versuchen? (j/n): "
        ).lower() == 'j'
    
    if os.path.exists('current.log'):
        if recovery_handler():
            # Wiederherstellungslogik würde hier aufgerufen
            log_event("System", "Recovery from existing log")
            return True
        else:
            # Archiviere alte Logdatei
            archive_name = f"current_{datetime.now().strftime('%Y%m%d_%H%M')}.log"
            os.rename('current.log', archive_name)
            create_new_log()
            log_event("System", f"New log started. Old log archived as {archive_name}")
    else:
        create_new_log()
    
    # Prüfe auf Excel-Dateien
    check_excel_files()
    
    return True

def create_new_log():
    """Erstellt eine neue Logdatei mit Initialisierungseintrag"""
    with open('current.log', 'w') as f:
        f.write(f"Log created at {datetime.now()}\n")
        f.flush()  # Ensure write is flushed before log_event opens the file
    log_event("System", "Application started")

def check_excel_files():
    """Überprüft Excel-Dateien im aktuellen Verzeichnis"""
    excel_files = glob.glob('*.xls*')
    
    if len(excel_files) == 1:
        if validate_excel(excel_files[0]):
            load_excel(excel_files[0])
        else:
            log_event("System", "Invalid Excel file found", "WARNING", {"file": excel_files[0]})
    elif len(excel_files) > 1:
        log_event("System", "Multiple Excel files found - user selection required", "INFO")
    else:
        log_event("System", "No Excel files found", "WARNING")

def validate_excel(file_path):
    """Validierte eine Excel-Datei (Platzhalter)"""
    # Hier würde die tatsächliche Validierungslogik stehen
    return True

def load_excel(file_path):
    """Lädt eine Excel-Datei (Platzhalter)"""
    log_event("System", f"Loading Excel file: {file_path}")