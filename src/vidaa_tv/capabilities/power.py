"""Power control.

Turning the TV on is not a session operation (the TV is unreachable while in
standby); see ``vidaa_tv.discovery.wake`` and ``VidaaClient.turn_on``.
"""

from __future__ import annotations

from ..keys import RemoteKey
from .remote import RemoteControl


class PowerControl:
    def __init__(self, remote: RemoteControl) -> None:
        self._remote = remote

    async def turn_off(self) -> None:
        """Put the TV in standby; it leaves the network within seconds."""
        await self._remote.press(RemoteKey.POWER)
