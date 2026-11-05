"""Keep the vendored copy of the library inside the Home Assistant component in sync.

Home Assistant installs ``custom_components/hisense_vidaa`` as it is, so the component
carries its own copy of ``vidaa_tv``. ``src/vidaa_tv`` stays the single source of truth.

Usage:
    python tools/sync_vendor.py          # refresh the copy
    python tools/sync_vendor.py --check  # exit 1 when the copy is out of date
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "vidaa_tv"
TARGET = ROOT / "custom_components" / "hisense_vidaa" / "vidaa_tv"


def _tree(base: Path) -> dict[str, bytes]:
    return {
        path.relative_to(base).as_posix(): path.read_bytes()
        for path in sorted(base.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def differences() -> list[str]:
    source = _tree(SOURCE)
    target = _tree(TARGET) if TARGET.exists() else {}
    problems = [f"missing: {name}" for name in sorted(source.keys() - target.keys())]
    problems += [f"stale:   {name}" for name in sorted(target.keys() - source.keys())]
    problems += [
        f"differs: {name}"
        for name in sorted(source.keys() & target.keys())
        if source[name] != target[name]
    ]
    return problems


def sync() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def main() -> int:
    if "--check" in sys.argv:
        problems = differences()
        for line in problems:
            print(line)
        if problems:
            print("vendored copy is out of date: run python tools/sync_vendor.py", file=sys.stderr)
            return 1
        print("vendored copy is in sync")
        return 0
    sync()
    print(f"synced {SOURCE.relative_to(ROOT)} -> {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
