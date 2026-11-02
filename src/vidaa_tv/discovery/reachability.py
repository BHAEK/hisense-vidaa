"""Network presence checks.

The TV never answers ICMP echo, so presence is decided by whether its MQTT port
accepts a TCP connection.
"""

from __future__ import annotations

import asyncio
import contextlib
import time

DEFAULT_PORT = 36669


async def is_reachable(host: str, port: int = DEFAULT_PORT, *, timeout: float = 1.0) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    except (OSError, TimeoutError):
        return False
    writer.close()
    with contextlib.suppress(OSError):
        await writer.wait_closed()
    return True


async def wait_until_reachable(
    host: str, port: int = DEFAULT_PORT, *, timeout: float = 60.0, interval: float = 1.0
) -> bool:
    """Poll until the port opens; returns False when ``timeout`` elapses first."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if await is_reachable(host, port, timeout=min(interval, 1.0)):
            return True
        await asyncio.sleep(interval)
    return False
