# Pairing flow

Pairing is **authorisation of a client identity**, not a token exchange.
Observed on the target TV (firmware V0001.01.00a.P0219).

A client identity is `<MAC>$vidaa_common`; the MAC identifies the *client*
(the host running the integration), not the TV.

## Sequence for a new identity  **[confirmed]**

1. Connect over MQTT/TLS with the static credentials and the client id.
2. Subscribe to `/remoteapp/mobile/<client>/#` and `/remoteapp/mobile/broadcast/#`.
3. The TV pushes `broadcast/ui_service/state` and, for an unknown identity,
   `<client>/ui_service/data/authentication` with an empty payload.
4. Publish `gettvstate` and `capability` (empty), then `vidaa_app_connect`
   `{"app_version":2,"connect_result":0,"device_type":"Mobile App"}`
   (all under `/remoteapp/tv/ui_service/<client>/actions/`).
5. The TV shows a PIN. Some identities also trigger `authenticationcodetoast`
   and `authenticationcodeclose` pushes.
6. Publish `authenticationcode` with `{"authNum":"<digits>"}` (a JSON **string**, see below).
7. The reply on `<client>/ui_service/data/authenticationcode` is
   `{"result":1,"info":""}` on success.
8. Optionally publish `authenticationcodeclose` (empty).

No token is issued on this firmware. `tokenissuance` never arrives and the
identity is simply remembered by the TV.

## PIN format  **[confirmed]**

The vendor app builds the payload by concatenating its four digit fields into a string
(`authNum` is a string). Sending the PIN as a JSON **number** works for PINs without a
leading zero but **fails for a PIN such as `0123`** (observed on the reference TV: the PIN
shown on the screen was rejected). The library now sends the string form.

Probe with a deliberately wrong PIN on the reference TV: both `{"authNum":0000}` (number) and
`{"authNum":"0000"}` (string) are parsed and answered with
`{"result":100,"info":"Wrong authNum!!"}`, so the TV accepts both syntaxes. The likely reason
for the failure of a number such as `0123` is that the TV reads it as `123` and compares the
text with the PIN `0123`; the string form delivers the digits unchanged. A normal PIN is
accepted in the string form (`8114`). A genuine PIN with a leading zero has not been
confirmed on the TV with the string form yet. **[open]**

## Reconnecting with a known identity  **[confirmed]**

No PIN is requested. The TV immediately pushes the current state,
`platform_service` volume changes and the capability reply.

## Pairing an already authorised identity  **[confirmed]**

The TV does not issue a new PIN to an identity it already knows. Sending an
authentication code then fails with
`{"result":100,"info":"Wrong authNum!!"}` and the flow cannot finish.

Design consequences:

- Pairing must detect "identity already authorised" (state/capability pushes
  arrive without a PIN prompt) and skip the PIN step.
- A new pairing should use a freshly generated identity rather than reuse a
  previous one.
- Pairing is a first-class, interactive operation of the library (start,
  supply PIN, persist identity), separate from normal use.

## Reply recognition

Replies are not tied to a per-command topic. They are recognised by payload shape
(see `protocol-notes.md`), and the TV also pushes unsolicited updates.
Empty payloads on subscribed topics occur and must be tolerated.
