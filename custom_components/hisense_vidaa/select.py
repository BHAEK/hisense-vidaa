"""Selects: choose an input source or launch an app."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import VidaaEntity, command
from .runtime import VidaaConfigEntry
from .vidaa_tv import PowerState


async def async_setup_entry(
    hass: HomeAssistant, entry: VidaaConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([VidaaSourceSelect(entry), VidaaAppSelect(entry)])


class _VidaaSelect(VidaaEntity, SelectEntity):
    @property
    def available(self) -> bool:
        return self._client.snapshot.power is PowerState.ON and self._catalog.loaded


class VidaaSourceSelect(_VidaaSelect):
    _attr_translation_key = "source"

    def __init__(self, entry: VidaaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_source_select"

    @property
    def options(self) -> list[str]:
        return [source.name for source in self._catalog.sources]

    @property
    def current_option(self) -> str | None:
        state = self._client.snapshot.state
        if state is None or state.kind == "app":
            return None
        if state.kind == "livetv":
            return "TV"
        return state.source_name if state.source_name in self.options else None

    @command
    async def async_select_option(self, option: str) -> None:
        await self._client.sources.select(option)


class VidaaAppSelect(_VidaaSelect):
    _attr_translation_key = "app"

    def __init__(self, entry: VidaaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_app_select"

    @property
    def options(self) -> list[str]:
        return [app.name for app in self._catalog.apps]

    @property
    def current_option(self) -> str | None:
        state = self._client.snapshot.state
        if state is None or state.kind != "app":
            return None
        for app in self._catalog.apps:
            # The TV reports the app lower-cased and sometimes by url.
            if app.url == state.app_url or app.name.casefold() == (state.app_name or "").casefold():
                return app.name
        return None

    @command
    async def async_select_option(self, option: str) -> None:
        await self._client.apps.launch(option)
