"""Buttons: the most useful remote keys, one tap on a dashboard."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from vidaa_tv import RemoteKey

from . import VidaaConfigEntry
from .entity import VidaaEntity


@dataclass(frozen=True, kw_only=True)
class VidaaButtonDescription(ButtonEntityDescription):
    remote_key: RemoteKey


def _button(key: RemoteKey, icon: str, *, default: bool = True) -> VidaaButtonDescription:
    return VidaaButtonDescription(
        key=key.name.lower(),
        translation_key=key.name.lower(),
        icon=icon,
        remote_key=key,
        entity_registry_enabled_default=default,
    )


BUTTONS: tuple[VidaaButtonDescription, ...] = (
    _button(RemoteKey.HOME, "mdi:home"),
    _button(RemoteKey.MENU, "mdi:menu"),
    _button(RemoteKey.BACK, "mdi:arrow-left"),
    _button(RemoteKey.EXIT, "mdi:exit-to-app"),
    _button(RemoteKey.EPG, "mdi:television-guide"),
    _button(RemoteKey.SUBTITLE, "mdi:subtitles"),
    _button(RemoteKey.SOURCES, "mdi:video-input-hdmi"),
    _button(RemoteKey.MUTE, "mdi:volume-mute"),
    _button(RemoteKey.CHANNEL_UP, "mdi:chevron-up"),
    _button(RemoteKey.CHANNEL_DOWN, "mdi:chevron-down"),
    _button(RemoteKey.UP, "mdi:arrow-up-bold"),
    _button(RemoteKey.DOWN, "mdi:arrow-down-bold"),
    _button(RemoteKey.LEFT, "mdi:arrow-left-bold"),
    _button(RemoteKey.RIGHT, "mdi:arrow-right-bold"),
    _button(RemoteKey.OK, "mdi:checkbox-blank-circle-outline"),
    _button(RemoteKey.PLAY, "mdi:play", default=False),
    _button(RemoteKey.PAUSE, "mdi:pause", default=False),
    _button(RemoteKey.STOP, "mdi:stop", default=False),
    _button(RemoteKey.REWIND, "mdi:rewind", default=False),
    _button(RemoteKey.FAST_FORWARD, "mdi:fast-forward", default=False),
    _button(RemoteKey.RED, "mdi:circle", default=False),
    _button(RemoteKey.GREEN, "mdi:circle", default=False),
    _button(RemoteKey.YELLOW, "mdi:circle", default=False),
    _button(RemoteKey.BLUE, "mdi:circle", default=False),
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

    async def async_press(self) -> None:
        await self._client.remote.press(self.entity_description.remote_key)
