"""An unknown client identity starts re-authentication; diagnostics hide identifiers."""

from __future__ import annotations

from custom_components.hisense_vidaa.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir  # noqa: F401
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from .conftest import DEVICE_ID, HOST
from .fake_tv import TV_ID, FakeTv
from .test_setup import setup


async def test_an_unrecognised_identity_asks_to_pair_again(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    tv.paired_ids.clear()
    await setup(hass, entry)
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [f["context"]["source"] for f in flows] == ["reauth"]


async def test_diagnostics_do_not_leak_identifiers(
    hass: HomeAssistant, hass_client, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    data = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    text = str(data)
    for secret in (HOST, DEVICE_ID, TV_ID, "AA:BB:CC:DD:EE:FF"):
        assert secret not in text
    assert data["connected"] is True
    assert data["snapshot"]["power"] == "on"
    assert data["catalog"]["channels"] == 2
