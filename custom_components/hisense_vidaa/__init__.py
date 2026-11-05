"""Home Assistant integration for Hisense VIDAA TVs.

This package is a thin adapter: all TV logic lives in the ``vidaa_tv`` library.
"""

from __future__ import annotations

import logging
from collections.abc import Coroutine
from typing import Any

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .catalog import VidaaCatalog
from .const import CONF_DEVICE_ID, CONF_MAC, DOMAIN
from .runtime import VidaaConfigEntry, VidaaData
from .vidaa_tv import PowerState, VidaaClient, mqtt_transport_factory
from .vidaa_tv.tracker import Snapshot

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: VidaaConfigEntry) -> bool:
    def spawn(name: str, coroutine: Coroutine[Any, Any, Any]) -> None:
        entry.async_create_background_task(hass, coroutine, f"{DOMAIN} {name}")

    client = VidaaClient(
        entry.data[CONF_HOST],
        entry.data[CONF_DEVICE_ID],
        mac=entry.data.get(CONF_MAC),
        transport_factory=mqtt_transport_factory(),
        task_factory=lambda coroutine: entry.async_create_background_task(
            hass, coroutine, f"{DOMAIN} connection"
        ),
    )
    catalog = VidaaCatalog(client)
    entry.runtime_data = VidaaData(client, catalog)

    resolving_mac = False
    published_identity: tuple[Any, ...] | None = None

    async def resolve_mac() -> None:
        """Learn the TV's MAC from the ARP table once and remember it."""
        nonlocal resolving_mac
        try:
            mac = await client.resolve_mac()
            if mac and mac != entry.data.get(CONF_MAC):
                hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_MAC: mac})
        finally:
            resolving_mac = False

    def update_device(snapshot: Snapshot) -> None:
        """Publish model, firmware and MAC to the device registry when they change."""
        nonlocal published_identity
        info = snapshot.info
        if info is None:
            return
        identity = (info, client.mac)
        if identity == published_identity:
            return
        published_identity = identity
        connections = (
            {(dr.CONNECTION_NETWORK_MAC, dr.format_mac(client.mac))} if client.mac else set()
        )
        dr.async_get(hass).async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            connections=connections,
            manufacturer="Hisense",
            model=info.model_code or info.board or "VIDAA",
            sw_version=info.software_version,
            hw_version=info.board or None,
            serial_number=info.device_id or None,
        )

    def on_snapshot(snapshot: Snapshot) -> None:
        nonlocal resolving_mac
        if snapshot.power is PowerState.ON and not catalog.loaded:
            spawn("catalog", catalog.refresh())
        elif snapshot.power in (PowerState.OFF, PowerState.STANDBY):
            catalog.reset()
        if snapshot.power is PowerState.ON and client.mac is None and not resolving_mac:
            resolving_mac = True
            spawn("mac lookup", resolve_mac())
        update_device(snapshot)

    entry.async_on_unload(client.add_listener(on_snapshot))
    await client.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VidaaConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.stop()
    return unloaded
