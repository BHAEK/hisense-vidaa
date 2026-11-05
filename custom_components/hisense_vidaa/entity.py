"""Base entity shared by every platform, and the command error wrapper."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .runtime import VidaaConfigEntry
from .vidaa_tv import PowerState
from .vidaa_tv.errors import VidaaError
from .vidaa_tv.tracker import Snapshot

_EntityT = TypeVar("_EntityT", bound="VidaaEntity")
_P = ParamSpec("_P")
_R = TypeVar("_R")

# Commands that make sense (or must be tried) while the TV looks off.
_ALLOWED_WHEN_OFF = {"async_turn_on", "async_turn_off"}


def command(
    func: Callable[Concatenate[_EntityT, _P], Awaitable[_R]],
) -> Callable[Concatenate[_EntityT, _P], Awaitable[_R]]:
    """Turn library errors into translated Home Assistant errors."""

    @wraps(func)
    async def wrapper(self: _EntityT, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        placeholders = {"name": self._title, "func": func.__name__}
        if (
            func.__name__ not in _ALLOWED_WHEN_OFF
            and self._client.snapshot.power is not PowerState.ON
        ):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_off",
                translation_placeholders=placeholders,
            )
        try:
            return await func(self, *args, **kwargs)
        except VidaaError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={**placeholders, "error": str(error)},
            ) from error

    return wrapper


class VidaaEntity(Entity):
    """Re-renders itself whenever the TV pushes a change."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: VidaaConfigEntry) -> None:
        self._client = entry.runtime_data.client
        self._catalog = entry.runtime_data.catalog
        self._title = entry.title
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Hisense",
            model="VIDAA",
            name=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._client.add_listener(self._handle_snapshot))
        self.async_on_remove(self._catalog.add_listener(self.async_write_ha_state))

    def _handle_snapshot(self, snapshot: Snapshot) -> None:
        """Called when the TV pushed a change; subclasses may refresh cached values first."""
        self.async_write_ha_state()
