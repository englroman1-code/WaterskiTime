"""Application configuration for the Waterski Racing Timing System.

Dieses Modul enthält:
    1. Statische Konstanten (Farben, Pfade, Fenstergröße) – AppConfig
    2. Persistente App-Parameter (JSON-Datei) – AppSettings + ConfigManager

Entscheidung Q1 (2026-08-13): App-Parameter werden als JSON gespeichert
(`app_settings.json`), NICHT als .env (ist für Secrets gedacht) und nicht
als XML (überdimensioniert für diesen Zweck). JSON ist lesbar, editierbar
und benötigt kein zusätzliches Paket.

Für die spätere .exe-Auslieferung wird die JSON per PyInstaller
(`--add-data`) neben die .exe gelegt.
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Statische Konstanten (niemals in JSON – Code-Konstanten)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AppConfig:
    """Statische Anwendungskonstanten (Farbschema, Pfade, Fenster).

    Diese Werte sind Teil des Programmcodes und werden nicht über die
    JSON-Datei konfiguriert. Das Farbdesign folgt der GUI-Description
    (05_a_GUI_Description.txt): dunkles High-Contrast-Theme.
    """
    # --- Fenster ----------------------------------------------------------
    WINDOW_TITLE: str = "Wasserski-Racing Timing System"
    WINDOW_WIDTH: int = 1440
    WINDOW_HEIGHT: int = 900

    # --- Branding (Kontaktdaten – zentral, Header + Footer) ----------------
    BRANDING_NAME: str = "EDV Engl Roman"
    BRANDING_URL: str = "www.engl.biz"
    BRANDING_EMAIL: str = "edv@engl.biz"

    # --- Farben (Dark Theme, Quelle: 08_gui_implementation_guide.md) --------
    COLOR_BG: str = "#121212"            # Hauptfensterhintergrund
    COLOR_PANEL: str = "#1E1E1E"         # Container-Panels
    COLOR_TEXT: str = "#FFFFFF"          # primäre Schriftfarbe
    COLOR_TEXT_SECONDARY: str = "#B0BEC5"  # sekundäre Schrift (Labels)
    COLOR_ACTIVE: str = "#00C853"        # Grün = aktiv / Führender / Neustart
    COLOR_WARNING: str = "#FFD600"       # Gelb = Status "wartend"
    COLOR_ERROR: str = "#FF1744"         # Rot = Rennstart / Warnung / Sperrzeit
    COLOR_PROGRESS: str = "#2979FF"      # Blau = Fortschrittsbalken (VORSTART)
    COLOR_ACCENT: str = "#1565C0"        # Blau = Buttons (Refresh, Aktionen)   
    COLOR_ACCENT_HOVER: str = "#1976D2"  # Blau heller = Hover-Effekt           
    COLOR_DISABLED: str = "#555555"      # Grau = deaktivierter Button (Start gesperrt)

    # --- Defaults ---------------------------------------------------------
    DEFAULT_LOCKOUT_SECONDS: float = 2.0   # Standard-Sperrzeit (überschreibbar in JSON)
    POLL_INTERVAL_MS: int = 50             # GUI-Poll-Intervall für die Event-Queue (ADR-007)


# ---------------------------------------------------------------------------
# Persistente App-Parameter (JSON)
# ---------------------------------------------------------------------------

@dataclass
class AppSettings:
    """Persistente, vom Bediener änderbare App-Parameter.

    Werte werden aus `app_settings.json` geladen; fehlende Felder fallen
    auf die Dataclass-Defaults zurück (abwärtskompatibel beim Hinzufügen
    neuer Parameter).
    """
    lockout_seconds: float = AppConfig.DEFAULT_LOCKOUT_SECONDS  # Sperrzeit je Boot (Q1)
    enable_keyboard: bool = False  # systemweite Hotkeys (keyboard-Library, Admin nötig, AGENTS.md §10)
    # Weitere Parameter später z. B.: event_log_path, window_size, theme_override ...
    # Hinweis: startreihe_offset_s wurde entfernt (2026-09-02) – die Zeit zwischen
    # den Startreihen kommt jetzt als Grid Time aus der Excel/IMPORT.json.


def get_runtime_dir() -> Path:
    """Ermittelt den Ordner für schreibbare Laufzeitdateien.

    Gebaute .exe (PyInstaller): Ordner der .exe – dort liegen Blackbox,
    Crash-Recovery-State, Exporte und das Start-Log. Entwicklung:
    Projekt-Root (unabhängig vom aktuellen Arbeitsverzeichnis).

    Returns:
        Der Laufzeitordner.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resolve_settings_path() -> Path:
    """Ermittelt den Pfad der app_settings.json zur Laufzeit.

    Entwicklung (nicht eingefroren): die JSON liegt im Modul-Ordner
    (python/config/app_settings.json) – wie bisher.

    Gebaute .exe (PyInstaller, `sys.frozen`): die JSON wird mit
    `--add-data "python/config/app_settings.json;config"` ins Bundle
    gelegt, wäre dort aber nicht editierbar (nur Lesen). Deshalb:
        1. Liegt bereits eine JSON NEBEN der .exe → diese verwenden
           (der Bediener kann Sperrzeit/Hotkeys anpassen).
        2. Sonst: die Bundle-Kopie aus sys._MEIPASS/config/ einmalig
           neben die .exe kopieren (schreibbar) und diese verwenden.

    Returns:
        Der aufgelöste Zielpfad der Konfigurationsdatei.
    """
    if not getattr(sys, "frozen", False):
        return Path(__file__).parent / "app_settings.json"

    exe_dir = Path(sys.executable).resolve().parent
    candidate = exe_dir / "app_settings.json"
    if candidate.exists():
        return candidate

    bundle_path = Path(getattr(sys, "_MEIPASS", exe_dir)) / "config" / "app_settings.json"
    if bundle_path.exists():
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundle_path, candidate)
            logger.info("app_settings.json nach {} kopiert (erster Start)",
                        candidate)
        except OSError as exc:
            logger.warning("app_settings.json konnte nicht kopiert werden "
                           f"({exc}) – verwende Bundle-Kopie schreibgeschützt")
            return bundle_path
    return candidate


class ConfigManager:
    """Lädt und speichert die AppSettings aus einer JSON-Datei.

    Verhalten:
        - Fehlt die Datei          → Defaults werden verwendet (und optional angelegt)
        - Unbekannte/fehlende Keys → Defaults, Rest wird übernommen
        - Ungültiges JSON          → Warnung + Defaults (App bleibt startbar!)
    """

    def __init__(self, path: str | Path | None = None) -> None:
        """ConfigManager initialisieren.

        Args:
            path: Pfad zur JSON-Datei. Wenn None, wird der Pfad über
                  `resolve_settings_path()` bestimmt (Entwicklung:
                  python/config/, gebaute .exe: neben der .exe).
        """
        self.path = resolve_settings_path() if path is None else Path(path)

    def load(self) -> AppSettings:
        """AppSettings laden (fehlende Felder → Defaults).

        Returns:
            AppSettings mit den gespeicherten (bzw. Standard-) Werten.
        """
        settings = AppSettings()
        if not self.path.exists():
            return settings

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            # App darf auch bei kaputter Config starten – Warnung reicht
            logger.warning(
                f"Konfiguration nicht lesbar ({exc}), verwende Standardwerte."
            )
            return settings

        # Nur bekannte Felder übernehmen (unbekannte Keys ignorieren)
        if isinstance(raw, dict):
            for field_name, field_value in asdict(settings).items():
                if field_name in raw:
                    setattr(settings, field_name, type(field_value)(raw[field_name]))
        return settings

    def save(self, settings: AppSettings) -> None:
        """AppSettings in die JSON-Datei schreiben.

        Args:
            settings: Die zu speichernden Einstellungen.
        """
        self.path.write_text(
            json.dumps(asdict(settings), indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_settings(self) -> AppSettings:
        """Komfort-Alias für load() (klarerer Aufrufname)."""
        return self.load()


# Modulweite Instanz, damit alle Komponenten dieselbe Konfiguration nutzen.
# (Einzige globale Variable im Projekt – bewusst: eine App = eine Config.)
_config_manager: Optional[ConfigManager] = None
_settings_cache: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Liefert die einmalig geladenen AppSettings (Caching).

    Returns:
        Die aktuellen App-Parameter.
    """
    global _settings_cache, _config_manager
    if _settings_cache is None:
        if _config_manager is None:
            _config_manager = ConfigManager()
        _settings_cache = _config_manager.load()
    return _settings_cache
