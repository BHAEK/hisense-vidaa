"""Remote entity: send any key of the TV remote."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import ATTR_DELAY_SECS, ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VidaaConfigEntry
from .const import TURN_ON_WAIT_SECONDS
from .entity import VidaaEntity, command
from .vidaa_tv import PowerState, RemoteKey

_DEFAULT_DELAY = 0.4


async def async_setup_entry(
    hass: HomeAssistant, entry: VidaaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([VidaaRemote(entry)])


def _resolve(command: str) -> str:
    """Accept enum names (``volume_up``), raw names (``KEY_MUTE``) or any other key."""
    try:
        return RemoteKey[command.upper()].value
    except KeyError:
        return command


class VidaaRemote(VidaaEntity, RemoteEntity):
    _attr_name = "Remote"

    def __init__(self, entry: VidaaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_remote"

    @property
    def is_on(self) -> bool:
        return self._client.snapshot.power is PowerState.ON

    @command
    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.turn_on(wait=TURN_ON_WAIT_SECONDS)

    @command
    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.turn_off()

    @command
    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        repeats = kwargs.get(ATTR_NUM_REPEATS, 1)
        delay = kwargs.get(ATTR_DELAY_SECS, _DEFAULT_DELAY)
        for _ in range(repeats):
            for item in command:
                await self._client.remote.press(_resolve(item))
                await asyncio.sleep(delay)
