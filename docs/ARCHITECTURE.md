# Architecture

## Layers

Dependencies point strictly downwards; no layer imports from one above it.

```
Home Assistant adapter   custom_components/hisense_vidaa
          |
      Client facade      vidaa_tv.client
          |
     Capabilities        vidaa_tv.capabilities   (power, volume, sources, apps, ...)
          |
       Protocol          vidaa_tv.protocol       (topics, codecs, auth)
          |
       Transport         vidaa_tv.transport      (abstract Transport; MQTT/TLS impl)
```

`vidaa_tv.discovery` (SSDP/mDNS, Wake-on-LAN) is independent of the session stack.

## Principles

- **Low coupling**: layers talk through small interfaces (`Transport` is a
  `typing.Protocol`), so every layer is testable with fakes.
- **High cohesion**: one capability per module; a capability knows its topics
  and payloads, nothing else.
- **Firmware variance**: older VIDAA versions expose fewer features.
  Capabilities are probed at connect time and raise `UnsupportedFeatureError`
  instead of failing silently.
- **No HA imports** inside `vidaa_tv`.
