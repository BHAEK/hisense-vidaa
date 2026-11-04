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

- Code, comments, docs and commit messages are in English.
- Keep commits small and focused; use conventional prefixes (`feat`, `fix`, `docs`,
  `test`, `chore`, `refactor`).
- Add tests for every behaviour change; transports are faked in `tests/fakes.py`.
- Work on a branch and open a pull request against `main`.

## Privacy

Never commit captures, decompiled vendor code, APKs, certificates, tokens, or the
MAC address, IP address or device id of a real TV. Redact them in logs and docs.
