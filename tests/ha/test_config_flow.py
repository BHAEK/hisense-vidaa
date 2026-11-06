"""The configuration flows: first setup, re-pairing and a moved TV."""

from __future__ import annotations

from custom_components.hisense_vidaa.const import CONF_DEVICE_ID, CONF_MAC, DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import DEVICE_ID, HOST
from .fake_tv import PIN, TV_ID, FakeTv


async def start_user_flow(hass: HomeAssistant, host: str = HOST) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: host, CONF_MAC: "AA:BB:CC:DD:EE:FF"}
    )


async def test_first_setup_pairs_with_the_pin_and_uses_the_tv_identity(
    hass: HomeAssistant, tv: FakeTv
) -> None:
    tv.paired_ids.clear()
    result = await start_user_flow(hass)
    assert result["step_id"] == "pin"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pin": PIN})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hisense TV"
    assert result["result"].unique_id == TV_ID
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_MAC] == "AA:BB:CC:DD:EE:FF"
    assert result["data"][CONF_DEVICE_ID] in tv.paired_ids


async def test_a_wrong_pin_can_be_retried(hass: HomeAssistant, tv: FakeTv) -> None:
    tv.paired_ids.clear()
    result = await start_user_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pin": "0000"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_pin"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pin": PIN})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_an_unreachable_tv_is_reported(hass: HomeAssistant, tv: FakeTv) -> None:
    tv.online = False
    result = await start_user_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_adding_the_same_tv_again_updates_its_address(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    entry.add_to_hass(hass)
    tv.paired_ids.clear()
    result = await start_user_flow(hass, host="192.0.2.99")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pin": PIN})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "192.0.2.99"


async def test_reauth_pairs_a_new_identity(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    entry.add_to_hass(hass)
    tv.paired_ids.clear()
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["step_id"] == "pin"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pin": PIN})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_DEVICE_ID] != DEVICE_ID
    assert entry.data[CONF_DEVICE_ID] in tv.paired_ids


async def test_reauth_refuses_a_different_tv(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv, monkeypatch
) -> None:
    entry.add_to_hass(hass)
    tv.paired_ids.clear()
    other = MockConfigEntry(domain=DOMAIN, unique_id="another-tv", data=dict(entry.data))
    other.add_to_hass(hass)
    result = await other.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pin": PIN})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"


async def test_reconfigure_changes_the_address(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.0.2.50", CONF_MAC: ""}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.0.2.50"
    assert entry.data[CONF_MAC] == "AA:BB:CC:DD:EE:FF"  # kept when the field is left empty


async def test_reconfigure_needs_a_paired_identity(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    entry.add_to_hass(hass)
    tv.paired_ids.clear()
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.0.2.50", CONF_MAC: ""}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_paired"}
