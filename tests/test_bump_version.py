"""Tests für das Versions-Skript scripts/bump_version.py (AGENTS.md §7).

Geprüft wird mit isolierten Pfaden (tmp_path), damit version.py/VERSION
im Repo unverändert bleiben:
    - aktuelle Version lesen (--check / read_current_version)
    - Schreiben aktualisiert version.py UND Root-VERSION synchron
    - ungültige Formate (nicht X.Y.Z) werden abgelehnt
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_bump_version(project_root: Path):
    """Lädt scripts/bump_version.py mit gemocktem Projekt-Root."""
    spec = importlib.util.spec_from_file_location(
        "bump_version", PROJECT_ROOT / "scripts" / "bump_version.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    # Projektpfade auf tmp_path umbiegen (Repos bleiben unberührt)
    module.PROJECT_ROOT = project_root
    module.VERSION_PY = project_root / "python" / "config" / "version.py"
    module.ROOT_VERSION_FILE = project_root / "VERSION"
    return module


@pytest.fixture()
def bump_env(tmp_path):
    """Isolierte Umgebung: version.py mit bekanntem Stand, kein VERSION-File."""
    project_root = tmp_path
    version_py = project_root / "python" / "config" / "version.py"
    version_py.parent.mkdir(parents=True)
    version_py.write_text(
        '"""App-Version."""\n\nVERSION = "0.1.0"\nBUILD_DATE = "2026-08-12"\n',
        encoding="utf-8")
    return _load_bump_version(project_root)


def test_read_current_version(bump_env) -> None:
    """Aktuelle Version wird aus version.py gelesen."""
    assert bump_env.read_current_version() == "0.1.0"


def test_write_version_updates_both_files(bump_env) -> None:
    """Schreiben aktualisiert version.py UND Root-VERSION (synchron)."""
    bump_env.write_version("0.2.0")

    text = bump_env.VERSION_PY.read_text(encoding="utf-8")
    assert 'VERSION = "0.2.0"' in text
    assert 'BUILD_DATE = "2026-08-12"' in text          # bleibt unberührt
    assert bump_env.ROOT_VERSION_FILE.read_text(encoding="utf-8") == "0.2.0\n"


def test_write_version_rejects_invalid_format(bump_env) -> None:
    """Nur X.Y.Z ist erlaubt – sonst ValueError, nichts wird geschrieben."""
    for bad in ["0.2", "0.2.0.1", "v0.2.0", "0,2,0", "abc"]:
        with pytest.raises(ValueError):
            bump_env.write_version(bad)

    # Nichts wurde verändert
    assert 'VERSION = "0.1.0"' in bump_env.VERSION_PY.read_text(encoding="utf-8")
    assert not bump_env.ROOT_VERSION_FILE.exists()


def test_main_check_prints_current_version(bump_env, capsys) -> None:
    """`--check` zeigt die aktuelle Version und ändert nichts."""
    assert bump_env.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Aktuelle Version: 0.1.0" in out
    assert 'VERSION = "0.1.0"' in bump_env.VERSION_PY.read_text(encoding="utf-8")


def test_main_sets_version_and_reports(bump_env, capsys) -> None:
    """main() mit neuer Version aktualisiert beide Dateien und meldet sie."""
    assert bump_env.main(["0.2.0"]) == 0
    out = capsys.readouterr().out
    assert "Neue Version:      0.2.0" in out
    assert bump_env.ROOT_VERSION_FILE.read_text(encoding="utf-8") == "0.2.0\n"
