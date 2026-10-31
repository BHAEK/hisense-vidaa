# Reverse engineering notes

Findings are recorded here as they are verified against real hardware.
Each finding should state: what was observed, how, and on which firmware.

Raw captures and decompiled APK sources are never committed (see `.gitignore`).

## Sources

- Community protocol knowledge (pyvidaa, existing Home Assistant integrations).
- Static analysis of the vendor remote-control app.
- Live traffic analysis against the target TV.
