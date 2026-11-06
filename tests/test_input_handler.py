"""Tests für HotkeyMapping + InputHandler (ohne echte Tastatur)."""

from __future__ import annotations

import queue
from datetime import datetime

from python.core.input_handler import HotkeyMapping, InputHandler
from python.logger.blackbox import BlackboxWriter


class FakeKeyEvent:
    """Minimaler Ersatz für keyboard.KeyboardEvent (Test-Fake)."""

    def __init__(self, name: str, event_type: str = "down") -> None:
        self.name = name
        self.event_type = event_type


def _make_handler(tmp_path):
    """Hilfsfunktion: Blackbox + Queue + InputHandler bauen."""
    box = BlackboxWriter(tmp_path / "blackbox.log")
    q: queue.Queue = queue.Queue()
    mapping = HotkeyMapping.from_starters(["A", "B", "C", "D", "E",
                                           "F", "G", "H", "I", "J", "K"])
    handler = InputHandler(q, mapping, box)
    return box, q, handler


def test_mapping_from_starters_letters() -> None:
    """from_starters mappt jeden Boot-Key auf die gleichnamige Taste."""
    mapping = HotkeyMapping.from_starters(["A", "B", "C"])
    assert mapping.letters == {"A": "a", "B": "b", "C": "c"}


def test_mapping_numpad_alias_first_ten() -> None:
    """Der Zahlenblock 1–0 ist Alias für die ersten zehn Boot-Keys."""
    mapping = HotkeyMapping.from_starters(
        ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"])
    # Sortiert: A–J bekommen 1..9,0
    assert mapping.numpad_alias["1"] == "A"
    assert mapping.numpad_alias["2"] == "B"
    assert mapping.numpad_alias["9"] == "I"
    assert mapping.numpad_alias["0"] == "J"
    # K (11. Boot) bekommt KEINEN Zahlenblock-Alias
    assert "K" not in mapping.numpad_alias.values()
    assert "K" not in {v for k, v in mapping.numpad_alias.items()}
    # 10 Aliase + 10 mit "num "-Präfix
    assert len(mapping.numpad_alias) == 20


def test_mapping_key_to_boot_letter() -> None:
    """key_to_boot übersetzt Buchstaben-Tasten (Groß/Klein egal)."""
    mapping = HotkeyMapping.from_starters(["A", "B"])
    assert mapping.key_to_boot("a") == "A"
    assert mapping.key_to_boot("B") == "B"


def test_mapping_key_to_boot_numpad() -> None:
    """key_to_boot übersetzt Zahlenblock-Aliase (mit/ohne 'num '-Präfix)."""
    mapping = HotkeyMapping.from_starters(["A", "B"])
    assert mapping.key_to_boot("1") == "A"
    assert mapping.key_to_boot("num 1") == "A"


def test_mapping_key_to_boot_unknown() -> None:
    """Unbekannte Tasten liefern None."""
    mapping = HotkeyMapping.from_starters(["A"])
    assert mapping.key_to_boot("x") is None
    assert mapping.key_to_boot("") is None


def test_on_event_writes_blackbox_and_queue(tmp_path) -> None:
    """Ein Tastendruck → Rohdruck in die Blackbox + Boot-Key auf die Queue."""
    box, q, handler = _make_handler(tmp_path)
    handler._on_event(FakeKeyEvent("a"))
    handler._on_event(FakeKeyEvent("num 2"))
    handler._on_event(FakeKeyEvent("a"))   # zweiter Druck von Boot A

    assert q.get_nowait() == "A"
    assert q.get_nowait() == "B"
    assert q.get_nowait() == "A"
    assert q.empty()

    entries = box.replay()
    assert len(entries) == 3
    # Rohdruck-Format: [ts] TASTE: '<taste>' (ohne EVENT/STATUS)
    assert entries[0].endswith("TASTE: 'a'")
    assert entries[1].endswith("TASTE: 'num 2'")
    assert "EVENT" not in entries[0] and "STATUS" not in entries[0]


def test_on_event_ignores_key_up(tmp_path) -> None:
    """Nur Key-Down-Events werden verarbeitet (kein Doppel-Logging)."""
    box, q, handler = _make_handler(tmp_path)
    handler._on_event(FakeKeyEvent("a", event_type="up"))
    assert q.empty()
    assert box.replay() == []


def test_on_event_ignores_unknown_key(tmp_path) -> None:
    """Tasten ohne Boot-Zuordnung werden ignoriert (auch 'x', F-Tasten)."""
    box, q, handler = _make_handler(tmp_path)
    handler._on_event(FakeKeyEvent("f1"))
    handler._on_event(FakeKeyEvent("shift"))
    assert q.empty()
    assert box.replay() == []


def test_stop_without_start_is_safe(tmp_path) -> None:
    """stop() ohne vorheriges start() wirft keinen Fehler."""
    _, _, handler = _make_handler(tmp_path)
    handler.stop()
    handler.stop()   # doppelt ist auch ok
