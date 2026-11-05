"""Build the release archive of the Home Assistant component.

The archive holds the contents of ``custom_components/hisense_vidaa`` at its root, which is
the layout expected by the Home Assistant store when a release asset is published.

Usage:
    python tools/build_release.py [OUTPUT_ZIP]
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "hisense_vidaa"


def build(output: Path) -> int:
    count = 0
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(COMPONENT.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, path.relative_to(COMPONENT).as_posix())
                count += 1
    return count


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "hisense_vidaa.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"{build(target)} files -> {target}")
