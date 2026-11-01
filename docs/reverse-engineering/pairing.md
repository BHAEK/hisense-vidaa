# Pairing flow

Source: an existing Home Assistant integration that pairs successfully with the
target TV (read from its code, not yet reproduced by this project).
A PIN **is** shown on the TV the first time a new client id connects.

Status: **[reported]**. Client id below is `<MAC>$vidaa_common`; the MAC identifies
the *client* (the host running the integration), not the TV.

## Sequence

1. Connect over MQTT/TLS with the static credentials and client id.
2. Subscribe to `/remoteapp/mobile/<client>/#` and `/remoteapp/mobile/broadcast/#`.
3. Publish, in this order (all under `/remoteapp/tv/ui_service/<client>/actions/`):
   1. `gettvstate` (empty)
   2. `capability` (empty)
   3. `vidaa_app_connect` `{"app_version":2,"connect_result":0,"device_type":"Mobile App"}`
4. The TV shows a PIN on screen.
5. Publish `authenticationcode` with `{"authNum":<digits>}` (a JSON number, not a string).
6. Wait for a reply object containing `"result"`; `result == 1` means accepted.
7. Publish `authenticationcodeclose` (empty).
8. Optionally wait for `tokenissuance` (`accesstoken` / `refreshtoken`).
   On the target TV no token is issued, and later sessions work with the paired
   client id alone.

## Reply recognition

Replies are not tied to a per-command topic. They are recognised by payload shape:

| Request | Reply predicate |
| --- | --- |
| `gettvstate` | object with `statetype` |
| `getvolume` | object with a volume-related key (`volume_type`, `volume_value`, ...) |
| `sourcelist` | list, or object with `sources` / `sourcelist` |
| `applist` | list of objects with `url` |
| `authenticationcode` | object with `result` |

Empty payloads on the subscribed topics also occur (e.g. the "PIN displayed"
notification) and must be tolerated.

## Design consequences

- A `Session` subscribes to wildcards and matches replies with predicates.
- A pairing step must be a first-class, interactive operation of the library
  (start pairing, supply PIN, persist client id), separate from normal use.
