# Roadmap

Status of the work towards the first public release (`0.1.0`) and beyond.
`[x]` done, `[ ]` open, **(field)** needs a real TV and a person in front of it.

## Release policy

- [Semantic Versioning](https://semver.org). One version number covers the library and the
  Home Assistant component, because the component ships a vendored copy of the library.
- Pre-releases use `0.1.0.devN` (work in progress) and `0.1.0rcN` (feature complete, in
  field validation). `0.1.0` is tagged only after the field checklist below is green.
- Every version has a section in [`CHANGELOG.md`](CHANGELOG.md), a git tag `vX.Y.Z` and a
  GitHub release carrying `hisense_vidaa.zip`.
- The version lives in `src/vidaa_tv/__version__.py`; CI fails when the component manifest
  or the changelog disagree with it.

## Milestone 0.1.0

### 1. Reliability

- [ ] The connection supervisor never dies on an unexpected error; failures are logged.
- [ ] Transport errors on subscribe and on the message stream end the session and trigger a
      reconnect instead of leaving stale state.
- [ ] Background tasks are owned by the config entry and stop cleanly on unload/shutdown.
- [ ] The MQTT transport is covered by automated tests (fake broker client).
- [ ] Availability transitions are logged once ("unavailable" / "back online").

### 2. Behaviour fixes

- [ ] Mute is an assumed state: a request only sends the key when it changes the state.
- [ ] Turn off is a no-op unless the TV is on.
- [ ] Turn on sends the wake-up and returns; a background check logs if the TV stays away.
- [ ] Media position is refreshed only when the TV pushes a change.
- [ ] The device registry is updated only when the identity information changes.
- [ ] Neutral default title (no IP address); every user-visible string is translated.
- [ ] Current Home Assistant APIs (`AddConfigEntryEntitiesCallback`), runtime data types in
      their own module, `loggers` declared in the manifest.

### 3. Install and update path

- [ ] The library uses relative imports, so the same source runs standalone and vendored.
- [ ] A vendored copy lives in `custom_components/hisense_vidaa/vidaa_tv/`, produced by
      `tools/sync_vendor.py` and verified in CI.
- [ ] Manifest requires only a pinned `aiomqtt`; no dependency on an unpublished package.
- [ ] Single version source with a consistency check.
- [ ] `CHANGELOG.md`, `hacs.json`, `brand/` assets, repository description and topics.
- [ ] Release workflow: tag → checks → `hisense_vidaa.zip` → GitHub release.
- [ ] `SECURITY.md`, issue and pull request templates, Dependabot.
- [ ] README: installation (store, custom repository, manual) and how updates arrive.

### 4. Configuration

- [ ] Stable config entry id taken from the TV itself (survives IP changes).
- [ ] Reconfigure flow (new address).
- [ ] Reauthentication flow when the TV forgets the paired identity.

### 5. CI and tests

- [ ] `hassfest` and the HACS validation run on every push.
- [ ] Adapter tests on the Home Assistant test harness (Python 3.14): config flow, setup,
      entities, diagnostics.
- [ ] Coverage reported; library gate at 85 %.

### 6. Field validation (needs the TV)

Run together before tagging `0.1.0`:

- [ ] **(field)** F1 Wake-up window: turn the TV off, then wake it after 10, 20, 30, 60 and
      120 minutes; note Wi-Fi vs Ethernet and the two network wake settings.
- [ ] **(field)** F2 Live TV from Home Assistant: channel, programme, duration and position,
      channel by number/name, media browser.
- [ ] **(field)** F3 Apps: launch every listed app (including the ones with a web URL) and
      check the app selector follows.
- [ ] **(field)** F4 Reconnect: power-cycle the TV from the remote, restart Home Assistant,
      unplug the TV; entities must recover with no reload and the log must show one
      "unavailable" and one "back online" line.
- [ ] **(field)** F5 Pairing from the Home Assistant UI with a fresh identity.
- [ ] **(field)** F6 Reauthentication (replace the stored identity with an unknown one) and
      reconfigure (change the address).
- [ ] **(field)** F7 Mute behaviour and absolute volume with the TV speakers selected
      (non-ARC output).
- [ ] **(field)** F8 Diagnostics download reviewed for leaked identifiers.
- [ ] **(field)** F9 Install from the published repository and update to the next
      pre-release; confirm the update is offered.
- [ ] **(field)** F10 One day with debug logging; look for connection flaps.
- [ ] **(field)** F11 Check the model name printed on the TV label against what the TV
      reports.

## Backlog (after 0.1.0)

- Options flow: hide sources/apps, custom broadcast address for wake-up.
- SSDP discovery (needs the UPnP description of a TV that is on; match carefully, the
  reported manufacturer may be empty).
- Alternative power-on action (run a user script when network wake-up is not enough).
- On-screen keyboard (`input` action) and pointer (`mouse` action).
- Rename the TV (`changetvname`), uninstall apps (`uninstallapp`).
- Features of other firmware generations: picture settings, screenshot, programme guide,
  recordings. Detect through the capability flags and the diagnostic probe.
- Publish the library on PyPI if there is demand for standalone use.
- More translations.

## Known limits

- Network wake-up is unreliable on some firmware/standby states; a CEC device waking the
  TV is a dependable workaround.
- With audio on ARC the TV ignores absolute volume (step only) and cannot report mute.
- Playback keys reach the TV's HDMI-CEC devices only when the TV forwards them.
- Verified on a single model and firmware (`V0001.01.00a.P0219`, 2018 generation).
