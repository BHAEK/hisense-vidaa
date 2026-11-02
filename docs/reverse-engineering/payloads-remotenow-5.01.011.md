# Payload shapes (RemoteNOW 5.01.011)

Derived from the vendor app's data classes and request builders. Field names are
exact; whether a given TV answers is **[open]** until tested on the target firmware.
Reply topics follow `/remoteapp/mobile/<client>/<service>/data/<action>`; unsolicited
pushes use `/remoteapp/mobile/broadcast/<service>/...`.

## Picture settings (`picturesetting`)

The same action name exists on **both** `platform_service` and `ui_service`. The app
sends the "get" to both (ui_service after 50 ms); writes go to either depending on
the picture-menu generation of the TV. Which one the target TV uses is **[open]**.

Request (all JSON):

| Purpose | Payload |
| --- | --- |
| List all menus | `{"action":"get_menu_info"}` |
| Set a value | `{"action":"set_value","menu_id":<int>,"menu_value":<int>,"menu_value_type":"<type>"}` |
| Trigger an action | `{"action":"on_action","menu_id":<int>,"menu_value":"<string>","menu_value_type":"string"}` |

Replies:

- `resp_get_menu_info`:
  `{"action":"resp_get_menu_info","pic_setting_version":"..","menu_info":[{"menu_id":<int>,"menu_name":"..","menu_value":"..","menu_value_type":"..","menu_flag":<int>}]}`
- set confirmation:
  `{"action":"<name>","menu_id":<int>,"menu_value":<int>,"menu_value_type":"<type>"}`

Menu ids referenced by the app include 1 (picture mode), 3, 70 and 84; the
catalogue itself comes from `get_menu_info`, so the library should treat the menu
list as data and not hard-code ids.

## Device and TV information (platform_service)

- `getdeviceinfo` reply fields: `country, ip, language, model_name, platform,
  region, transport_protocol, tv_name, tv_version, vidaa_support, voice`.
  This is the likely place where the model name (H65B7320) appears.
- `gettvinfo`: TV identity (shape not yet extracted).
- `screencapture` request; replies arrive as `screencaptureinfo`
  (`{"format","width","height","size"}`) followed by raw bytes on `screencapturedata`.

## Capability (ui_service)

`capability` reply, TV part: `brand, featurecode, deviceid, capability, tuner_num,
fake_sleep, fake_sleep_state, audio_capture_supported, screen_capture_supported,
audio_capture_version`. UI part: `baseUIVersion, deviceType, launcherVersion,
sportappVersion, tvBrowser, vidaaappVersion`. App part: `emanual, fourknow, search`.

`fake_sleep` / `fake_sleep_state` describe a **fake standby** (screen off, network
alive). Related broadcast states `fake_sleep_0` and `fake_sleep_1` exist (below).

## Sources, apps, volume

- Source: `sourceid, sourcename, displayname, is_signal, is_lock, hotel_mode, httpIcon`.
- App: `appId, name, url, urlType, storeType, from, icon, hasDetailPage,
  isFavorite, isunInstalled`. Uninstall payload: `{"from","name","url"}`.
- Volume: `{"volume_type":<int>,"volume_value":<int>}`.
- Authentication result: `{"result":<int>,"info":"<text>"}`.

## Broadcast `ui_service/state` types

`statetype` values the app reacts to:
`sourceswitch, livetv, mediadmp, mediadlna, tshift, app, input, mouse, voicestate,
fake_sleep_0, fake_sleep_1`.

## Platform reply topics seen by the app

`addbooking, applybookingconflict, channelepg, channellist, curallprogram,
deletebooking, editbooking, getbookingconflict, getbookinglist, getchannellistinfo,
getdeviceinfo, gettvinfo, getvolume, picturesetting, programinfo, screencapturedata,
screencaptureinfo`.

## Consequences for the library

- Add `DeviceInfo`, `TvCapability` and `PictureMenu` models and capabilities;
  treat the picture-menu catalogue as discovered data.
- Model the TV power state with at least: off (unreachable), fake standby
  (reachable, screen off) and on, driven by `fake_sleep_*` states.
- The `fake_sleep` finding is a candidate explanation for the "TV on for a minute at
  night" and "network slow to come back" observations: **[hypothesis, to test]**.
