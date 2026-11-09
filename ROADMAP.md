# Roadmap

Status of the work towards the first public release (`0.1.0`) and beyond.
`[x]` done, `[ ]` open, **(field)** needs a real TV and a person in front of it.

## Release policy

Current step: `0.1.0` is released (F9 is green; F10 and F12 stay open and are tracked in
`docs/compatibility.md`). Fixes follow as `0.1.x`.

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

- [x] The connection supervisor never dies on an unexpected error; failures are logged.
- [x] Transport errors on subscribe and on the message stream end the session and trigger a
      reconnect instead of leaving stale state.
- [x] Background tasks are owned by the config entry and stop cleanly on unload/shutdown.
- [x] The MQTT transport is covered by automated tests (fake broker client).
- [x] Availability transitions are logged once ("unavailable" / "back online").

### 2. Behaviour fixes

- [x] Mute is an assumed state: a request only sends the key when it changes the state.
- [x] Turn off is a no-op unless the TV is on.
- [x] Turn on sends the wake-up and returns; a background check logs if the TV stays away.
- [x] Media position is refreshed only when the TV pushes a change.
- [x] The device registry is updated only when the identity information changes.
- [x] Neutral default title (no IP address); entity names and errors are translated (media
      browser folder titles stay in English).
- [x] Current Home Assistant APIs (`AddConfigEntryEntitiesCallback`), runtime data types in
      their own module, `loggers` declared in the manifest.

### 3. Install and update path

- [x] The library uses relative imports, so the same source runs standalone and vendored.
- [x] A vendored copy lives in `custom_components/hisense_vidaa/vidaa_tv/`, produced by
      `tools/sync_vendor.py` and verified in CI.
- [x] Manifest requires only a pinned `aiomqtt`; no dependency on an unpublished package.
- [x] Single version source with a consistency check.
- [x] `CHANGELOG.md`, `hacs.json`, `brand/` assets.
- [x] Repository description and topics on GitHub.
- [x] Release workflow: tag → checks → `hisense_vidaa.zip` → GitHub release (proven by the
      `v0.1.0rc1` tag).
- [x] `SECURITY.md`, issue and pull request templates, Dependabot.
- [x] README: installation (store, custom repository, manual) and how updates arrive.

### 4. Configuration

- [x] Stable config entry id taken from the TV itself (survives IP changes).
- [x] Reconfigure flow (new address).
- [x] Reauthentication flow when the TV forgets the paired identity.

### 5. CI and tests

- [x] `hassfest` and the HACS validation run on every push and are green.
- [x] Adapter tests on the Home Assistant test harness (Python 3.14): config flow, setup,
      entities, diagnostics.
- [x] Coverage reported; library gate at 85 %.

### 6. Field validation (needs the TV)

Run together before tagging `0.1.0`:

- [ ] **(field)** F1 (not blocking, deferred) Wake-up window: turn the TV off, then wake it after 10, 20, 30, 60 and
      120 minutes; note Wi-Fi vs Ethernet and the two network wake settings.
- [x] **(field)** F2 Live TV from Home Assistant: channel, programme, duration and position,
      channel by number/name, media browser.
- [x] **(field)** F3 Apps: launch every listed app (including the ones with a web URL) and
      check the app selector follows.
- [x] **(field)** F4 Reconnect: power-cycle the TV from the remote, restart Home Assistant,
      unplug the TV; entities must recover with no reload and the log must show one
      "unavailable" and one "back online" line.
- [x] **(field)** F5 Pairing from the Home Assistant UI with a fresh identity (new entry,
      stable id from the TV, entities created, entity settings restored afterwards).
- [x] **(field)** F6 Reconfigure (change the address, wrong address refused, right address
      accepted) works from the interface. Re-authentication is covered by automated tests only
      and is listed as untested in `docs/compatibility.md`.
- [x] **(field)** F7 Mute behaviour and absolute volume with the TV speakers selected
      (non-ARC output): the mute request sends the key only when it changes the assumed
      state, and the volume slider appears and sets the exact level without ARC. Confirmed
      limit: muting with the remote is not noticed, so the next mute request in Home
      Assistant un-mutes the TV while Home Assistant reports it as muted.
- [x] **(field)** F8 Diagnostics download reviewed: address, MAC, client identity, TV id and entry
      id are redacted; the programme title no longer is (it was over-redacted).
- [x] **(field)** F9 Install from the published repository (done: installed from HACS as a
      custom repository) and update to the next release (done: the update was offered and applied).
- [ ] **(field)** F10 One day with debug logging; look for connection flaps and for the slow
      config entry setup seen at startup (about 7 s in the diagnostics timings).
- [x] **(field)** F11 The label reads `H65B7320` while the TV reports `65A6101EE_0001` in its
      capability message: that value is an internal board/panel code, not the model name, so
      it is shown as the model id and the model is shown generically.
- [ ] **(field)** F12 PIN starting with zero: sent as a JSON number it was rejected by the TV
      (confirmed); the PIN is now sent as a string like the vendor app does. Still to verify
      on the TV: a normal PIN with the string form, and a PIN with a leading zero when one
      turns up.
- [x] **(field)** F17 Explicit mute: `KEY_TVMUTE` and `KEY_TVUNMUTE` do nothing on the reference
      TV, `KEY_MUTE` is a plain toggle, and neither the key nor `getvolume` produces any
      message about the mute state (no `volume_type` 2). Mute therefore stays an assumed
      state; it only drifts if the TV is muted with another remote.
- [x] **(field)** F13 Alternative standby: `KEY_SAVEPOWERS` and `KEY_SLEEPS` were sent and
      watched (screen, MQTT port, pushes): neither has any effect on the reference TV. The
      TV does not report `fake_sleep`, so `KEY_POWER` is a full standby and the only
      reliable wake-up is the network packet or an HDMI-CEC device.
- [x] **(field)** F14 First CI run of hassfest, the HACS validation and the integration tests
      on GitHub is green.
- [x] **(field)** F15 The MAC address is learned automatically when left empty at setup.
- [x] **(field)** F16 Turn off and on from Home Assistant: turn on is confirmed (wake-up
      packets, TV reachable 7 s later, "back online" logged); turn off, the no-op while off,
      and a wake-up after 5 minutes of standby from Home Assistant all work.

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
- With audio on ARC the TV ignores absolute volume (step only) and cannot report mute; mute
  is therefore an assumed state and goes out of step when the TV is muted with the remote.
- Playback keys reach the TV's HDMI-CEC devices only when the TV forwards them.
- Verified on a single model and firmware (`V0001.01.00a.P0219`, 2018 generation).
