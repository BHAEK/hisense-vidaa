"""Wake a sleeping TV over the network.

Two equivalent packets are known to work; both are sent to every broadcast
address given, several times, as the vendor app does.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time

WOL_PORTS = (9, 7)
VIDAA_PORT = 33129
DEFAULT_REPEAT = 5
DEFAULT_DELAY = 0.1


def parse_mac(mac: str) -> bytes:
    digits = re.sub(r"[^0-9A-Fa-f]", "", mac)
    if len(digits) != 12:
        raise ValueError(f"MAC address must have 12 hex digits: {mac!r}")
    return bytes.fromhex(digits)


def magic_packet(mac: str) -> bytes:
    """Standard Wake-on-LAN packet."""
    return b"\xff" * 6 + parse_mac(mac) * 16


def vidaa_packet(mac: str) -> bytes:
    """VIDAA variant: the standard packet followed by six zero bytes."""
    return magic_packet(mac) + b"\x00" * 6


def broadcast_addresses(host: str | None = None, prefix: int = 24) -> tuple[str, ...]:
    """Limited broadcast plus, when ``host`` is an IPv4 address, its subnet broadcast."""
    addresses = ["255.255.255.255"]
    if host:
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None
        if isinstance(ip, ipaddress.IPv4Address):
            network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
            addresses.append(str(network.broadcast_address))
    return tuple(addresses)


def _send_blocking(mac: str, addresses: tuple[str, ...], repeat: int, delay: float) -> None:
    magic = magic_packet(mac)
    vidaa = vidaa_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(repeat):
            for address in addresses:
                for port in WOL_PORTS:
                    sock.sendto(magic, (address, port))
                sock.sendto(vidaa, (address, VIDAA_PORT))
            time.sleep(delay)


async def send_wake(
    mac: str,
    addresses: tuple[str, ...] = ("255.255.255.255",),
    *,
    repeat: int = DEFAULT_REPEAT,
    delay: float = DEFAULT_DELAY,
) -> None:
    """Send the wake packets without blocking the event loop."""
    await asyncio.to_thread(_send_blocking, mac, addresses, repeat, delay)
