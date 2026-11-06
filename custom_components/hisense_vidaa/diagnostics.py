"""Diagnostics download, with identifiers redacted."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_MAC
from .runtime import VidaaConfigEntry

TO_REDACT = {CONF_HOST, CONF_MAC, CONF_DEVICE_ID, "device_id", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VidaaConfigEntry
) -> dict[str, Any]:
    data = entry.runtime_data
    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "connected": data.client.connected,
            "snapshot": asdict(data.client.snapshot),
            "catalog": {
                "loaded": data.catalog.loaded,
                "sources": [source.name for source in data.catalog.sources],
                "apps": len(data.catalog.apps),
                "channels": len(data.catalog.channels),
            },
        },
        TO_REDACT,
    )
