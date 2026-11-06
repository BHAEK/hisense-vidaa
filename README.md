# hisense-vidaa

[![CI](https://github.com/BHAEK/hisense-vidaa/actions/workflows/ci.yml/badge.svg)](https://github.com/BHAEK/hisense-vidaa/actions/workflows/ci.yml)
[![Validate](https://github.com/BHAEK/hisense-vidaa/actions/workflows/validate.yml/badge.svg)](https://github.com/BHAEK/hisense-vidaa/actions/workflows/validate.yml)

Async Python library and Home Assistant integration for Hisense TVs running
**VIDAA OS**, including older firmware generations.

The protocol is reverse engineered from the vendor remote app and verified on real
hardware. Every feature listed below was exercised on a TV running software
`V0001.01.00a.P0219` (board MSD6886, 2018 generation).

> Status: pre-release (`0.1.0.devN`). Independent community project, not affiliated with or
> endorsed by Hisense or VIDAA. See the [roadmap](ROADMAP.md) and the
> [changelog](CHANGELOG.md).

## What works

| Area | Features |
| --- | --- |
| Pairing | PIN pairing of a new client identity; paired identities reconnect silently |
| Power | Turn off; turn on over the network (Wake-on-LAN and the VIDAA wake packet) |
| State (push) | Power, source, live channel and current programme, running app, volume |
| Remote | Every key of the vendor remote (180+ key names), including navigation forwarded to HDMI-CEC devices |
| Volume | Step up/down, mute toggle; absolute volume when the audio is not on ARC |
| Sources | List and switch (TV, AV, HDMI) |
| Apps | List and launch installed apps |
| Channels | Channel lists, tuning by number or name |

Not available on this firmware (verified, see `docs/reverse-engineering/`): remote
picture settings, screenshots, programme guide data, recordings.

## Home Assistant

### Install

**Through the store** (HACS or the built-in marketplace, depending on your Home Assistant
version): add `https://github.com/BHAEK/hisense-vidaa` as a custom repository of type
*Integration*, install **Hisense VIDAA** and restart Home Assistant.

**Manually**: download `hisense_vidaa.zip` from the
[latest release](https://github.com/BHAEK/hisense-vidaa/releases), unzip it into
`<config>/custom_components/hisense_vidaa/` and restart Home Assistant.

### Set up

*Settings → Devices & services → Add integration → Hisense VIDAA.*

1. Turn the TV on and enter its IP address.
2. Type the PIN shown on the TV screen (you have about a minute).
3. The MAC address is optional: once the TV is connected it is read from the network
   neighbour table (same network segment required) and stored. It is needed to turn the TV
   on from standby.

If the TV forgets Home Assistant, a *re-authentication* notice asks for a new PIN; if the TV
gets a new address, use *Reconfigure* on the integration entry.

### Update

Updates arrive through the store when a new release is published (pre-releases are shown
only if you enable them). Manual installs: replace the folder with the one from the new
release and restart. The component carries its own copy of the library, so there is
nothing else to install except `aiomqtt`, which Home Assistant installs by itself.

### Entities

| Platform | Entities |
| --- | --- |
| `media_player` | power, volume (step; absolute when audio is not on ARC), mute, play/pause/stop keys, source and app selection, channel by number/name, programme duration and position, media browser (channels and apps) |
| `remote` | send any key, with repeats |
| `sensor` | source, channel, programme, programme end, volume |
| `select` | input source, app |
| `button` | common remote keys |
| `binary_sensor` | connection status (diagnostic) |

Commands sent while the TV is off fail with a clear message. A diagnostics download with
identifiers redacted is available from the device page.

### TV settings and known limits

- Enable **Wake on LAN** (and the wireless wake option when the TV is on Wi-Fi) in the TV
  network settings. Network wake-up can still be unreliable depending on the TV's standby
  state; waking the TV through an HDMI-CEC device is a dependable alternative.
- Presence is detected through the TV's MQTT port (36669); the TV never answers ping.
- With audio on ARC the TV ignores absolute volume (step only) and cannot report mute, so
  mute is tracked as an assumed state: if you mute the TV with the remote, Home Assistant
  does not notice and its next mute request un-mutes the TV.
- Playback keys reach HDMI devices only when the TV forwards them over CEC.

Tested with Home Assistant 2026.10.

## Library

```python
import asyncio
from vidaa_tv import VidaaClient, RemoteKey, mqtt_transport_factory


async def main() -> None:
    tv = VidaaClient(
        "192.168.1.50",
        device_id="AA:BB:CC:DD:EE:01",  # your paired client identity
        mac="AA:BB:CC:DD:EE:FF",  # the TV's MAC, only needed to wake it
        transport_factory=mqtt_transport_factory(),
    )
    tv.add_listener(lambda snapshot: print(snapshot.power, snapshot.state))
    await tv.start()  # connects and reconnects in the background
    await tv.wait_connected(10)

    await tv.remote.press(RemoteKey.HOME)
    await tv.sources.select("HDMI2")
    await tv.apps.launch("YouTube")
    await tv.turn_off()
    await tv.stop()


asyncio.run(main())
```

Pair a new identity with `PairingFlow` (the TV shows a PIN on screen):

```python
flow = PairingFlow(host, mqtt_transport_factory())
if await flow.start() is PairingOutcome.PIN_REQUIRED:
    await flow.submit_pin(input("PIN: "))
await flow.close()
print(flow.device_id)  # keep it: this is the identity the TV now trusts
```

Python 3.11+; the `mqtt` extra installs `aiomqtt`. On Windows, `aiomqtt` needs the selector
event loop (`asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)`).

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/vidaa_tv/` | Client library (single source of truth) |
| `custom_components/hisense_vidaa/` | Home Assistant adapter; `vidaa_tv/` inside it is a generated copy of the library |
| `docs/` | Architecture and reverse-engineering notes |
| `tools/` | Diagnostic probe, vendoring, release and brand helpers |
| `tests/unit/`, `tests/ha/` | Library tests and Home Assistant integration tests |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the layering and
[`docs/reverse-engineering/`](docs/reverse-engineering/) for the protocol notes.

## Development

```bash
python -m venv .venv
pip install -e ".[dev,mqtt]"
python tools/sync_vendor.py     # after any change under src/vidaa_tv
pytest && ruff check . && mypy src
```

The Home Assistant integration tests need the Home Assistant test kit (Python 3.14, Linux or
macOS) and run in CI: `pip install pytest-homeassistant-custom-component` then
`pytest tests/ha`.

Contributions are welcome; see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Diagnostics for other firmware

`tools/probe.py HOST` pairs (if needed) and records how a TV answers each query, so other
firmware generations can be documented. Captures go to a git-ignored folder and should be
redacted before being shared: they contain the TV's device id.

## License

MIT
