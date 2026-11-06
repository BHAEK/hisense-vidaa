# Protocol notes

Status legend: **[confirmed]** observed on the target TV, **[reported]** taken from
community sources or an existing integration but not yet reproduced here,
**[open]** unknown.

Target: Hisense, board MSD6886, software V0001.01.00a.P0219
(model H65B7320, user-reported, not yet confirmed by the TV itself).

## Transport

- MQTT v3.1.1 over TLS, port 36669, server certificate not verified. **[confirmed]**
- Both "TLS with client certificate" and "TLS without client certificate" are
  accepted by the broker. Plain (non-TLS) MQTT is refused. **[confirmed]**
- Credentials are the static pair (no token). **[confirmed]**
- The client certificate is extracted by the user from the vendor app and is
  never distributed with this project.
- The TV drops idle sessions; clients must reconnect transparently.

## Identity and topics

- Client id and topic segment: `<MAC>$vidaa_common`. **[confirmed]**
- Publish: `/remoteapp/tv/<service>/<client>/actions/<action>`
- Subscribe: `/remoteapp/mobile/<client>/#` and `/remoteapp/mobile/broadcast/#`
  (wildcards are accepted on this firmware). **[confirmed]**
- Pairing is described in [pairing.md](pairing.md).

## Commands

| Service | Action | Payload | Status |
| --- | --- | --- | --- |
| `remote_service` | `sendkey` | raw key name, e.g. `KEY_VOLUMEUP` | confirmed |
| `platform_service` | `getvolume` | empty | confirmed |
| `platform_service` | `changevolume` | number as string | **ineffective with ARC audio** |
| `ui_service` | `gettvstate` | empty | confirmed |
| `ui_service` | `capability` | empty | confirmed |
| `ui_service` | `sourcelist` | empty | confirmed |
| `ui_service` | `changesource` | `{"sourceid":"4","sourcename":"HDMI1"}` | confirmed |
| `ui_service` | `applist` | empty | confirmed |
| `ui_service` | `launchapp` | `{"appId","name","url","urlType","storeType"}` copied from `applist` | confirmed (YouTube Kids) |

## Replies and pushes  **[confirmed]**

| Topic | Payload |
| --- | --- |
| `<client>/ui_service/data/sourcelist` | list of sources (below) |
| `<client>/ui_service/data/applist` | list of apps (below) |
| `<client>/ui_service/data/authenticationcode` | `{"result":1,"info":""}` |
| `broadcast/ui_service/state` | state object, e.g. `{"statetype":"sourceswitch","sourceid":"HDMI2",...}` |
| `broadcast/platform_service/actions/volumechange` | `{"volume_type":1,"volume_value":N}` |

`gettvstate` reply: `{"statetype":"sourceswitch","sourceid":"HDMI2","sourcename":"HDMI2","is_signal":1,"is_lock":0,"hotel_mode":0,"displayname":"HDMI2"}`.
The state may be null while on, and the source id was once seen as `HDMI2-0`.

`capability` reply (truncated in the source):
`{"pvr":0,"reminder":1,"boardVersion":"MSD6886","produceDate":"P0219","uniqueDeviceId":"<id>","softwareVersion":"V0001.01.00a.P0219","vendorBrand":...}`.

### Sources

Ids are numeric strings; `changesource` takes the id and the name.

| Name | id |
| --- | --- |
| TV | 0 |
| AV | 1 |
| HDMI1 | 4 |
| HDMI2 | 5 |
| HDMI3 | 6 |

Each entry has `sourcename`, `displayname`, `is_signal`, `is_lock`, `hotel_mode`
(all strings in `sourcelist`). Note `gettvstate` reports the source as a name
and a number in different places; normalise both.

### Apps

```json
{"url":"netflix","isunInstalled":false,"name":"Netflix","from":"","urlType":37,"storeType":0,"appId":"1"}
```

Seen: Netflix, Prime Video, YouTube (`urlType` 37, `storeType` 0); Disney+ and
RaiPlay with https URLs and `storeType` 99.

## Volume  **[confirmed]**

- Audio routed to an ARC soundbar reports `volume_type` 1. `changevolume`
  (several payload shapes, on several services) does not change the value.
- `KEY_VOLUMEUP` / `KEY_VOLUMEDOWN` do. A target of N may land on N+1.
- `volume_type` is the audio output, **not** a mute flag. Mute state is not
  readable with ARC; `KEY_MUTE` only toggles.

## Power

Measured on the target TV (connected over Wi-Fi, "Wake on LAN" and the wireless
wake option both enabled in the TV network settings):

- Power off: `KEY_POWER`. The TV pushes `broadcast/platform_service/actions/tvsleep`
  (empty payload) about half a second later and leaves the network within ~3 s: no
  ICMP echo, MQTT port closed. This is a full standby, not a "fake sleep". **[confirmed]**
- Power on: a magic packet to the subnet broadcast address wakes the TV. Either of
  these works on its own, sent 5 times 100 ms apart: **[confirmed]**
  - standard WoL, UDP port 9 and 7: `FF*6 + MAC*16`
  - VIDAA packet, UDP port 33129: `FF*6 + MAC*16 + 00*6`
- Measured at 2 min and at 5 min of standby: the MQTT port is open ~7 s after the
  packets. After a cold start by remote the port opened within 37 s.
- The TV does **not** answer ICMP echo at all (also when on); use the MQTT port
  as the presence signal.
- Earlier attempts that failed (WoL, VIDAA packet, unicast) happened before the user
  confirmed the TV network settings; the working configuration has both toggles on.
  Whether the setting was the cause is **[probable, not isolated]**.
- A sleeping TV has no ARP entry on the sender; unicast to its IP is unreliable,
  broadcast works.
- Waking an HDMI-CEC source (e.g. a Fire TV) also switches the TV on.
- In standby the broker is unreachable (`Host is unreachable`). Treat connection
  failure as "off", not as an error.

How the vendor app does it (decompiled): it sends the VIDAA packet unicast to the
last known IP on port 33129, 5 times 100 ms apart, once per known MAC (it stores a
Wi-Fi and an Ethernet MAC per TV), then re-runs device discovery every 5 s for up
to ~50 s. On receiving `tvsleep` it marks the TV as disconnected.

## Keys

Back is `KEY_RETURNS`. the vendor app names rewind `KEY_BACKS` and fast-forward `KEY_FORWARDS` (community notes say `KEY_BACK` for rewind; to verify on the TV).
Play/pause sent through the TV does not reach a CEC source, although the physical
remote does via CEC; this is a TV-side limitation.

## Open questions

1. Does `launchapp` also work for apps with `storeType` 99 (Disney+, RaiPlay)?
2. Is the TV network wake setting the only thing that made wake-up reliable?
3. What are the remaining fields of the `capability` reply?
4. Is the model H65B7320 reported anywhere by the TV?

## Probe results, 2026-11-05 (fresh client identity, TLS without client certificate)

Confirmed with `tools/probe.py` on the target TV:

- Connecting **without a client certificate** works. A new identity gets
  `ui_service/data/authentication` (empty) and the TV shows a 4-digit PIN; the PIN
  is accepted with `{"result":1,"info":""}` and no token follows.
- On connect the TV pushes `broadcast/ui_service/state` (here `livetv` with
  `channel_name`, `channel_num`, `channel_param`, `list_param`, `sourceid`) and
  `broadcast/platform_service/actions/volumechange`.
- `broadcast/ui_service/actions/remote_launcher` (empty payload) repeats about every
  10 s while connected; likely a heartbeat.
- Replies seen: `capability` (adds `chipplatform`, `devicemsg`, `searchnow`,
  `emanual`, `produceDate`, `pvr`, `reminder`, `uniqueDeviceId`, `vendorBrand`),
  `gettvinfo` (`brand, capability, deviceid, featurecode, tuner_num`),
  `sourcelist` (ids 0/1/4/5/6 as above), `applist` (Netflix, Prime Video, Disney+,
  YouTube, RAIPLAY, Chili, Rakuten TV, Kidoodle.TV, YouTube Kids, FITE, ...).
- **No reply at all** to `getdeviceinfo`, to `picturesetting` (neither on
  `platform_service` nor on `ui_service`) and, while on live TV, to `gettvstate`.
  Treat these as unsupported on this firmware; current state must come from the
  connect-time broadcast and later pushes.
- `getvolume` is answered through the `volumechange` push, not a dedicated reply.
- `capability.devicemsg` reads `65A6101EE_0001`, which does not obviously match the
  user-reported model name; the model must not be inferred from the user's value.

## Probe results, 2026-11-05 (second round)

- A client identity paired once reconnects without a PIN and receives the current
  state immediately. **[confirmed]**
- `changesource` works for ids 4 (HDMI1), 0 (TV) and 5 (HDMI2). Each switch is
  confirmed by one or more `broadcast/ui_service/state` pushes; a stale push of the
  previous source can arrive just before the new one, so consumers must use the
  last push, not the first. **[confirmed]**
- Switching to the TV source yields several pushes: `sourceswitch`, then `livetv`
  (channel number and `channel_param`), then `livetv` again with programme data
  (`progname`, `starttime`, `endtime`, `detail`). **[confirmed]**
- `launchapp` with an entry copied from `applist` works: the TV answers with
  `{"statetype":"app","name":"youtube_kids","url":"youtube_kids"}`. **[confirmed]**
- `gettvstate` is answered as a push on `broadcast/ui_service/state`, and only when
  the source is an external input. **[confirmed]**
- `KEY_VOLUMEUP` / `KEY_VOLUMEDOWN` change the volume by exactly 1, confirmed by a
  `volumechange` push (12 -> 13 -> 12). **[confirmed]**
- Navigation keys produce no acknowledgement. Observed on screen: `KEY_UP` and
  `KEY_DOWN` sent while on HDMI2 move the focus of the CEC source (a Fire TV), so
  the TV forwards navigation keys over HDMI-CEC. **[confirmed]**
- `KEY_INFO` on live TV produced no visible banner. Either the key is not mapped on
  this firmware or it needs a different key (e.g. `KEY_EPG`). **[not working]**
- `KEY_SAVEPOWERS` and `KEY_SLEEPS` (defined by the vendor app but not used by its
  interface) produce no visible effect, no push and no change of the network state on the
  reference TV. **[not working]**
- `launchapp` (YouTube Kids), `changesource` and the return to HDMI2 were all
  confirmed visually by the user.

## Probe results, 2026-11-05 (third round: TV functions)

Confirmed visually by the user and by TV pushes:

- `KEY_EPG`, `KEY_SUBTITLE`, `KEY_MENU`, `KEY_EXIT`, `KEY_MUTE` work. The TV also
  pushes a confirmation on `broadcast/ui_service/actions/<name>` (empty payload):
  `remote_epg` for the guide and `remote_setting` for subtitle/menu. These pushes are
  usable as acknowledgements. Returning from a menu produces a `livetv` state push.
- `KEY_INFO` shows nothing on this firmware.
- `platform_service/getchannellistinfo` replies with
  `[{"list_name":"Digitale Terrestre","list_para":"<id>","list_version":"34","dtv_flag":1}]`.
- `platform_service/channellist` needs `{"list_para":"<id>","list_name":"<name>"}` and
  replies on `.../platform_service/data/channellist` with
  `{"list_para","list_name","list":[{"channel_num","channel_name","channel_param"}, ...]}`
  (310 channels on the target TV). Without the payload it does not reply.
- `ui_service/changechannel` with `{"channel_param":"<value from channellist>"}` tunes
  the channel; confirmed on three channels. The `livetv` push sequence repeats the
  previous programme data for a moment before the new one arrives, so consumers must
  keep the last push.
- `channel_param` format: `<num>#ch<uuid>#sl<list uuid>#<flag>`.

## Screenshot (`screencapture`) - not supported on this firmware

The vendor app uses a separate MQTT identity `<MAC>$s_cap`, publishes an empty payload
to `/remoteapp/tv/platform_service/<MAC>$s_cap/actions/screencapture` and expects
`screencaptureinfo` (`{"format","width","height","size"}`) followed by the image bytes on
`screencapturedata`, under `/remoteapp/mobile/<MAC>$s_cap/platform_service/data/`.
The feature is only exposed (in the app's hidden debug screen) when `gettvinfo` reports
`screen_capture_supported`. The target TV's `gettvinfo` does not contain that field.

Tested on the target TV: connection as `$s_cap` is accepted (no PIN, state pushes arrive),
but no reply of any kind came for empty, `{}` and text payloads, from either identity,
on `platform_service` or `ui_service`. **Not supported** on V0001.01.00a.P0219.
The library should gate the feature on the capability flag.

## Probe results, 2026-11-05 (fourth round)

- `launchapp` with `storeType` 99 entries (Disney+, RAIPLAY) works; the TV confirms with
  `{"statetype":"app","name":"disney+","url":"<url>"}` (name lower-cased). **[confirmed]**
- `ui_service/appversion` replies with a bare JSON string (a millisecond timestamp). **[confirmed]**
- `getbookinglist` gets no reply (the TV reports `pvr: 0`); `curallprogram` replies with an
  empty payload (three times): no guide data on this firmware.
- Switching to an HDMI input with a CEC device produces extra pushes on
  `broadcast/platform_service/actions/sourceinsert`: a list of sub-sources such as
  `HDMI2-0` (no signal) then `HDMI2-2` (signal). This explains the `HDMI2-0` source id
  seen earlier. **[confirmed]**
- `is_signal` on the source push can be 0 for a second or two after a switch while the
  input settles.
