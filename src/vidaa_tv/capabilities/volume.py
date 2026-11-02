"""Volume control.

Absolute volume is ignored by the firmware when audio goes through ARC, so
changes are made by stepping with the remote keys and re-reading the level.
"""

from __future__ import annotations

import asyncio

from vidaa_tv.capabilities.remote import RemoteControl
from vidaa_tv.keys import RemoteKey
from vidaa_tv.models import Volume
from vidaa_tv.protocol import parsers
from vidaa_tv.protocol.topics import Action
from vidaa_tv.session import Session

MAX_STEPS = 50


class VolumeControl:
    def __init__(self, session: Session, remote: RemoteControl, *, step_delay: float = 0.2) -> None:
        self._session = session
        self._remote = remote
        self._step_delay = step_delay

    async def get(self) -> Volume:
        reply = await self._session.request(Action.GET_VOLUME, parsers.is_volume)
        return parsers.parse_volume(reply.payload)

    async def step(self, steps: int) -> None:
        """Press volume up (positive) or down (negative) ``abs(steps)`` times."""
        key = RemoteKey.VOLUME_UP if steps > 0 else RemoteKey.VOLUME_DOWN
        for _ in range(min(abs(steps), MAX_STEPS)):
            await self._remote.press(key)
            await asyncio.sleep(self._step_delay)

    async def mute_toggle(self) -> None:
        """Toggle mute. The state cannot be read back reliably, so it is not returned."""
        await self._remote.press(RemoteKey.MUTE)

    async def set_level(self, target: int) -> Volume:
        """Move to ``target`` (0-100); the result may differ by one step with ARC."""
        current = await self.get()
        if current.is_arc:
            await self.step(target - current.level)
        else:
            await self._session.send(Action.CHANGE_VOLUME, str(max(0, min(100, target))))
        return await self.get()
