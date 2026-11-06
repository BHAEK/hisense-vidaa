"""Print the changelog section of one version (used to fill the GitHub release).

Usage:
    python tools/release_notes.py VERSION
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def section(text: str, version: str) -> str | None:
    """Return the body of the ``## [version]`` section, or ``None`` when it is absent."""
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    body = section(CHANGELOG.read_text(encoding="utf-8"), sys.argv[1])
    if body is None:
        print(f"no changelog section for {sys.argv[1]}", file=sys.stderr)
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
