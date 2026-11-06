"""Bump-Versionsskript: synchronisiert die Version an den zentralen Stellen.

Verwendung:
    python scripts/bump_version.py 0.2.0

Wirkung (Single Source of Truth = python/config/version.py, AGENTS.md §7):
    1. Schreibt `VERSION = "X.Y.Z"` in python/config/version.py
       (BUILD_DATE/APP_NAME/APP_TITLE bleiben unberührt)
    2. Schreibt die Root-Datei `VERSION` mit derselben Version

Ohne Argument wird nur die aktuelle Version angezeigt (--check).

Beispiel-Ablauf eines Releases (AGENTS.md §5):
    python scripts/bump_version.py 0.2.0
    → danach ACTIVE_CHANGES → RELEASE_LOG verschieben, ACTIVE_CHANGES leeren
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_PY = PROJECT_ROOT / "python" / "config" / "version.py"
ROOT_VERSION_FILE = PROJECT_ROOT / "VERSION"

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_VERSION_LINE = re.compile(r'^(VERSION\s*=\s*)"[^"]*"(\s*)$', re.MULTILINE)
_CURRENT = re.compile(r'^VERSION\s*=\s*"([^"]+)"', re.MULTILINE)


def read_current_version() -> str:
    """Liest die aktuelle Version aus version.py (Source of Truth).

    Returns:
        Aktuelle Versionsnummer als String, z. B. "0.1.0".
    """
    match = _CURRENT.search(VERSION_PY.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError(
            f"VERSION-Zeile nicht gefunden in {VERSION_PY}")
    return match.group(1)


def write_version(new_version: str) -> None:
    """Schreibt die neue Version nach version.py und in die Root-VERSION-Datei.

    Args:
        new_version: Versionsnummer im Format X.Y.Z (wird validiert).

    Raises:
        ValueError: wenn das Format nicht X.Y.Z entspricht.
    """
    if not _SEMVER.match(new_version):
        raise ValueError(
            f"Ungültige Versionsnummer '{new_version}' – erwartet X.Y.Z "
            "(z. B. 0.2.0)")

    text = VERSION_PY.read_text(encoding="utf-8")
    new_text, count = _VERSION_LINE.subn(
        rf'\g<1>"{new_version}"\g<2>', text, count=1)
    if count != 1:
        raise RuntimeError(f"VERSION-Zeile nicht ersetzbar in {VERSION_PY}")
    VERSION_PY.write_text(new_text, encoding="utf-8")

    ROOT_VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI-Einstieg: Version anzeigen (--check) oder neu setzen."""
    parser = argparse.ArgumentParser(
        description="Zeigt oder setzt die Projektversion zentral "
                    "(python/config/version.py + Root-VERSION).")
    parser.add_argument("new_version", nargs="?", default=None,
                        help="Neue Version X.Y.Z (ohne Argument: nur Anzeige)")
    parser.add_argument("--check", action="store_true",
                        help="Nur aktuelle Version anzeigen")
    args = parser.parse_args(argv)

    current = read_current_version()
    print(f"Aktuelle Version: {current}")

    if args.check or args.new_version is None:
        return 0

    write_version(args.new_version)
    print(f"Neue Version:      {args.new_version}")
    print(f"  aktualisiert: {VERSION_PY.relative_to(PROJECT_ROOT)}")
    print(f"  aktualisiert: {ROOT_VERSION_FILE.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
