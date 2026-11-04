"""Base entity shared by every platform."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import VidaaConfigEntry
from .const import DOMAIN


class VidaaEntity(Entity):
    """Re-renders itself whenever the TV pushes a change."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: VidaaConfigEntry) -> None:
        self._client = entry.runtime_data.client
        self._catalog = entry.runtime_data.catalog
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Hisense",
            model="VIDAA",
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._client.add_listener(lambda _snapshot: self.async_write_ha_state())
        )
        self.async_on_remove(self._catalog.add_listener(self.async_write_ha_state))
