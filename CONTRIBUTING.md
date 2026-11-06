# Contributing

## Principles

- **Layers point downwards**: transport → protocol → capabilities → client → Home Assistant
  adapter. A layer never imports from one above it, and `vidaa_tv` never imports
  `homeassistant`.
- **Low coupling, high cohesion**: depend on small interfaces (`typing.Protocol`), one
  capability per module, pure functions where possible.
- **Evidence first**: protocol facts go in `docs/reverse-engineering/` marked as
  confirmed, reported or open, with the firmware they were observed on.
- **Firmware varies**: probe and report what a TV does not support instead of failing
  silently.

## Workflow

```bash
pip install -e ".[dev,mqtt]"
ruff check . && ruff format --check . && mypy src && pytest
```

- After any change under `src/vidaa_tv/`, run `python tools/sync_vendor.py`: the component
  ships a generated copy of the library and CI fails when it is out of date.
- Home Assistant integration tests live in `tests/ha/` and need the Home Assistant test kit
  (Python 3.14 on Linux or macOS); they run in CI.
- Every release needs a matching section in `CHANGELOG.md` and the same version in
  `src/vidaa_tv/__version__.py` and the manifest (`python tools/check_versions.py`).
- Code, comments, docs and commit messages are in English.
- Keep commits small and focused; use conventional prefixes (`feat`, `fix`, `docs`,
  `test`, `chore`, `refactor`).
- Add tests for every behaviour change; transports are faked in `tests/fakes.py`.
- Work on a branch and open a pull request against `main`.

## Privacy

Never commit captures, decompiled vendor code, APKs, certificates, tokens, or the
MAC address, IP address or device id of a real TV. Redact them in logs and docs.
