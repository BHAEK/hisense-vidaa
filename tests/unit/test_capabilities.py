import asyncio
import json

import pytest

from tests.fakes import FakeTransport
from vidaa_tv.capabilities.apps import Apps
from vidaa_tv.capabilities.remote import RemoteControl
from vidaa_tv.capabilities.sources import Sources
from vidaa_tv.capabilities.volume import VolumeControl
from vidaa_tv.errors import UnsupportedFeatureError
from vidaa_tv.session import Session

CLIENT = "AA$vidaa_common"
BASE = f"/remoteapp/mobile/{CLIENT}"
SOURCES = [
    {"sourceid": "0", "sourcename": "TV", "displayname": "TV"},
    {"sourceid": "4", "sourcename": "HDMI1", "displayname": "HDMI1"},
]


def make() -> tuple[FakeTransport, Session]:
    transport = FakeTransport()
    return transport, Session(transport, CLIENT, timeout=1)


async def reply_soon(transport: FakeTransport, topic: str, payload: object) -> None:
    await asyncio.sleep(0.01)
    await transport.deliver(topic, json.dumps(payload).encode())


async def test_sources_select_by_name_sends_id_and_name() -> None:
    transport, session = make()
    task = asyncio.create_task(Sources(session).select("hdmi1"))
    await reply_soon(transport, f"{BASE}/ui_service/data/sourcelist", SOURCES)
    await task
    assert transport.published[-1].payload == b'{"sourceid":"4","sourcename":"HDMI1"}'


async def test_sources_select_unknown_raises() -> None:
    transport, session = make()
    task = asyncio.create_task(Sources(session).select("nope"))
    await reply_soon(transport, f"{BASE}/ui_service/data/sourcelist", SOURCES)
    with pytest.raises(UnsupportedFeatureError):
        await task


async def test_apps_launch_copies_app_fields() -> None:
    transport, session = make()
    task = asyncio.create_task(Apps(session).launch("Netflix"))
    await reply_soon(
        transport,
        f"{BASE}/ui_service/data/applist",
        [{"url": "netflix", "name": "Netflix", "appId": "1", "urlType": 37, "storeType": 0}],
    )
    await task
    sent = json.loads(transport.published[-1].payload)
    assert sent == {
        "appId": "1",
        "name": "Netflix",
        "url": "netflix",
        "urlType": 37,
        "storeType": 0,
    }


async def test_volume_steps_when_audio_is_arc() -> None:
    transport, session = make()
    volume = VolumeControl(session, RemoteControl(session), step_delay=0)

    async def tv() -> None:
        topic = "/remoteapp/mobile/broadcast/platform_service/actions/volumechange"
        await asyncio.sleep(0.01)
        await transport.deliver(topic, b'{"volume_type":1,"volume_value":10}')
        await asyncio.sleep(0.05)
        await transport.deliver(topic, b'{"volume_type":1,"volume_value":12}')

    reply = asyncio.create_task(tv())
    result = await volume.set_level(12)
    await reply
    keys = [m.payload for m in transport.published if b"KEY_" in m.payload]
    assert keys == [b"KEY_VOLUMEUP", b"KEY_VOLUMEUP"]
    assert result.level == 12


async def test_volume_set_level_uses_absolute_command_without_arc() -> None:
    transport, session = make()
    volume = VolumeControl(session, RemoteControl(session), step_delay=0)

    async def tv() -> None:
        topic = "/remoteapp/mobile/broadcast/platform_service/actions/volumechange"
        await asyncio.sleep(0.01)
        await transport.deliver(topic, b'{"volume_type":0,"volume_value":10}')
        await asyncio.sleep(0.05)
        await transport.deliver(topic, b'{"volume_type":0,"volume_value":30}')

    reply = asyncio.create_task(tv())
    result = await volume.set_level(30)
    await reply
    assert any(
        m.payload == b"30" and m.topic.endswith("/changevolume") for m in transport.published
    )
    assert result.level == 30
