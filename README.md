<div align="center">

<img src="custom_components/hisense_vidaa/brand/icon@2x.png" alt="Hisense VIDAA" width="112">

# Hisense VIDAA for Home Assistant

**Fast, local, push-based control for Hisense TVs running VIDAA OS, including older firmware.**<br>
No cloud, no polling, no account: the TV tells Home Assistant what it is doing the moment it happens.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=BHAEK&repository=hisense-vidaa&category=integration)
&nbsp;
[![Open your Home Assistant instance and start setting up the integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hisense_vidaa)

[![CI](https://github.com/BHAEK/hisense-vidaa/actions/workflows/ci.yml/badge.svg)](https://github.com/BHAEK/hisense-vidaa/actions/workflows/ci.yml)
[![Validate](https://github.com/BHAEK/hisense-vidaa/actions/workflows/validate.yml/badge.svg)](https://github.com/BHAEK/hisense-vidaa/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/BHAEK/hisense-vidaa?include_prereleases&label=release)](https://github.com/BHAEK/hisense-vidaa/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.10%2B-41BDF5.svg)](https://www.home-assistant.io)

</div>

> **Status: release candidate (`0.1.0rc1`).** Built and verified on a real 2018-generation TV.
> Other models are expected to work but are not verified: see [what has been tested](docs/compatibility.md).
> Independent community project, not affiliated with or endorsed by Hisense or VIDAA.

---

## ✨ Highlights

- 📡 **Instant state.** Power, source, channel, programme, running app and volume arrive as pushes from the TV, not from a polling loop.
- 🔌 **Turns the TV on from standby.** Wake-up packets, MAC address detected automatically, and a clear log of what happened.
- 🎛️ **Everything on the remote.** More than 180 keys, volume, sources, apps, and tuning a channel by number or name.
- 🗂️ **Media browser.** Browse the channel list and the installed apps right from the Home Assistant media player.
- 🔄 **Survives reality.** Reconnects by itself when the TV is switched off, unplugged or Home Assistant restarts; no reload needed.
- 🔐 **PIN pairing, re-authentication and reconfigure** from the interface, with a stable id taken from the TV itself.
- 🧰 **A reusable Python library** (`vidaa_tv`) underneath: layered, typed and tested, with the Home Assistant part kept as a thin adapter.

## 🚀 Install

1. Click **Open in HACS** above (or add `https://github.com/BHAEK/hisense-vidaa` as a custom repository of type *Integration*), then install **Hisense VIDAA** and restart Home Assistant.
   Until a stable release exists, versions are pre-releases, which the store shows only if you enable them.
2. Click **Set up integration** above, or go to *Settings → Devices & services → Add integration → Hisense VIDAA*.
3. **Turn the TV on**, enter its IP address and type the **PIN shown on the TV screen** (you have about a minute).

The MAC address is optional: once connected it is read from your network and stored, because it is needed to turn the TV on from standby.

<details>
<summary><b>Manual install</b></summary>

Download `hisense_vidaa.zip` from the [latest release](https://github.com/BHAEK/hisense-vidaa/releases), unzip it into `<config>/custom_components/hisense_vidaa/` and restart Home Assistant. Updating means replacing that folder with the one from the new release. The component carries its own copy of the library; Home Assistant installs the only dependency (`aiomqtt`) by itself.

</details>

## 📺 What you get

| Platform | Entities |
| --- | --- |
| **Media player** | Power, volume (step, or exact level when the audio is not on ARC), mute, play/pause/stop keys, source and app selection, channel by number/name, programme title, duration and position, media browser |
| **Remote** | Send any key, with repeats and delays |
| **Sensors** | Source, channel, programme, programme end, volume |
| **Selects** | Input source, app |
| **Buttons** | The everyday keys: home, menu, back, guide, subtitles, channel, arrows, OK, mute… |
| **Binary sensor** | Connection status (diagnostic) |
| **Diagnostics** | One-click download with addresses and identifiers redacted |

## ✅ Verified on real hardware

Hisense **H65B7320**, software `V0001.01.00a.P0219`, 2018 generation, over Wi-Fi, with the audio on an ARC soundbar and on the TV speakers. Exercised end to end: pairing, live TV, apps, volume and mute, power off and on, reconnection after every kind of interruption, reconfigure, diagnostics.

The honest list of what is **not** verified (newer firmware needing different credentials, TLS client certificates, other models, Ethernet-connected TVs, re-authentication on a real TV, a PIN starting with zero…) is in [`docs/compatibility.md`](docs/compatibility.md). If you have a different TV, a [firmware report](https://github.com/BHAEK/hisense-vidaa/issues/new?template=firmware_report.yml) is the most useful contribution you can make.

## ⚠️ Good to know

- Turn **Wake on LAN** on in the TV network settings (and the wireless wake option if the TV is on Wi-Fi). Network wake-up can be less dependable in some standby states; waking the TV through an HDMI-CEC device is a robust alternative.
- The TV never answers ping; presence is detected on its MQTT port (36669).
- With audio on **ARC** the TV ignores absolute volume (step only) and **cannot report mute**. Mute is therefore tracked as an assumed state: if you mute with the remote, Home Assistant does not notice and its next mute request un-mutes the TV.
- Playback keys reach HDMI devices only when the TV forwards them over CEC.
- Features the reference TV does not offer at all (remote picture settings, screenshots, programme guide, recordings) are documented in [`docs/reverse-engineering`](docs/reverse-engineering/).

## 🐍 Use the library without Home Assistant

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

Python 3.11+; the `mqtt` extra installs `aiomqtt`. On Windows, `aiomqtt` needs the selector event loop (`asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)`). Architecture and design rules: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## 🔬 How it was built

There is no public documentation for the protocol a VIDAA TV speaks to its remote app, so this project was **reverse engineered** and then verified on a real TV:

1. **Prior art first.** The community had already mapped much of the ground. The author's own Home Assistant ran a modified copy of the **[Hisense Laser TV integration](https://github.com/theappartment/hisense-laser-tv-ha)** ("LaserTV"), and the **[pyvidaa](https://github.com/warrenrees/myhisense-tv)** protocol analysis described the MQTT topics, the pairing exchange and the authentication schemes. They were the map; the territory still had to be walked.
2. **The vendor remote app, read statically.** The Android remote-control app was decompiled and studied (never run) to extract the complete catalogue of actions, payload shapes, key names and how the app handles power, volume, mute and standby.
3. **Live probing of a real TV.** A diagnostic probe recorded how the TV answers each query, which ones it ignores, and what it pushes on its own.
4. **Field tests, one by one.** Every feature was exercised on the physical TV and inside a real Home Assistant, including the awkward cases (standby, unplugging, restarts, mute, a PIN starting with zero).
5. **Design lessons from other integrations.** The Home Assistant integrations for LG webOS, Sony Bravia, Samsung, Roku, Philips, Apple TV, Vizio and Android TV were compared to decide what a good TV integration exposes and how it should behave.

The full story, with what was taken from each source and how, is in [`docs/how-it-was-built.md`](docs/how-it-was-built.md).

### 🤖 Built with an AI assistant

The code, tests and documentation were written in pair-programming with **Claude Sonnet** (Anthropic), driven through Claude Code, under the author's direction. The assistant analysed the decompiled app, wrote and refactored the code, ran the probes, designed the test plan and drove the field tests; a second assistant instance running next to Home Assistant provided read-only views of the real installation (logs, states, registries) and restored the setup after tests. The author set the goals, took every decision, and **verified the behaviour on the real TV**, which is what the compatibility page records.

## 🙏 Credits

- **[theappartment/hisense-laser-tv-ha](https://github.com/theappartment/hisense-laser-tv-ha)** (MIT): the integration the author ran at home. Its client and pairing flow were the starting point for understanding the topics, the static credentials and the wake-up packets.
- **[warrenrees/myhisense-tv](https://github.com/warrenrees/myhisense-tv)** (`pyvidaa`, MIT): the protocol analysis (services, topics, pairing, credential schemes) used as a map; the optional dynamic credentials were implemented from the algorithm it documents.
- **[stevene1919/hisense_vidaa](https://github.com/stevene1919/hisense_vidaa)** (MIT) for its notes on the firmware generations and authentication profiles, and the earlier community work it builds on: **[sehaas/ha_hisense_tv](https://github.com/sehaas/ha_hisense_tv)** and **[newAM/hisensetv](https://github.com/newAM/hisensetv)**.
- The Home Assistant developers, for the integrations used as a design reference.

No code was copied from these projects: the behaviour was re-implemented from scratch and re-verified. No vendor code or assets are included.

## 🤝 Contributing

Bug reports, firmware reports and pull requests are welcome: see [`CONTRIBUTING.md`](CONTRIBUTING.md) and the [roadmap](ROADMAP.md). Development setup:

```bash
python -m venv .venv
pip install -e ".[dev,mqtt]"
python tools/sync_vendor.py     # after any change under src/vidaa_tv
pytest && ruff check . && mypy src
```

The Home Assistant integration tests run in CI (Python 3.14, Home Assistant test kit): `pip install pytest-homeassistant-custom-component && pytest tests/ha`.

`tools/probe.py HOST` pairs (if needed) and records how a TV answers each query, so other firmware generations can be documented. Redact captures before sharing them: they contain the TV's device id.

## ⚖️ Disclaimer and license

Hisense and VIDAA are trademarks of their respective owners. This project is independent, community-made and not affiliated with or endorsed by them. The protocol was studied for interoperability with hardware the author owns.

Released under the [MIT license](LICENSE).
