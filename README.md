# hisense-vidaa

Async Python library and Home Assistant integration for Hisense TVs running
**VIDAA OS**, including older firmware generations.

The protocol is reverse engineered from the vendor remote app and verified on real
hardware. Every feature listed below was exercised on a TV running software
`V0001.01.00a.P0219` (board MSD6886, 2018 generation).

> Status: early development (`0.1.0`). Independent community project, not affiliated
> with or endorsed by Hisense or VIDAA.

## What works

| Area | Features |
| --- | --- |
| Pairing | PIN pairing of a new client identity; known identities reconnect silently |
| Power | Turn off; turn on over the network (Wake-on-LAN and the VIDAA wake packet) |
| State (push) | Power, source, live channel and current programme, running app, volume |
| Remote | Every key of the vendor remote (180+ key names), including navigation forwarded to HDMI-CEC devices |
| Volume | Step up/down, mute toggle (the TV cannot report mute or set absolute volume over ARC) |
| Sources | List and switch (TV, AV, HDMI) |
| Apps | List and launch installed apps |
| Channels | Channel lists, tuning by number or name |

Not available on this firmware (verified, see `docs/reverse-engineering/`): remote
picture settings, screenshots, programme guide data, recordings.

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

## Home Assistant

The `custom_components/hisense_vidaa` folder is a thin adapter over the library.

| Platform | Entities |
| --- | --- |
| `media_player` | power, volume (step; absolute when audio is not on ARC), mute, play/pause/stop keys, source and app selection, channel by number/name, programme duration and position, media browser (channels and apps) |
| `remote` | send any key, with repeats |
| `sensor` | source, channel, programme, programme end, volume |
| `select` | input source, app |
| `button` | common remote keys |
| `binary_sensor` | connection status (diagnostic) |

Home Assistant keeps its configuration folder off the import path, so for manual
installs build a self-contained copy of the component:

```bash
python tools/build_ha_bundle.py        # writes dist/hisense_vidaa_ha_test.zip
```

Unzip it into the Home Assistant configuration directory (it only adds
`custom_components/hisense_vidaa`), restart, then add **Hisense VIDAA** from
*Settings → Devices & services* with the TV's address and, optionally, its MAC.
Keep the TV on and watch for the PIN. The MAC address may be left empty: it is read from
the host's neighbour table once the TV is connected (same network segment required) and
stored. Commands sent while the TV is off fail with a clear message, and a diagnostics
download with identifiers redacted is available from the device page.

## Requirements and TV settings

- Python 3.11+ for the library; the `mqtt` extra installs `aiomqtt`.
- The TV must be on the same network. Presence is detected through its MQTT port
  (36669); the TV never answers ping.
- To wake the TV, enable **Wake on LAN** (and the wireless wake option on Wi-Fi) in
  the TV network settings, and supply the TV's MAC address.
- On Windows, `aiomqtt` needs the selector event loop
  (`asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)`).

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/vidaa_tv/` | Client library |
| `custom_components/hisense_vidaa/` | Home Assistant adapter |
| `docs/` | Architecture and reverse-engineering notes |
| `tools/` | Diagnostic probe and bundle builder |
| `tests/` | Unit tests |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the layering and
[`docs/reverse-engineering/`](docs/reverse-engineering/) for the protocol notes.

## Development

```bash
python -m venv .venv
pip install -e ".[dev,mqtt]"
pytest
ruff check .
mypy src
```

Contributions are welcome; see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Diagnostics

`tools/probe.py HOST` pairs (if needed) and records how a TV answers each query, so
other firmware generations can be documented. Captures go to a git-ignored folder and
should be redacted before being shared: they contain the TV's device id.

## License

MIT
