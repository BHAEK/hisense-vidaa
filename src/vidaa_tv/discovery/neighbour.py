"""Find a device's MAC address in the local neighbour (ARP) table.

The TV does not report its own MAC over MQTT, but once it has been talked to, the
host running the client has it in its ARP table (same subnet required).
"""

from __future__ import annotations

import asyncio
import re
import subprocess
from pathlib import Path

_MAC = re.compile(r"(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}", re.IGNORECASE)
_PROC_NET_ARP = Path("/proc/net/arp")
_EMPTY = "00:00:00:00:00:00"


def _normalise(mac: str) -> str:
    return mac.replace("-", ":").upper()


def parse_proc_net_arp(text: str, host: str) -> str | None:
    """Parse the Linux ``/proc/net/arp`` table."""
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 4 and fields[0] == host and fields[3] != _EMPTY:
            return _normalise(fields[3])
    return None


def parse_arp_output(text: str, host: str) -> str | None:
    """Parse the output of ``arp -a <host>`` (Windows, macOS, BSD)."""
    for line in text.splitlines():
        if host in line.split() or f"({host})" in line:
            match = _MAC.search(line)
            if match and _normalise(match.group()) != _EMPTY:
                return _normalise(match.group())
    return None


def _run_arp(host: str) -> str:
    result = subprocess.run(
        ["arp", "-a", host],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    return result.stdout


async def lookup_mac(host: str) -> str | None:
    """Return the MAC of ``host`` if it is in the neighbour table, else ``None``."""
    try:
        text = await asyncio.to_thread(_PROC_NET_ARP.read_text)
    except OSError:
        pass
    else:
        return parse_proc_net_arp(text, host)
    try:
        return parse_arp_output(await asyncio.to_thread(_run_arp, host), host)
    except (OSError, subprocess.SubprocessError):
        return None
