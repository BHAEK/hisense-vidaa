import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "release_notes", Path(__file__).resolve().parents[2] / "tools" / "release_notes.py"
)
assert SPEC is not None and SPEC.loader is not None
release_notes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_notes)

CHANGELOG = """# Changelog

## [Unreleased]

## [0.2.0] - 2026-01-02

### Added

- Second.

## [0.1.0] - 2026-01-01

First.
"""


def test_extracts_one_section() -> None:
    assert release_notes.section(CHANGELOG, "0.2.0") == "### Added\n\n- Second."
    assert release_notes.section(CHANGELOG, "0.1.0") == "First."


def test_unknown_version_is_none() -> None:
    assert release_notes.section(CHANGELOG, "9.9.9") is None
