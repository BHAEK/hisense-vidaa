# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org).

## [Unreleased]

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
