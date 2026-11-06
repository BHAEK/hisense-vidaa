# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org).

## [Unreleased]

## [0.1.0.dev2] - 2026-11-06

Hardening and release preparation.

### Added

- Re-authentication when the TV no longer recognises the client, a reconfigure flow for a
  new address, and a config entry id taken from the TV's own device id.
- The Home Assistant component ships a generated copy of the library (checked in CI) and
  pins `aiomqtt`; no unpublished package is required.
- Release packaging: `hacs.json`, brand icons, a release workflow that builds
  `hisense_vidaa.zip`, hassfest and HACS validation.
- Integration tests on the Home Assistant test kit, MQTT transport tests and a library
  coverage gate (85 %).
- `SECURITY.md`, issue and pull request templates, Dependabot, a roadmap.

### Changed

- Mute is an assumed state; turn off is a no-op unless the TV is on; turn on returns after
  sending the wake-up and a background check logs the outcome.
- Media position is stable between TV pushes; the device registry is updated only when the
  TV identity changes; the default title no longer contains the address.
- Background tasks belong to the config entry and stop with it.
- The library uses relative imports and a single version source.

### Fixed

- The device model reported by the TV is no longer overwritten by the entities.

## [0.1.0.dev1] - 2026-11-05

First development snapshot.

### Added

- Async client library for Hisense VIDAA TVs: PIN pairing, push-based state tracking,
  remote keys, volume, sources, apps, channels, power off and network wake-up.
- Home Assistant integration: media player, remote, sensors, selects, buttons,
  connection sensor, diagnostics, media browser.
- Reverse-engineering notes and a diagnostic probe for other firmware generations.

### Fixed

- Subscription and message-stream failures end the session and trigger a reconnect.
- The connection supervisor survives unexpected errors and logs availability changes.
