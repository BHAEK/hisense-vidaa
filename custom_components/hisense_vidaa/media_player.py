"""Media player entity: the TV as a whole."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from vidaa_tv import PowerState, RemoteKey

from . import VidaaConfigEntry
from .const import TURN_ON_WAIT_SECONDS
from .entity import VidaaEntity

_FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.PLAY_MEDIA
)


async def async_setup_entry(
    hass: HomeAssistant, entry: VidaaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([VidaaMediaPlayer(entry)])


class VidaaMediaPlayer(VidaaEntity, MediaPlayerEntity):
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = _FEATURES

    def __init__(self, entry: VidaaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = entry.entry_id

    @property
    def state(self) -> MediaPlayerState | None:
        power = self._client.snapshot.power
        if power is PowerState.ON:
            return MediaPlayerState.ON
        if power is PowerState.UNKNOWN:
            return None
        return MediaPlayerState.OFF

    @property
    def source(self) -> str | None:
        state = self._client.snapshot.state
        if state is None:
            return None
        if state.kind == "livetv":
            return "TV"
        return state.app_name or state.source_name

    @property
    def source_list(self) -> list[str]:
        return [*(s.name for s in self._catalog.sources), *(a.name for a in self._catalog.apps)]

    @property
    def media_title(self) -> str | None:
        state = self._client.snapshot.state
        return state.programme.title if state and state.programme else None

    @property
    def media_channel(self) -> str | None:
        state = self._client.snapshot.state
        return state.channel_name if state else None

    @property
    def app_name(self) -> str | None:
        state = self._client.snapshot.state
        return state.app_name if state else None

    async def async_turn_on(self) -> None:
        await self._client.turn_on(wait=TURN_ON_WAIT_SECONDS)

    async def async_turn_off(self) -> None:
        await self._client.turn_off()

    async def async_volume_up(self) -> None:
        await self._client.volume.step(1)

    async def async_volume_down(self) -> None:
        await self._client.volume.step(-1)

    async def async_mute_volume(self, mute: bool) -> None:
        # The TV only toggles mute and does not report it, so a request is a toggle.
        await self._client.volume.mute_toggle()

    async def async_media_next_track(self) -> None:
        await self._client.remote.press(RemoteKey.CHANNEL_UP)

    async def async_media_previous_track(self) -> None:
        await self._client.remote.press(RemoteKey.CHANNEL_DOWN)

    async def async_select_source(self, source: str) -> None:
        if any(item.name == source for item in self._catalog.sources):
            await self._client.sources.select(source)
        else:
            await self._client.apps.launch(source)

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        """Tune a live channel by number or name."""
        if media_type != MediaType.CHANNEL:
            raise ValueError(f"unsupported media type: {media_type}")
        channel_lists = await self._client.channels.lists()
        if not channel_lists:
            raise ValueError("the TV has no channel list")
        channel = await self._client.channels.find(channel_lists[0], media_id)
        await self._client.channels.tune(channel)
