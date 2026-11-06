## What changes

## Why

## Checklist

- [ ] `ruff check . && ruff format --check . && mypy src && pytest` pass
- [ ] `python tools/sync_vendor.py` was run (the vendored copy matches `src/vidaa_tv`)
- [ ] Integration tests pass (`pytest tests/ha`) when the adapter changed
- [ ] `CHANGELOG.md` updated
- [ ] No addresses, MACs, device ids or captures in the change
