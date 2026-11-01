# Protocol notes

Status legend: **[confirmed]** observed on the target TV, **[reported]** taken from
community sources or an existing integration but not yet reproduced here,
**[open]** unknown.

Target: Hisense H65B7320, software V0001.01.00a.P0219 (user-reported).

## Transport

- MQTT v3.1.1 over TLS, port 36669, server certificate not verified. **[confirmed]**
- A client certificate is presented; the profile that works on this TV is the
  static "legacy app" one (static MQTT username/password, no token). **[confirmed]**
- The client certificate is extracted by the user from the vendor app and is
  never distributed with this project.

## Identity and topics

- Client id and topic segment: `<MAC>$vidaa_common`. **[confirmed]**
- Publish: `/remoteapp/tv/<service>/<client>/actions/<action>`
- Subscribe: `/remoteapp/mobile/<client>/#` plus
  `/remoteapp/mobile/broadcast/ui_service/state`. **[confirmed]**
  (Other sources report wildcard subscriptions being refused on some firmware.)

| Service | Action | Payload | Status |
| --- | --- | --- | --- |
| `remote_service` | `sendkey` | raw key name, e.g. `KEY_VOLUMEUP` | confirmed |
| `platform_service` | `getvolume` | empty | confirmed |
| `platform_service` | `changevolume` | `"NN"` | ignored when audio goes through ARC/CEC |
| `ui_service` | `gettvstate` | empty | confirmed |
| `ui_service` | `sourcelist` | empty | confirmed |
| `ui_service` | `changesource` | `{"sourceid": "N", "sourcename": "NAME"}` | confirmed |
| `ui_service` | `applist` | empty | reported |
| `ui_service` | `launchapp` | `{"appId", "name", "url", "urlType": 37, "storeType": 0}` | open |
| `ui_service` | `capability` | empty | sent by existing integration, response unknown |

Observed `gettvstate` response:

```json
{"statetype":"sourceswitch","sourceid":"HDMI2","sourcename":"HDMI2","is_signal":1,"is_lock":0,"hotel_mode":0,"displayname":"HDMI2"}
```

Sources seen: `TV`, `HDMI1`, `HDMI2`, `HDMI3`, `AV`. A source id was once reported
as `HDMI2-0`; the state payload may be null while the TV is on.

## Power

- Power off: `KEY_POWER`. **[confirmed]**
- Power on: Wake-on-LAN magic packet (UDP 9 and 7, broadcast) plus the vendor
  packet `FF*6 + MAC*16 + 00*6` on UDP 33129, repeated 5 times at 0.1 s.
  **[open]** whether it works without HDMI-CEC help from another device.
- While in standby the broker is unreachable (`Host is unreachable`): the TV
  cannot be queried and must be treated as "off" on connection failure.

## Known quirks

- Volume set is unreliable with external audio over ARC/CEC; volume stepping
  with keys works. The `volume_type` field (1 = ARC) identifies that case.
- Mute state cannot be read when audio is on ARC.
- Back is `KEY_RETURNS`; `KEY_BACK` is rewind and `KEY_FORWARDS` is fast-forward.

## Open questions

1. Does `applist` / `launchapp` work on this firmware?
2. Is a token ever required, or is the static profile enough for every call?
3. What does `capability` return?
4. Is the vendor wake packet effective on its own?
5. Why does the TV occasionally turn on for about a minute at night?
