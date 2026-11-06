"""InputHandler – systemweite Hotkey-Erfassung (keyboard-Library).

Eingabe & Threading (Objektplan Kapitel 6, ADR-007/ADR-008):

    HotkeyMapping – Tastenzuordnung: Boot-Key (A–Z) → physikalische Taste
                    (+ Zahlenblock-Alias "1".."0" als Bediener-Option)
    InputHandler  – lauscht auf systemweite Tastendrücke und
                    1. schreibt den Rohdruck SOFORT in die Blackbox
                       (Beweisfunktion – passiert im Keyboard-Thread der
                       keyboard-Library)
                    2. legt den Boot-Key auf die input_queue für den
                       GUI-Thread (AppController pollt per after(), ADR-007)

Hinweis (AGENTS.md §10): Die keyboard-Library benötigt auf Windows
Administrator-Rechte für die systemweite Erfassung. Das Registrieren der
Hooks passiert nur in start() – die Verarbeitungslogik (_on_event) ist
ohne echte Hardware testbar.
"""

from __future__ import annotations

import queue
from dataclasses import dataclass, field
from datetime import datetime

from python.logger.blackbox import BlackboxWriter


@dataclass
class HotkeyMapping:
    """Tastenzuordnung zwischen Boot-Keys und physikalischen Tasten.

    Attributes:
        letters: Boot-Key (A–Z, groß) → Tastennamen (klein, "a".."z").
        numpad_alias: Tastennamen ("1".."0", ggf. mit "num "-Präfix)
            → Boot-Key (Bediener-Option, Objektplan §6.2).
    """

    letters: dict[str, str] = field(default_factory=dict)
    numpad_alias: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_starters(cls, boot_keys: list[str]) -> "HotkeyMapping":
        """Baut das Mapping aus der Starterliste (ADR-008).

        Jeder Boot-Key (A–Z) wird auf die gleichnamige Taste gemappt;
        der Zahlenblock 1–0 wird als Alias für die ersten zehn Boot-Keys
        vergeben (Bediener-Option).

        Args:
            boot_keys: Boot-Keys der Starter (z. B. ["A", "B", ...]).

        Returns:
            Fertig befülltes HotkeyMapping.
        """
        mapping = cls()
        for key in boot_keys:
            key = key.upper()
            if len(key) == 1 and key.isalpha():
                mapping.letters[key] = key.lower()
        # Zahlenblock-Alias: "1".."0" für die ersten 10 Boot-Keys (sortiert)
        ordered = sorted(mapping.letters)
        for index, boot_key in enumerate(ordered[:10]):
            alias = str((index + 1) % 10)          # 1..9, 0 für den 10.
            mapping.numpad_alias[alias] = boot_key
            mapping.numpad_alias[f"num {alias}"] = boot_key
        return mapping

    def key_to_boot(self, key_name: str) -> str | None:
        """Übersetzt einen Tastennamen in den zugehörigen Boot-Key.

        Args:
            key_name: Tastennamen aus der keyboard-Library (z. B. "a", "1").

        Returns:
            Boot-Key (groß) oder None, wenn die Taste keinem Boot zugeordnet ist.
        """
        name = key_name.strip().lower()
        for boot_key, letter in self.letters.items():
            if letter == name:
                return boot_key
        return self.numpad_alias.get(name)


class InputHandler:
    """Systemweite Hotkey-Erfassung mit Sofort-Blackbox (Beweisfunktion)."""

    def __init__(self, input_queue: queue.Queue,
                 key_map: HotkeyMapping,
                 blackbox: BlackboxWriter) -> None:
        """InputHandler initialisieren.

        Args:
            input_queue: Queue für den GUI-Thread (Boot-Keys werden
                         hineingelegt – AppController pollt per after()).
            key_map: Tastenzuordnung (HotkeyMapping).
            blackbox: BlackboxWriter für den sofortigen Rohdruck.
        """
        self._queue = input_queue
        self._key_map = key_map
        self._blackbox = blackbox
        self._hook = None

    # ------------------------------------------------------------------
    # Lebenszyklus
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Registriert den systemweiten Tastatur-Hook (keyboard.on_press).

        Raises:
            RuntimeError: wenn die Registrierung fehlschlägt (z. B. fehlende
                          Administrator-Rechte auf Windows, AGENTS.md §10).
        """
        if self._hook is not None:
            return
        try:
            import keyboard
        except ImportError as exc:  # pragma: no cover - abhängig vom System
            raise RuntimeError("keyboard-Library nicht installiert") from exc
        self._hook = keyboard.on_press(self._on_event)

    def stop(self) -> None:
        """Entfernt den Tastatur-Hook wieder (kein Weiterempfangen)."""
        if self._hook is None:
            return
        try:
            import keyboard
            keyboard.unhook(self._hook)
        except Exception:  # pragma: no cover - abhängig vom System
            pass
        self._hook = None

    def update_mapping(self, key_map: HotkeyMapping) -> None:
        """Ersetzt die Tastenzuordnung (z. B. nach einem Rennen-Wechsel).

        Der Keyboard-Thread liest das Mapping bei jedem Druck neu – der
        Attribut-Tausch ist atomar und damit thread-sicher.

        Args:
            key_map: neues HotkeyMapping (aktive Starter des Rennens).
        """
        self._key_map = key_map

    # ------------------------------------------------------------------
    # Ereignisverarbeitung (ohne echte Hardware testbar)
    # ------------------------------------------------------------------

    def _on_event(self, event) -> None:
        """Verarbeitet einen Tastendruck (Callback der keyboard-Library).

        Reihenfolge (Objektplan §9):
            1. Nur Key-Down-Events; nur bekannte Boot-Tasten
            2. Rohdruck SOFORT in die Blackbox (Beweisfunktion, im
               Keyboard-Thread, bevor die Verarbeitung läuft)
            3. Boot-Key auf die input_queue legen (GUI-Thread verarbeitet)

        Args:
            event: Objekt mit den Attributen `name` (Tastennamen) und
                   `event_type` ("down"/"up") – aus der keyboard-Library
                   oder ein Test-Fake.
        """
        event_type = getattr(event, "event_type", "down")
        if event_type != "down":
            return
        boot_key = self._key_map.key_to_boot(event.name)
        if boot_key is None:
            return
        # 1. Rohdruck sofort protokollieren (Taste, kein Boot-Key –
        #    damit z. B. '1' vom Zahlenblock eindeutig als Taste belegt ist)
        self._blackbox.write_key_event(
            datetime.now(), key=event.name.strip().lower(), event_type=None,
            status=None)
        # 2. Boot-Key an den GUI-Thread weiterreichen
        self._queue.put(boot_key)


__all__ = ["HotkeyMapping", "InputHandler"]
