# Action catalogue (RemoteNOW 5.01.011)

Extracted from the decompiled topic builders of the vendor app. Names are
what the app can send; **availability and payloads on the target firmware must
still be verified** unless marked in `protocol-notes.md`.

Topic form: `/remoteapp/tv/<service>/<client>/actions/<action>`.

## remote_service

| Action | Notes |
| --- | --- |
| `sendkey` | key press (see key list) |
| `mouse` | pointer / air-mouse input |
| `input` | text entry |

## ui_service

| Action | Notes |
| --- | --- |
| `gettvstate` | current source / app |
| `sourcelist`, `changesource` | inputs |
| `applist`, `applisticon`, `appversion`, `launchapp`, `uninstallapp` | applications |
| `changechannel` | tune a channel |
| `playvideo`, `timeseek`, `dlnastop`, `defaultnext`, `defaultprevious` | media push / transport |
| `capability` | device capabilities |
| `picturesetting` | picture adjustments |
| `changetvname` | rename the TV |
| `authenticationcode`, `authenticationcodeclose` | pairing |

(`vidaa_app_connect` is used in pairing but is not built by this app version's
topic helpers; it is sent by other clients and accepted by the target TV.)

## platform_service

| Action | Notes |
| --- | --- |
| `getvolume`, `changevolume` | volume |
| `gettvinfo`, `getdeviceinfo` | identity and hardware info |
| `getchannellistinfo`, `channellist`, `curallprogram` | channel lists |
| `channelepg`, `programinfo` | guide data |
| `addbooking`, `editbooking`, `deletebooking`, `getbookinglist` | reminders / bookings |
| `getbookingconflict`, `applybookingconflict`, `cancelbookingconflict` | booking conflicts |
| `picturesetting` | picture adjustments |
| `screencapture` | TV screenshot |
| `changetvname` | rename the TV |

## avs_service

`voicestart`, `voicestop`, `voicedata` - voice assistant streaming.

## Subscriptions used by the app

`/remoteapp/mobile/broadcast/#` and `/remoteapp/mobile/<client>/#`.

## Key names found in the app

Navigation: `KEY_UP KEY_DOWN KEY_LEFT KEY_RIGHT KEY_OK KEY_ENTER KEY_RETURNS KEY_EXIT KEY_MENU KEY_HOME`
Power/sleep: `KEY_POWER KEY_SLEEPS KEY_SAVEPOWERS`
Volume: `KEY_VOLUMEUP KEY_VOLUMEDOWN KEY_MUTE KEY_TVMUTE KEY_TVUNMUTE KEY_VOICEUP KEY_VOICEDOWN`
Channels: `KEY_CHANNELUP KEY_CHANNELDOWN KEY_CHANNELDOT KEY_CHANNELLINE KEY_PROGRAMS KEY_RADIOS KEY_TVS`
Media: `KEY_PLAY KEY_PAUSE KEY_STOP KEY_FORWARDS KEY_BACKS KEY_NEXT KEY_PREVIOUS KEY_RECORD KEY_TIMESHIFT`
Info: `KEY_INFO KEY_EPG KEY_SUBTITLE KEY_CC KEY_TXT KEY_AUDIO KEY_MTS KEY_SEARCH KEY_ZOOM KEY_SOURCES KEY_FAVORITESS KEY_PVR`
Colours: `KEY_RED KEY_GREEN KEY_YELLOW KEY_BLUE`
Digits: `KEY_0` ... `KEY_9`
Keyboard: `KEY_A` ... `KEY_Z`, `KEY_SPACE`, `KEY_BACKSPACE`, punctuation keys, each with a `...UP` release variant.

Rewind is `KEY_BACKS` in this app and fast-forward `KEY_FORWARDS`; the earlier
community note of `KEY_BACK` for rewind is therefore to be re-checked on the TV.
