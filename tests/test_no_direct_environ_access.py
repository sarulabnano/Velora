"""Enforces that `os.environ` is read in exactly one place in the codebase.

architecture.md original §6: "Nunca se accederá directamente a
os.environ desde el resto del proyecto." This test makes that a checked
invariant instead of a convention that can silently rot.
"""

from __future__ import annotations

from pathlib import Path

_ALLOWED_FILE = "_sources.py"
_SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "velora"


def test_os_environ_is_only_read_in_the_designated_source_file() -> None:
    offending: list[str] = []

    for path in _SRC_ROOT.rglob("*.py"):
        if path.name == _ALLOWED_FILE:
            continue
        text = path.read_text(encoding="utf-8")
        if "os.environ." in text or "os.environ[" in text:
            offending.append(str(path.relative_to(_SRC_ROOT)))

    assert offending == [], (
        f"os.environ must only be accessed in configuration/{_ALLOWED_FILE}, "
        f"but it also appears in: {offending}"
    )
