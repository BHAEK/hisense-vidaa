# Architecture

## Layers

Dependencies point strictly downwards; no layer imports from one above it.

```
Home Assistant adapter   custom_components/hisense_vidaa
          |
      Client facade      vidaa_tv.client      (VidaaClient)
        /      \
 Supervisor   Tracker    vidaa_tv.supervisor, vidaa_tv.tracker
        \      /
     Capabilities        vidaa_tv.capabilities (remote, power, volume, sources, apps, channels)
          |
        Session          vidaa_tv.session     (send, request/reply matching, listeners)
          |
       Protocol          vidaa_tv.protocol    (topics, codec, parsers, auth)
          |
       Transport         vidaa_tv.transport   (abstract Transport; MQTT/TLS implementation)
```

`vidaa_tv.discovery` (wake packets, reachability) and `vidaa_tv.pairing` sit beside the
session stack: the TV is unreachable while asleep, so waking it cannot go through a session.

## Main ideas

- **The TV talks by pushing.** Many requests are answered with broadcast pushes instead of
  dedicated replies. `StateTracker` folds pushes into an immutable `Snapshot`; `Session`
  recognises replies by payload shape (`ReplyMatcher`) rather than by topic.
- **Off is a normal state.** A standby TV refuses connections. `Supervisor` reconnects with
  back-off and reports the TV as `OFF` instead of raising.
- **Interfaces over implementations.** `Transport` is a `typing.Protocol`; tests use an
  in-memory fake, and the MQTT implementation is an optional extra.
- **One capability per module.** A capability knows its actions and payloads and nothing
  about the others. `VidaaClient` composes them.
- **Pure parsing.** `protocol.parsers` turns payloads into immutable models with no I/O.
- **No Home Assistant in the library.** The adapter only maps snapshots to entities and
  entity commands to capability calls.

## Firmware variance

Older VIDAA versions expose fewer features. Features that the TV does not answer
(picture settings, screenshots, programme guide, recordings on the reference firmware)
are documented in `docs/reverse-engineering/` and must be detected, not assumed.
