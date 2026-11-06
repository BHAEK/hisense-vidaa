"""Setting the integration up, and what happens when the TV goes away and returns."""

from __future__ import annotations

import asyncio

from custom_components.hisense_vidaa.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .fake_tv import LIVE_STATE, TV_ID, FakeTv


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for _ in range(10):  # the supervisor and the catalog load in the background
        await asyncio.sleep(0)
    await hass.async_block_till_done()


async def test_setup_creates_the_entities_and_the_device(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    registry = er.async_get(hass)
    platforms = {e.domain for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert platforms == {"media_player", "remote", "sensor", "select", "button", "binary_sensor"}
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, entry.entry_id), entry.entry_id
    )
    assert device is not None
    assert device.model == "65A_TEST"
    assert device.sw_version == "V0001.01.00a.P0219"
    assert device.serial_number == TV_ID
    assert (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff") in device.connections


async def test_media_player_reports_the_tv_state(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    state = hass.states.get("media_player.hisense_tv")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["source"] == "HDMI2"
    assert state.attributes["volume_level"] == 0.12
    assert state.attributes["source_list"] == ["TV", "HDMI1", "HDMI2", "Netflix", "YouTube"]
    await tv.push_state(LIVE_STATE)
    await hass.async_block_till_done()
    state = hass.states.get("media_player.hisense_tv")
    assert state is not None
    assert state.attributes["media_title"] == "News"
    assert state.attributes["media_channel"] == "Rai 1"
    assert state.attributes["media_duration"] == 600


async def test_the_tv_going_off_and_coming_back(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    runtime = entry.runtime_data
    tv.drop()
    await hass.async_block_till_done()
    for _ in range(10):
        await asyncio.sleep(0)
    assert hass.states.get("media_player.hisense_tv").state == "off"  # type: ignore[union-attr]
    assert hass.states.get("binary_sensor.hisense_tv_connection").state == "off"  # type: ignore[union-attr]
    tv.online = True
    runtime.client._supervisor.nudge()
    assert await runtime.client.wait_connected(2)
    await hass.async_block_till_done()
    assert hass.states.get("media_player.hisense_tv").state == "on"  # type: ignore[union-attr]


async def test_unload_stops_the_client(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not tv.connected
