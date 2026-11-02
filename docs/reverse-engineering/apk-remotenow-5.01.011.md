# RemoteNOW 5.01.011 - static triage

Package `com.universal.remote.ms`, version 5.01.011 (code 50010011), min SDK 16,
target SDK 30. Only static analysis was performed: the APK was never installed
or executed. The file itself is kept out of the repository (see `.gitignore`).

## Integrity

- ZIP structure valid, 1693 entries; v1, v2 and v3 signatures present.
- Signer certificate subject: "Android" / Google Inc. (store signing key, 2018-2048).
  Its fingerprint should be compared with a copy obtained from the official store
  before the APK is trusted for anything beyond reading.

## Findings

- Permissions are consistent with a TV remote: network/Wi-Fi state, location
  (Wi-Fi scanning), microphone (voice remote), storage, push.
  No SMS-sending, accessibility-service or device-admin declarations.
- Third-party SDKs account for the dynamic code loading and push components
  (Alibaba/Agoo, Xiaomi, Firebase, Microsoft/Twitter sign-in, Paho MQTT).
- Vendor endpoints are `*.vidaahub.com` and `hismarttv.com`.
- Native libraries: DLNA (`libmbldlna`), RenderScript, `libtnet`, `libcocklogic`.
  There is no `libmqttcrypt`, so this build belongs to the older (static
  credentials) generation, which matches the target TV.
- Bundled keystores: `res/raw/remoteclientmobile.p12` (client certificate) and
  `res/raw/remoteca.bks` (trust store).

## Protocol facts learned

- Four services exist under `/remoteapp/tv/`: `remote_service`, `ui_service`,
  `platform_service` and **`avs_service`** (not yet documented; probably audio/voice).
- Subscriptions used by the app: `/remoteapp/mobile/` and
  `/remoteapp/mobile/broadcast/#`.
- The app contains screens for picture settings, backlight, calibration, screenshot,
  EPG, PVR reminders, auto wake-up, DLNA photo/video/music push and a hotel mode:
  candidate features for the library.

## Next steps

1. Decompile the DEX files and extract the full action/topic list per service.
2. Document the payload of each action.
3. Identify the DLNA control surface (UPnP) as a second channel.

## Power and standby handling in the app

- Wake-up: UDP packet `FF*6 + MAC*16 + 00*6` to the last known IP, port 33129,
  5 repeats at 100 ms, for the Wi-Fi MAC and for the Ethernet MAC when both are
  known. The app stores `macWifi`, `macEthernet` and a `network_wakeup` flag per TV.
- After sending, the app polls for the device every 5 s (up to ~50 s) before giving up.
- An automatic wake-up setting exists (`is_need_wake_on_wifi`): when the phone joins
  the home network the app tries to wake the last connected TV.
- `broadcast/platform_service/actions/tvsleep` makes the app drop the TV
  connection. `capability.fake_sleep` / `fake_sleep_state` and the states
  `fake_sleep_0` / `fake_sleep_1` describe a screen-off mode with the network alive;
  the target TV did not use it when powered off with `KEY_POWER`.
- Power keys in the remote UI: `KEY_POWER`, `KEY_SAVEPOWERS`, `KEY_SLEEPS`.
