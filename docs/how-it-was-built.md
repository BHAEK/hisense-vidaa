# How it was built

A transparent account of where the knowledge in this project comes from, what each source
contributed, and which parts were done by whom. Nothing here is a requirement for using the
integration; it is here so that you can judge how far to trust it, and reproduce the work for
another TV.

## The problem

A VIDAA TV can be controlled by the vendor's phone app over a local MQTT broker built into the
TV. There is no public documentation of that protocol, it varies between firmware generations,
and older TVs behave differently from newer ones. The goal was an integration that exposes
**everything the firmware allows**, is built as a clean, layered library, and does not depend
on guesses.

## Method

### 1. Start from what the community knew

Three kinds of existing work were read and compared before writing anything:

| Source | What it gave | How it was used |
| --- | --- | --- |
| **Hisense Laser TV integration** ([theappartment/hisense-laser-tv-ha](https://github.com/theappartment/hisense-laser-tv-ha), MIT), in the modified form the author ran at home | A working client for the author's TV: the topic layout, static credentials, the pairing exchange, the wake-up packets, the apps and source actions, and what already worked or failed in daily use | Read as a behavioural reference and a source of leads to verify; not copied |
| **pyvidaa protocol analysis** ([warrenrees/myhisense-tv](https://github.com/warrenrees/myhisense-tv), MIT) | A map of the services and topics, the pairing flow, the three authentication generations and the algorithm of the dynamic credentials | Used to orient the work; the dynamic credential generator was implemented from the documented algorithm and is checked only against the example vector it publishes (it has **not** been run against a TV) |
| **hisense_vidaa for Home Assistant** ([stevene1919/hisense_vidaa](https://github.com/stevene1919/hisense_vidaa), MIT) and the earlier work it credits ([sehaas/ha_hisense_tv](https://github.com/sehaas/ha_hisense_tv), [newAM/hisensetv](https://github.com/newAM/hisensetv)) | Notes on firmware profiles (legacy static credentials, RemoteNOW generation, modern dynamic credentials) | Consulted to understand which firmware needs what |

### 2. Read the vendor app (static analysis)

The Android remote-control app was obtained, checked (integrity, signature, permissions,
declared components, embedded endpoints), and then **decompiled for reading only; it was never
installed or run**. From it came the facts that no other source offered:

- the complete list of actions per service and the shape of their payloads;
- the key table (more than 180 key names) and which ones the app really uses;
- how the app handles power, standby, fake standby, wake-up, volume types and mute;
- that the PIN is sent as a *string* (which later explained a real bug, see below).

Only interoperability facts were taken. No vendor source code, resources or certificates are
included in this repository, and the decompiled output is kept out of version control.

### 3. Probe a real TV

A diagnostic tool (`tools/probe.py`) pairs with a TV and records, untouched, how it answers
each query. This separated what the app *can* send from what the reference TV *actually
answers*. Examples: several actions get no reply on this firmware (picture settings,
screenshots, guide data), state is delivered by pushes rather than replies, and the TV leaves
the network completely a few seconds after the power key.

### 4. Field-test every feature

Each behaviour was exercised on the physical TV, and later inside a real Home Assistant, with a
written checklist (see the [roadmap](../ROADMAP.md)). Several findings changed the design:

- **Power:** the TV does not report a "fake standby", so the power key is a full standby;
  network wake-up works, and was measured after two and five minutes of standby.
- **Volume:** the audio output type identifies ARC (step only) versus the TV speakers (exact
  level); mute produces no message at all, so it is an assumed state.
- **PIN:** a PIN starting with zero was rejected when sent as a number. The vendor app sends a
  string; the library now does the same.
- **Reconnection:** every kind of interruption (power key, unplugged, Home Assistant restart,
  TV off during a restart) was reproduced, and the logs reviewed.

### 5. Learn from other Home Assistant integrations

The integrations for LG webOS, Sony Bravia, Samsung, Roku, Philips TV, Apple TV, Vizio and
Android TV Remote were read to decide which entities a good TV integration offers and how it
should behave (translated errors, diagnostics, re-authentication and reconfigure flows,
media browsing, stable identifiers). Where this project does better or differently, notably
push-based state and a built-in wake-up, it is because the TV allows it.

## Who did what

The project was developed as a pair-programming effort between the author and an AI assistant,
**Claude Sonnet** (Anthropic), used through Claude Code.

- **The author** defined the goals and the quality bar, supplied and operated the reference TV
  and the Home Assistant instance, took every decision (scope, naming, what to publish and
  when), ran or observed every test on the hardware and confirmed what worked.
- **The assistant** studied the existing projects and the decompiled app, designed and wrote the
  library, the Home Assistant adapter, the tests and the documentation, wrote the probes,
  prepared and guided each field test, and analysed the results. A second assistant instance
  running next to Home Assistant provided read-only views of the real installation (logs,
  states, registries) and, with the author's approval, restored the configuration after tests.

Because AI-written code deserves scrutiny, the behaviour that matters is recorded in
[`compatibility.md`](compatibility.md) as *verified on hardware* or *not tested*, and the whole
history is in the git log. Reports of anything that does not work on your TV are very welcome.

## What was deliberately not done

- No vendor code, assets, certificates or keys are redistributed.
- No code was copied from the projects above; behaviour was re-implemented and re-verified.
- Nothing that the reference TV does not do is claimed: unsupported features are documented as
  unsupported, and untested paths are labelled as such.

## Reproducing this for another TV

1. Run `python tools/probe.py HOST` against the TV and keep the capture (redact addresses and
   identifiers).
2. Compare the answers with [`reverse-engineering/protocol-notes.md`](reverse-engineering/protocol-notes.md).
3. Open a *New TV or firmware report* issue with the differences.
