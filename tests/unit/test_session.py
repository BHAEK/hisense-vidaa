import asyncio

import pytest

from tests.fakes import FakeTransport
from vidaa_tv.capabilities.remote import RemoteControl
from vidaa_tv.errors import ConnectionFailedError
from vidaa_tv.keys import RemoteKey
from vidaa_tv.protocol.topics import Action
from vidaa_tv.session import Reply, Session

CLIENT = "AA$vidaa_common"
REPLY_TOPIC = f"/remoteapp/mobile/{CLIENT}/ui_service/data/state"


def is_tv_state(reply: Reply) -> bool:
    return isinstance(reply.payload, dict) and "statetype" in reply.payload


async def test_remote_press_publishes_raw_key() -> None:
    transport = FakeTransport()
    await RemoteControl(Session(transport, CLIENT)).press(RemoteKey.BACK)
    [message] = transport.published
    assert message.topic == f"/remoteapp/tv/remote_service/{CLIENT}/actions/sendkey"
    assert message.payload == b"KEY_RETURNS"


async def test_request_matches_reply_by_payload_shape() -> None:
    transport = FakeTransport()
    session = Session(transport, CLIENT, timeout=1)
    task = asyncio.create_task(session.request(Action.GET_TV_STATE, is_tv_state))
    await asyncio.sleep(0.01)
    await transport.deliver(REPLY_TOPIC, b'{"is_lock":0}')  # ignored: wrong shape
    await transport.deliver(REPLY_TOPIC, b'{"statetype":"sourceswitch","sourceid":"HDMI2"}')
    reply = await task
    assert reply.payload["sourceid"] == "HDMI2"


async def test_listeners_see_unsolicited_broadcasts() -> None:
    transport = FakeTransport()
    session = Session(transport, CLIENT)
    seen: list[Reply] = []
    session.add_listener(seen.append)
    await session.open()
    await transport.deliver("/remoteapp/mobile/broadcast/ui_service/state", b'{"statetype":"x"}')
    assert [r.payload for r in seen] == [{"statetype": "x"}]


async def test_request_times_out_as_connection_error() -> None:
    session = Session(FakeTransport(), CLIENT, timeout=0.05)
    with pytest.raises(ConnectionFailedError):
        await session.request(Action.GET_TV_STATE, is_tv_state)
