"""Findet das Hauptfenster der App per Win32-API und gibt seine Bildschirm-
Koordinaten als JSON aus.

Verwendung (für deterministische GUI-Screenshots):
    python scripts/capture_window.py
    → {"handle": ..., "x": ..., "y": ..., "w": ..., "h": ...}
    (leeres JSON {}, wenn das Fenster nicht gefunden wurde)

Damit kann ein externes Skript (PowerShell CopyFromScreen) exakt den
Fensterbereich erfassen – unabhängig von Monitorposition oder Fokus.
"""

from __future__ import annotations

import ctypes
import json
import sys
from ctypes import wintypes

# Fenstertitel-Präfix, um das App-Fenster eindeutig zu identifizieren
WINDOW_TITLE_PREFIX = "Wasserski-Racing"

RECT = wintypes.RECT
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def find_window(title_prefix: str) -> dict:
    """Sucht das erste Top-Level-Fenster, dessen Titel mit dem Präfix beginnt.

    Args:
        title_prefix: Titel-Präfix (z. B. "Wasserski-Racing").

    Returns:
        Dict mit Fenster-Handle und Koordinaten (leer, wenn nicht gefunden).
    """
    user32 = ctypes.windll.user32
    result: dict = {}

    def callback(hwnd: int, _lparam: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if buffer.value.startswith(title_prefix):
            rect = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            result.update({
                "handle": int(hwnd),
                "x": int(rect.left),
                "y": int(rect.top),
                "w": int(rect.right - rect.left),
                "h": int(rect.bottom - rect.top),
            })
            return False  # gefunden → Suche beenden
        return True       # weiter suchen

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return result


def activate_window(hwnd: int) -> None:
    """Bringt ein Fenster in den Vordergrund (für zuverlässige Screenshots).

    Args:
        hwnd: Fenster-Handle (aus find_window).
    """
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, 9)            # SW_RESTORE (falls minimiert)
    user32.SetForegroundWindow(hwnd)      # in den Vordergrund holen
    user32.BringWindowToTop(hwnd)         # Z-Order anheben


if __name__ == "__main__":
    args = sys.argv[1:]
    prefix = args[0] if args else WINDOW_TITLE_PREFIX
    window = find_window(prefix)
    if window and "--activate" in args:
        activate_window(window["handle"])
    print(json.dumps(window))
