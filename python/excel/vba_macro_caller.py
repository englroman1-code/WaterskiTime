"""VbaMacroCaller – Ruft VBA-Makros in Excel-Dateien via COM auf.

Der primäre Anwendungsfall ist der Aufruf von
``ExportExpRangesToJSON``, der die _EXP_ Named Ranges aus der Excel
in eine IMPORT.json exportiert. Die Python-App liest dann IMPORT.json
statt die Excel direkt über openpyxl zu öffnen (ADR-009).

Voraussetzung:
    - Microsoft Excel muss installiert sein
    - Makros müssen ausgeführt werden dürfen (Trusted Location oder
      ``AutomationSecurity``). Ein „Vertrauenszugang zum VBA-Projekt-
      objektmodell“ ist NICHT nötig – der Caller liest das VBProject nicht.
    - Die Excel-Datei muss das Export-Makro enthalten. Die aktuelle Vorlage
      nutzt das Modul ``mdl_Engl_Export``; der hier verwendete Modulname
      ``mdlEngl`` ist noch nicht angepasst (offener Punkt 1, 2026-11-06).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from loguru import logger


class VbaMacroError(Exception):
    """Fehler beim Aufruf eines VBA-Makros."""
    pass


class VbaMacroCaller:
    """Ruft VBA-Makros in Excel-Dateien via COM automation auf.

    Der Caller öffnet Excel unsichtbar, führt das Makro aus und
    schließt Excel wieder. Die Excel-Datei muss nicht manuell
    geöffnet werden – der Caller übernimmt alles.
    """

    # Wartezeit (Sekunden) nach dem Makro-Aufruf, bis die JSON-Datei
    # garantiert geschrieben ist
    MACRO_SETTLE_TIME_S: float = 1.0

    # Maximal warten auf IMPORT.json nach Makro-Aufruf
    JSON_WAIT_TIMEOUT_S: float = 5.0

    def __init__(self, excel_path: str | Path) -> None:
        """Initialisierung.

        Args:
            excel_path: Pfad zur Excel-Datei (.xlsm/.xlsx) mit VBA-Makros.
        """
        self._excel_path = Path(excel_path)
        if not self._excel_path.exists():
            raise FileNotFoundError(
                f"Excel-Datei nicht gefunden: {self._excel_path}"
            )

    def export_json(self, json_path: str | Path | None = None) -> Path:
        """Ruft das VBA-Makro ``ExportExpRangesToJSON`` auf.

        Das Makro liest alle ``_EXP_`` Named Ranges aus der Excel
        und schreibt sie als IMPORT.json.

        Args:
            json_path: Optionaler Ziel-Pfad für die JSON-Datei.
                Wenn None, wird der Standard-Pfad des Makros verwendet
                (gleicher Ordner wie die Excel-Datei, Dateiname IMPORT.json).

        Returns:
            Pfad zur erzeugten IMPORT.json.

        Raises:
            VbaMacroError: Wenn der Makro-Aufruf fehlschlägt.
            FileNotFoundError: Wenn die Excel-Datei nicht gefunden wird.
        """
        target_json = Path(json_path) if json_path else None
        json_dir = target_json.parent if target_json else self._excel_path.parent
        expected_json = json_dir / "IMPORT.json"

        logger.info(
            "VBA-Makro: ExportExpRangesToJSON wird aufgerufen für {}",
            self._excel_path.name,
        )

        try:
            self._run_macro(
                macro_name="ExportExpRangesToJSON",
                json_path=str(target_json) if target_json else "",
            )
        except VbaMacroError:
            raise
        except Exception as exc:
            raise VbaMacroError(
                f"VBA-Makro konnte nicht ausgeführt werden: {exc}"
            ) from exc

        # Warten bis die JSON-Datei erscheint
        if not self._wait_for_json(expected_json):
            raise VbaMacroError(
                f"IMPORT.json wurde nicht erzeugt in: {json_dir}\n"
                f"VBA-Makro 'ExportExpRangesToJSON' hat keinen Fehler "
                f"zurückgegeben, aber die Datei fehlt."
            )

        logger.info("VBA-Makro: IMPORT.json erzeugt: {}", expected_json)
        return expected_json

    def _run_macro(
        self, macro_name: str, json_path: str = ""
    ) -> None:
        """Öffnet Excel via COM und ruft ein VBA-Makro auf.

        Args:
            macro_name: Name des VBA-Makros (in Modul mdlEngl).
            json_path: Optionaler Pfad-Parameter für das Makro.

        Raises:
            VbaMacroError: Bei COM-Fehlern oder Makro-Ausführungsfehlern.
        """
        excel = None
        wb = None

        try:
            # COM-Objekt erzeugen
            import win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.EnableEvents = False

            # Excel-Datei öffnen (mit Makros: xlOpenFormatXML = 52 für .xlsm)
            wb = excel.Workbooks.Open(
                str(self._excel_path.resolve()),
                ReadOnly=False,  # Makro muss schreiben können
            )

            # VBA-Makro aufrufen
            # Aufruf: Application.Run("mdlEngl.ExportExpRangesToJSON", jsonPath)
            if json_path:
                result = excel.Run(
                    f"mdlEngl.{macro_name}", json_path
                )
            else:
                result = excel.Run(f"mdlEngl.{macro_name}")

            # Makro gibt Boolean zurück
            if result is False:
                raise VbaMacroError(
                    f"VBA-Makro '{macro_name}' gab False zurück.\n"
                    f"Möglicherweise sind die Named Ranges nicht vorhanden "
                    f"oder die Excel-Struktur ist ungültig."
                )

            # Kurz warten bis Excel alles fertig geschrieben hat
            time.sleep(self.MACRO_SETTLE_TIME_S)

        except VbaMacroError:
            raise
        except ImportError:
            raise VbaMacroError(
                "pywin32 nicht installiert. "
                "Bitte 'pip install pywin32' ausführen."
            )
        except Exception as exc:
            # COM-Fehler (z.B. Excel nicht installiert, Makro nicht gefunden)
            error_msg = str(exc)
            if "Run method" in error_msg or "Makro" in error_msg or "macro" in error_msg.lower():
                raise VbaMacroError(
                    f"VBA-Makro '{macro_name}' nicht gefunden in "
                    f"{self._excel_path.name}.\n"
                    f"Bitte sicherstellen, dass das VBA-Modul 'mdlEngl' "
                    f"mit der Funktion '{macro_name}' vorhanden ist.\n"
                    f"Detail: {exc}"
                ) from exc
            raise VbaMacroError(
                f"COM-Fehler beim Aufruf von '{macro_name}': {exc}"
            ) from exc
        finally:
            # Excel sicher schließen
            try:
                if wb is not None:
                    wb.Close(SaveChanges=False)
            except Exception:
                pass
            try:
                if excel is not None:
                    excel.Quit()
            except Exception:
                pass
            # COM-Objekte freigeben
            try:
                import win32com.client
                if wb is not None:
                    win32com.client.gencache.EnsureDispatch("Excel.Application")
            except Exception:
                pass

    def _wait_for_json(self, json_path: Path) -> bool:
        """Wartet bis die JSON-Datei vorhanden und lesbar ist.

        Args:
            json_path: Erwarteter Pfad zur IMPORT.json.

        Returns:
            True wenn die Datei vorhanden ist, False bei Timeout.
        """
        deadline = time.time() + self.JSON_WAIT_TIMEOUT_S
        while time.time() < deadline:
            if json_path.exists():
                # Prüfen ob Datei vollständig geschrieben (nicht leer)
                try:
                    size = json_path.stat().st_size
                    if size > 0:
                        return True
                except OSError:
                    pass
            time.sleep(0.2)
        return False

    def check_macro_available(self) -> bool:
        """Prüft ob das VBA-Makro in der Excel-Datei vorhanden ist.

        Returns:
            True wenn das Makro aufrufbar ist, False sonst.
        """
        try:
            import win32com.client
        except ImportError:
            logger.warning("pywin32 nicht installiert – VBA-Check nicht möglich")
            return False

        excel = None
        wb = None

        try:
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False

            wb = excel.Workbooks.Open(
                str(self._excel_path.resolve()),
                ReadOnly=True,
            )

            # Versuchen das Makro aufzurufen (mit Dummy-Parameter)
            # Wenn es nicht existiert, wirft Excel einen Fehler
            try:
                excel.Run("mdlEngl.ExportExpRangesToJSON", "")
                return True
            except Exception:
                return False

        except Exception:
            return False
        finally:
            try:
                if wb is not None:
                    wb.Close(SaveChanges=False)
            except Exception:
                pass
            try:
                if excel is not None:
                    excel.Quit()
            except Exception:
                pass
