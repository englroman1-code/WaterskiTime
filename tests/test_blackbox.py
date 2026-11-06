"""Tests für den BlackboxWriter (Beweisfunktion, append-only TXT)."""

from __future__ import annotations

import threading
from datetime import datetime

from python.logger.blackbox import BlackboxWriter, format_timestamp


def test_new_file_created(tmp_path) -> None:
    """Beim Anlegen entsteht die Blackbox-Datei."""
    path = tmp_path / "blackbox.log"
    box = BlackboxWriter(path)
    box.close()
    assert path.exists()


def test_write_appends_line_with_newline(tmp_path) -> None:
    """write() hängt eine Zeile mit Zeilenumbruch an."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    box.write("ERSTER EINTRAG")
    box.write("ZWEITER EINTRAG")
    box.close()
    lines = (tmp_path / "blackbox.log").read_text(encoding="utf-8").splitlines()
    assert lines == ["ERSTER EINTRAG", "ZWEITER EINTRAG"]


def test_existing_file_not_truncated(tmp_path) -> None:
    """Eine vorhandene Blackbox wird beim Öffnen NICHT geleert (append-only)."""
    path = tmp_path / "blackbox.log"
    path.write_text("ALTER EINTRAG\n", encoding="utf-8")
    box = BlackboxWriter(path)
    box.write("NEUER EINTRAG")
    box.close()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == ["ALTER EINTRAG", "NEUER EINTRAG"]


def test_flush_writes_immediately(tmp_path) -> None:
    """Nach write() liegt der Eintrag sofort auf der Platte (ohne close)."""
    path = tmp_path / "blackbox.log"
    box = BlackboxWriter(path)
    box.write("SOFORT SICHTBAR")
    assert "SOFORT SICHTBAR" in path.read_text(encoding="utf-8")
    box.close()


def test_write_key_event_full_format(tmp_path) -> None:
    """write_key_event baut das exakte Zeilenformat (Objektplan §7.3)."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    ts = datetime(2026, 8, 14, 8, 0, 0, 123000)
    box.write_key_event(ts, key="A", event_type="PASSAGE", status="VALID")
    box.close()
    lines = (tmp_path / "blackbox.log").read_text(encoding="utf-8").splitlines()
    assert lines == [
        "[2026-08-14 08:00:00,123] TASTE: 'A' EVENT: PASSAGE STATUS: VALID"]


def test_write_key_event_system_event(tmp_path) -> None:
    """Systemereignisse haben keinen TASTE-Teil."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    ts = datetime(2026, 8, 14, 8, 0, 1, 456000)
    box.write_key_event(ts, key=None, event_type="START", status="VALID")
    box.close()
    lines = (tmp_path / "blackbox.log").read_text(encoding="utf-8").splitlines()
    assert lines == ["[2026-08-14 08:00:01,456] EVENT: START STATUS: VALID"]


def test_write_key_event_raw_press(tmp_path) -> None:
    """Der Rohdruck (Keyboard-Thread) hat nur den TASTE-Teil."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    ts = datetime(2026, 8, 14, 8, 0, 2, 789000)
    box.write_key_event(ts, key="a", event_type=None, status=None)
    box.close()
    lines = (tmp_path / "blackbox.log").read_text(encoding="utf-8").splitlines()
    assert lines == ["[2026-08-14 08:00:02,789] TASTE: 'a'"]


def test_replay_returns_all_lines(tmp_path) -> None:
    """replay() liefert alle Einträge in chronologischer Reihenfolge."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    box.write("EINS")
    box.write("ZWEI")
    box.write("DREI")
    assert box.replay() == ["EINS", "ZWEI", "DREI"]
    box.close()


def test_rotation_renames_full_file(tmp_path) -> None:
    """Bei Überschreiten der Grenze wird die volle Datei umbenannt."""
    path = tmp_path / "blackbox.log"
    box = BlackboxWriter(path, max_bytes=40)
    box.write("EIN SEHR LANGER EINTRAG DER ROTIERT WIRD")
    box.write("KURZ")
    box.close()

    # Alte Datei wurde mit Zeitstempel-Suffix archiviert
    archived = list(tmp_path.glob("blackbox_*.log"))
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8").count("ROTIERT") == 1
    # Neue Datei enthält nur den Eintrag nach der Rotation
    assert path.read_text(encoding="utf-8").splitlines() == ["KURZ"]


def test_rotation_at_open_when_already_full(tmp_path) -> None:
    """Beim Öffnen wird rotiert, wenn die vorhandene Datei bereits voll ist."""
    path = tmp_path / "blackbox.log"
    path.write_text("A" * 500, encoding="utf-8")
    box = BlackboxWriter(path, max_bytes=100)
    box.write("NEU")
    box.close()
    assert path.read_text(encoding="utf-8").splitlines() == ["NEU"]
    assert len(list(tmp_path.glob("blackbox_*.log"))) == 1


def test_thread_safety_parallel_writes(tmp_path) -> None:
    """Paralleles Schreiben aus mehreren Threads verliert keine Einträge."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    errors: list[Exception] = []

    def worker(thread_id: int) -> None:
        try:
            for i in range(10):
                box.write(f"T{thread_id}-{i}")
        except Exception as exc:  # pragma: no cover - Fehler im Test sammeln
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,))
               for t in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    entries = box.replay()
    assert len(entries) == 200
    assert len(set(entries)) == 200        # kein Eintrag doppelt/verloren
    box.close()


def test_format_timestamp_milliseconds() -> None:
    """format_timestamp kürzt Mikro- auf Millisekunden."""
    ts = datetime(2026, 8, 14, 14, 35, 2, 987654)
    assert format_timestamp(ts) == "2026-08-14 14:35:02,987"


def test_write_calls_fsync(tmp_path, monkeypatch) -> None:
    """write() ruft fsync auf (Beweisfunktion auch bei Stromausfall)."""
    calls: list[int] = []
    monkeypatch.setattr(
        "python.logger.blackbox.os.fsync", lambda fd: calls.append(fd))
    box = BlackboxWriter(tmp_path / "blackbox.log")
    box.write("FSYNC-TEST")
    box.close()
    assert calls
