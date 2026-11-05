"""Fail when the version differs between the library, the component and the changelog."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def library_version() -> str:
    text = (ROOT / "src" / "vidaa_tv" / "__version__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__ = "([^"]+)"', text)
    if match is None:
        raise SystemExit("cannot read the library version")
    return match.group(1)


def manifest_version() -> str:
    path = ROOT / "custom_components" / "hisense_vidaa" / "manifest.json"
    return str(json.loads(path.read_text(encoding="utf-8"))["version"])


def changelog_version() -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^## \[(?!Unreleased)([^\]]+)\]", text, re.MULTILINE)
    if match is None:
        raise SystemExit("the changelog has no released section")
    return match.group(1)


def main() -> int:
    versions = {
        "library (src/vidaa_tv/__version__.py)": library_version(),
        "component (manifest.json)": manifest_version(),
        "changelog (newest section)": changelog_version(),
    }
    for name, value in versions.items():
        print(f"{name}: {value}")
    if len(set(versions.values())) != 1:
        print("version mismatch", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
