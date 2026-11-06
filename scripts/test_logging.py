import pytest
from python.logger.logging_util import log_event, init_logging
import os
import glob

def test_log_creation(tmp_path):
    """Testet die Erstellung von Logdateien"""
    os.chdir(tmp_path)
    init_logging()
    
    assert os.path.exists('current.log')
    assert "Application started" in open('current.log').read()

def test_error_logging(tmp_path):
    """Testet die Fehlerprotokollierung"""
    os.chdir(tmp_path)
    log_event("Test", "Critical error", "CRITICAL")
    
    assert os.path.exists('error.log')
    assert "CRITICAL" in open('error.log').read()

def test_log_rotation(tmp_path):
    """Testet die Log-Rotation bei Neustart"""
    os.chdir(tmp_path)
    
    # Ersten Start simulieren
    init_logging()
    assert os.path.exists('current.log')
    
    # Zweiten Start mit vorhandenem Log (kein Recovery)
    open('test.xlsx', 'w').close()  # Test-Excel erstellen
    init_logging(recovery_handler=lambda: False)
    
    archived_logs = glob.glob('current_*.log')
    assert len(archived_logs) == 1
    assert "Old log archived" in open('current.log').read()

def test_excel_validation(tmp_path):
    """Testet Excel-Datei-Erkennung"""
    os.chdir(tmp_path)
    open('valid.xlsx', 'w').close()
    
    init_logging()
    assert "Loading Excel file" in open('current.log').read()