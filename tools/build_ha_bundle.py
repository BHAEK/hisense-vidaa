"""Build a self-contained Home Assistant custom component for manual testing.

Home Assistant does not keep its config directory on ``sys.path``, so the library
cannot sit next to ``custom_components``. This script copies it *inside* the
component and rewrites imports accordingly. The bundle needs only ``aiomqtt``.

Usage:
    python tools/build_ha_bundle.py [OUTPUT_ZIP]
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "src" / "vidaa_tv"
COMPONENT = ROOT / "custom_components" / "hisense_vidaa"
PACKAGE = "custom_components.hisense_vidaa.vidaa_tv"

_IMPORT = re.compile(r"^(\s*)from vidaa_tv(\.[\w.]+)? import ", re.MULTILINE)


def _library_source(text: str) -> str:
    return _IMPORT.sub(lambda m: f"{m.group(1)}from {PACKAGE}{m.group(2) or ''} import ", text)


def _adapter_source(text: str) -> str:
    return _IMPORT.sub(lambda m: f"{m.group(1)}from .vidaa_tv{m.group(2) or ''} import ", text)


def _files(base: Path):
    for path in sorted(base.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            yield path


def build(output: Path) -> int:
    count = 0
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in _files(LIBRARY):
            rel = path.relative_to(LIBRARY).as_posix()
            arc = f"custom_components/hisense_vidaa/vidaa_tv/{rel}"
            if path.suffix == ".py":
                bundle.writestr(arc, _library_source(path.read_text(encoding="utf-8")))
            else:
                bundle.write(path, arc)
            count += 1
        for path in _files(COMPONENT):
            rel = path.relative_to(COMPONENT).as_posix()
            arc = f"custom_components/hisense_vidaa/{rel}"
            if rel == "manifest.json":
                manifest = json.loads(path.read_text(encoding="utf-8"))
                manifest["requirements"] = ["aiomqtt>=2.0"]  # library is bundled
                bundle.writestr(arc, json.dumps(manifest, indent=2) + "\n")
            elif path.suffix == ".py":
                bundle.writestr(arc, _adapter_source(path.read_text(encoding="utf-8")))
            else:
                bundle.write(path, arc)
            count += 1
    return count


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "hisense_vidaa_ha_test.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"{build(target)} files -> {target}")
