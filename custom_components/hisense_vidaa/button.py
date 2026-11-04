"""Buttons: the most useful remote keys, one tap on a dashboard."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from vidaa_tv import RemoteKey

from . import VidaaConfigEntry
from .entity import VidaaEntity, command


@dataclass(frozen=True, kw_only=True)
class VidaaButtonDescription(ButtonEntityDescription):
    remote_key: RemoteKey


def _button(key: RemoteKey, *, default: bool = True) -> VidaaButtonDescription:
    return VidaaButtonDescription(
        key=key.name.lower(),
        translation_key=key.name.lower(),
        remote_key=key,
        entity_registry_enabled_default=default,
    )


BUTTONS: tuple[VidaaButtonDescription, ...] = (
    _button(RemoteKey.HOME),
    _button(RemoteKey.MENU),
    _button(RemoteKey.BACK),
    _button(RemoteKey.EXIT),
    _button(RemoteKey.EPG),
    _button(RemoteKey.SUBTITLE),
    _button(RemoteKey.SOURCES),
    _button(RemoteKey.MUTE),
    _button(RemoteKey.CHANNEL_UP),
    _button(RemoteKey.CHANNEL_DOWN),
    _button(RemoteKey.UP),
    _button(RemoteKey.DOWN),
    _button(RemoteKey.LEFT),
    _button(RemoteKey.RIGHT),
    _button(RemoteKey.OK),
    _button(RemoteKey.PLAY, default=False),
    _button(RemoteKey.PAUSE, default=False),
    _button(RemoteKey.STOP, default=False),
    _button(RemoteKey.REWIND, default=False),
    _button(RemoteKey.FAST_FORWARD, default=False),
    _button(RemoteKey.RED, default=False),
    _button(RemoteKey.GREEN, default=False),
    _button(RemoteKey.YELLOW, default=False),
    _button(RemoteKey.BLUE, default=False),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: VidaaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(VidaaButton(entry, description) for description in BUTTONS)


class VidaaButton(VidaaEntity, ButtonEntity):
    entity_description: VidaaButtonDescription

    def __init__(self, entry: VidaaConfigEntry, description: VidaaButtonDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @command
    async def async_press(self) -> None:
        await self._client.remote.press(self.entity_description.remote_key)
