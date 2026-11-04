"""Home Assistant integration for Hisense VIDAA TVs.

This package is a thin adapter: all TV logic lives in the ``vidaa_tv`` library.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from vidaa_tv import PowerState, VidaaClient, mqtt_transport_factory
from vidaa_tv.tracker import Snapshot

from .catalog import VidaaCatalog
from .const import CONF_DEVICE_ID, CONF_MAC, DOMAIN

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
]


@dataclass
class VidaaData:
    client: VidaaClient
    catalog: VidaaCatalog


VidaaConfigEntry = ConfigEntry[VidaaData]


async def async_setup_entry(hass: HomeAssistant, entry: VidaaConfigEntry) -> bool:
    client = VidaaClient(
        entry.data[CONF_HOST],
        entry.data[CONF_DEVICE_ID],
        mac=entry.data.get(CONF_MAC),
        transport_factory=mqtt_transport_factory(),
    )
    catalog = VidaaCatalog(client)
    entry.runtime_data = VidaaData(client, catalog)

    def on_snapshot(snapshot: Snapshot) -> None:
        if snapshot.power is PowerState.ON and not catalog.loaded:
            hass.async_create_task(catalog.refresh())
        elif snapshot.power in (PowerState.OFF, PowerState.STANDBY):
            catalog.reset()
        if snapshot.info is not None:
            dr.async_get(hass).async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, entry.entry_id)},
                manufacturer="Hisense",
                model=snapshot.info.model_code or snapshot.info.board or "VIDAA",
                sw_version=snapshot.info.software_version,
            )

    entry.async_on_unload(client.add_listener(on_snapshot))
    await client.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VidaaConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.stop()
    return unloaded
