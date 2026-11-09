# Compatibility and verification status

What has been exercised on real hardware, and what has not. Everything below the first
table is **untested** and is offered as is: if it works for you, great; if it does not,
please open a *New TV or firmware report* issue and attach the probe output.

## Verified (reference TV)

Hisense model `H65B7320`, software `V0001.01.00a.P0219`, board MSD6886 (2018 generation),
connected over Wi-Fi, audio on an ARC soundbar or on the TV speakers; Home Assistant
2026.10 / 2026.11.

| Area | Verified |
| --- | --- |
| Pairing | PIN pairing with a new client identity (library, probe) |
| State | Source, live channel, programme, running app, volume (pushed by the TV) |
| Keys | Navigation, volume, mute (toggle), guide, menu, subtitles; navigation forwarded to HDMI-CEC devices |
| Sources / apps / channels | Listing and switching; launching apps (including web apps); tuning by number and name |
| Power | Off with the power key; on with the network wake-up packets (also after 5 minutes of standby) |
| Home Assistant | Setup, entities, services, media browser, diagnostics, reconnection after the TV is switched off, unplugged, or Home Assistant restarts, reconfigure flow |

## Not tested

| Area | Notes |
| --- | --- |
| **Dynamic credentials** (`vidaa_tv.protocol.auth.dynamic_credentials`) | The credential scheme used by newer firmware, implemented from third-party analysis of the vendor app. Never run against a TV. The reference TV uses the static credentials. |
| **Client-certificate TLS** | Newer firmware may require a client certificate. The library accepts one (`TlsConfig`) but the Home Assistant integration does not expose it and it was never exercised. The reference TV accepts a connection without one. |
| Other models and firmware generations | Only one model was available. Features the reference TV does not answer (picture settings, screenshots, programme guide, recordings) are documented as unsupported there and may work elsewhere. |
| TV connected over Ethernet | Wake-up and reconnect behaviour was observed on Wi-Fi only. |
| Wake-up after long standby | Checked at 2 and 5 minutes; longer standby periods were not measured, and network wake-up is known to be less dependable in some standby states. |
| **Re-authentication flow** | Covered by automated tests with a simulated TV; not triggered on a real TV. |
| PIN starting with a zero | Sent as a JSON number it was rejected by the TV (confirmed). It is now sent as a string, like the vendor app does; the string form is covered by automated tests but not yet verified on the TV. |
| Several TVs at once | One TV per integration entry was used; two entries were not tried. |
| Installation from a store | Install and update through HACS or the Home Assistant marketplace are not verified yet. |
| Home Assistant versions other than 2026.10/2026.11 | |
