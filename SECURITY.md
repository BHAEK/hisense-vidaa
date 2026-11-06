# Security policy

## Supported versions

Only the latest release receives fixes while the project is below `1.0`.

## Reporting a vulnerability

Please do **not** open a public issue. Use GitHub's private vulnerability reporting
(*Security* tab → *Report a vulnerability*) and include the version, the TV model and
firmware, and the steps to reproduce.

## Scope and privacy

The integration talks to a TV on the local network only. Credentials are limited to the
paired client identity stored in the Home Assistant config entry. Logs, diagnostics and
captures you attach to a report can contain the TV's address, MAC address and device id:
redact them first. The diagnostics download already hides them.
