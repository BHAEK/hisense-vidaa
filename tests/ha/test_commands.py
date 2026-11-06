"""Commands sent from Home Assistant reach the TV, and failures read well."""

from __future__ import annotations

import asyncio

import pytest
from custom_components.hisense_vidaa.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .fake_tv import LIVE_STATE, FakeTv
from .test_setup import setup

PLAYER = "media_player.hisense_tv"


async def call(hass: HomeAssistant, domain: str, service: str, **data: object) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    for _ in range(5):
        await asyncio.sleep(0)


async def test_volume_and_media_keys(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(hass, "media_player", "volume_up", entity_id=PLAYER)
    await call(hass, "media_player", "media_pause", entity_id=PLAYER)
    await call(hass, "media_player", "media_next_track", entity_id=PLAYER)
    assert tv.keys == ["KEY_VOLUMEUP", "KEY_PAUSE", "KEY_CHANNELUP"]


async def test_mute_only_sends_a_key_when_the_state_changes(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(hass, "media_player", "volume_mute", entity_id=PLAYER, is_volume_muted=False)
    assert tv.keys == []  # already unmuted as far as we know
    await call(hass, "media_player", "volume_mute", entity_id=PLAYER, is_volume_muted=True)
    assert tv.keys == ["KEY_MUTE"]
    assert hass.states.get(PLAYER).attributes["is_volume_muted"] is True  # type: ignore[union-attr]
    await call(hass, "media_player", "volume_mute", entity_id=PLAYER, is_volume_muted=True)
    assert tv.keys == ["KEY_MUTE"]


async def test_absolute_volume_is_offered_only_without_arc(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    arc = hass.states.get(PLAYER).attributes["supported_features"]  # type: ignore[union-attr]
    await tv.push_volume(20, output_type=0)
    await hass.async_block_till_done()
    speakers = hass.states.get(PLAYER).attributes["supported_features"]  # type: ignore[union-attr]
    assert speakers & 4 and not arc & 4  # MediaPlayerEntityFeature.VOLUME_SET == 4


async def test_turn_off_sends_power_only_when_on(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(hass, "media_player", "turn_off", entity_id=PLAYER)
    assert tv.keys == ["KEY_POWER"]
    tv.drop()
    await hass.async_block_till_done()
    await call(hass, "media_player", "turn_off", entity_id=PLAYER)
    assert tv.keys == ["KEY_POWER"]  # a second press would turn it back on


async def test_turn_on_wakes_without_blocking(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    tv.drop()
    await hass.async_block_till_done()
    await call(hass, "media_player", "turn_on", entity_id=PLAYER)
    assert tv.send_wake.await_count == 1  # type: ignore[attr-defined]


async def test_commands_while_off_explain_why(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    tv.drop()
    await hass.async_block_till_done()
    with pytest.raises(HomeAssistantError) as error:
        await call(hass, "media_player", "volume_up", entity_id=PLAYER)
    assert error.value.translation_key == "device_off"
    assert error.value.translation_domain == DOMAIN


async def test_select_source_and_app(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(hass, "media_player", "select_source", entity_id=PLAYER, source="HDMI1")
    await call(hass, "media_player", "select_source", entity_id=PLAYER, source="Netflix")
    sent = [payload for action, payload in tv.commands if action in ("changesource", "launchapp")]
    assert '"sourcename":"HDMI1"' in sent[0]
    assert '"name":"Netflix"' in sent[1]


async def test_play_channel_by_number_and_unknown_channel(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(
        hass,
        "media_player",
        "play_media",
        entity_id=PLAYER,
        media_content_type="channel",
        media_content_id="5",
    )
    assert ("changechannel", '{"channel_param":"P5"}') in tv.commands
    with pytest.raises(ServiceValidationError):
        await call(
            hass,
            "media_player",
            "play_media",
            entity_id=PLAYER,
            media_content_type="channel",
            media_content_id="99",
        )


async def test_media_browser_lists_channels_and_apps(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv, hass_ws_client
) -> None:
    await setup(hass, entry)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "media_player/browse_media", "entity_id": PLAYER})
    root = (await client.receive_json())["result"]
    assert [c["title"] for c in root["children"]] == ["Channels", "Apps"]
    await client.send_json(
        {
            "id": 2,
            "type": "media_player/browse_media",
            "entity_id": PLAYER,
            "media_content_id": "channels",
            "media_content_type": "channels",
        }
    )
    channels = (await client.receive_json())["result"]
    assert [c["title"] for c in channels["children"]] == ["1 Rai 1", "5 Canale5 HD"]


async def test_remote_sends_named_and_raw_keys(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(
        hass,
        "remote",
        "send_command",
        entity_id="remote.hisense_tv_remote",
        command=["home", "KEY_MENU"],
        delay_secs=0,
    )
    assert tv.keys == ["KEY_HOME", "KEY_MENU"]


async def test_button_press_sends_its_key(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await call(hass, "button", "press", entity_id="button.hisense_tv_home")
    assert tv.keys == ["KEY_HOME"]


async def test_sensors_follow_the_programme_and_go_unavailable_when_off(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    await tv.push_state(LIVE_STATE)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.hisense_tv_programme").state == "News"  # type: ignore[union-attr]
    assert hass.states.get("sensor.hisense_tv_channel").state == "Rai 1"  # type: ignore[union-attr]
    assert hass.states.get("sensor.hisense_tv_volume").state == "12"  # type: ignore[union-attr]
    tv.drop()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.hisense_tv_channel").state == "unavailable"  # type: ignore[union-attr]


async def test_selects_follow_the_tv(
    hass: HomeAssistant, entry: MockConfigEntry, tv: FakeTv
) -> None:
    await setup(hass, entry)
    source = hass.states.get("select.hisense_tv_source")
    assert source is not None
    assert source.state == "HDMI2"
    assert source.attributes["options"] == ["TV", "HDMI1", "HDMI2"]
    await call(hass, "select", "select_option", entity_id="select.hisense_tv_app", option="YouTube")
    assert any(action == "launchapp" and "YouTube" in payload for action, payload in tv.commands)
