"""Media player entity: the TV as a whole."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaClass,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from vidaa_tv import PowerState, RemoteKey

from . import VidaaConfigEntry
from .const import DOMAIN, TURN_ON_WAIT_SECONDS
from .entity import VidaaEntity, command

_BASE_FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.BROWSE_MEDIA
)

_ROOT = "root"
_CHANNELS = "channels"
_APPS = "apps"


async def async_setup_entry(
    hass: HomeAssistant, entry: VidaaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([VidaaMediaPlayer(entry)])


class VidaaMediaPlayer(VidaaEntity, MediaPlayerEntity):
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV

    def __init__(self, entry: VidaaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = entry.entry_id

    # -- state ---------------------------------------------------------------
    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = _BASE_FEATURES
        volume = self._client.snapshot.volume
        # Absolute volume is ignored by the TV when audio goes to an ARC device.
        if volume is not None and not volume.is_arc:
            features |= MediaPlayerEntityFeature.VOLUME_SET
        return features

    @property
    def state(self) -> MediaPlayerState | None:
        power = self._client.snapshot.power
        if power is PowerState.ON:
            return MediaPlayerState.ON
        if power is PowerState.UNKNOWN:
            return None
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        volume = self._client.snapshot.volume
        return None if volume is None else volume.level / 100

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
    def media_content_type(self) -> MediaType | None:
        state = self._client.snapshot.state
        if state is None:
            return None
        if state.kind == "livetv":
            return MediaType.CHANNEL
        if state.kind == "app":
            return MediaType.APP
        return None

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

    @property
    def media_duration(self) -> int | None:
        state = self._client.snapshot.state
        return state.programme.duration if state and state.programme else None

    @property
    def media_position(self) -> int | None:
        state = self._client.snapshot.state
        if state is None or state.programme is None:
            return None
        return state.programme.position(dt_util.utcnow().timestamp())

    @property
    def media_position_updated_at(self) -> datetime | None:
        return dt_util.utcnow() if self.media_position is not None else None

    # -- commands ------------------------------------------------------------
    @command
    async def async_turn_on(self) -> None:
        if not await self._client.turn_on(wait=TURN_ON_WAIT_SECONDS):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="turn_on_timeout",
                translation_placeholders={"name": self._title},
            )

    @command
    async def async_turn_off(self) -> None:
        await self._client.turn_off()

    @command
    async def async_volume_up(self) -> None:
        await self._client.volume.step(1)

    @command
    async def async_volume_down(self) -> None:
        await self._client.volume.step(-1)

    @command
    async def async_set_volume_level(self, volume: float) -> None:
        await self._client.volume.set_level(round(volume * 100))

    @command
    async def async_mute_volume(self, mute: bool) -> None:
        # The TV only toggles mute and does not report it, so a request is a toggle.
        await self._client.volume.mute_toggle()

    @command
    async def async_media_play(self) -> None:
        await self._client.remote.press(RemoteKey.PLAY)

    @command
    async def async_media_pause(self) -> None:
        await self._client.remote.press(RemoteKey.PAUSE)

    @command
    async def async_media_stop(self) -> None:
        await self._client.remote.press(RemoteKey.STOP)

    @command
    async def async_media_next_track(self) -> None:
        await self._client.remote.press(RemoteKey.CHANNEL_UP)

    @command
    async def async_media_previous_track(self) -> None:
        await self._client.remote.press(RemoteKey.CHANNEL_DOWN)

    @command
    async def async_select_source(self, source: str) -> None:
        if any(item.name == source for item in self._catalog.sources):
            await self._client.sources.select(source)
        else:
            await self._client.apps.launch(source)

    @command
    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        """Tune a live channel (number or name) or launch an app (name)."""
        if media_type == MediaType.CHANNEL:
            match = next(
                (
                    channel
                    for channel in self._catalog.channels
                    if media_id == channel.number or media_id.casefold() == channel.name.casefold()
                ),
                None,
            )
            if match is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="unknown_channel",
                    translation_placeholders={"channel": media_id},
                )
            await self._client.channels.tune(match)
        elif media_type == MediaType.APP:
            await self._client.apps.launch(media_id)
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unsupported_media_type",
                translation_placeholders={"media_type": str(media_type)},
            )

    # -- browsing ------------------------------------------------------------
    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        if media_content_id == _CHANNELS:
            return self._folder(
                _CHANNELS,
                "Channels",
                [
                    BrowseMedia(
                        media_class=MediaClass.CHANNEL,
                        media_content_id=channel.number,
                        media_content_type=MediaType.CHANNEL,
                        title=f"{channel.number} {channel.name}",
                        can_play=True,
                        can_expand=False,
                    )
                    for channel in self._catalog.channels
                ],
            )
        if media_content_id == _APPS:
            return self._folder(
                _APPS,
                "Apps",
                [
                    BrowseMedia(
                        media_class=MediaClass.APP,
                        media_content_id=app.name,
                        media_content_type=MediaType.APP,
                        title=app.name,
                        can_play=True,
                        can_expand=False,
                    )
                    for app in self._catalog.apps
                ],
            )
        return self._folder(
            _ROOT,
            self._title,
            [
                self._folder(_CHANNELS, "Channels", None),
                self._folder(_APPS, "Apps", None),
            ],
        )

    @staticmethod
    def _folder(content_id: str, title: str, children: list[BrowseMedia] | None) -> BrowseMedia:
        return BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id=content_id,
            media_content_type=content_id,
            title=title,
            can_play=False,
            can_expand=True,
            children=children,
        )
