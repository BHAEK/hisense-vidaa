# hisense-vidaa

Async Python library and Home Assistant integration for Hisense TVs running
**VIDAA OS**, including older firmware generations.

> Status: early development. The protocol is being documented through
> reverse engineering; see [`docs/`](docs/).

## Goals

- Expose every feature the TV firmware allows (power, keys, volume, sources,
  apps, picture/sound settings, state push, wake-up).
- Strictly layered, modular code with low coupling and high cohesion.
- A reusable library (`vidaa_tv`) with a thin Home Assistant adapter on top.

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/vidaa_tv/` | Client library |
| `custom_components/hisense_vidaa/` | Home Assistant adapter |
| `docs/` | Architecture and protocol documentation |
| `tools/` | Reverse-engineering and diagnostic helpers |
| `tests/` | Unit tests |

## Development

```bash
python -m venv .venv
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

## Disclaimer

This is an independent, community project. It is not affiliated with or
endorsed by Hisense or VIDAA.

## License

MIT
