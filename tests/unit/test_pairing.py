import asyncio
import re

import pytest

from tests.fakes import FakeTransport
from vidaa_tv.errors import AuthenticationError
from vidaa_tv.pairing import Pairing, PairingOutcome, new_device_id
from vidaa_tv.session import Session

CLIENT = "AA$vidaa_common"
BASE = f"/remoteapp/mobile/{CLIENT}/ui_service/data"


def make() -> tuple[FakeTransport, Pairing]:
    transport = FakeTransport()
    return transport, Pairing(Session(transport, CLIENT, timeout=1))


async def test_unknown_identity_requires_pin() -> None:
    transport, pairing = make()
    task = asyncio.create_task(pairing.start())
    await asyncio.sleep(0.01)
    await transport.deliver(f"{BASE}/authentication", b"")
    assert await task is PairingOutcome.PIN_REQUIRED
    sent = [m.topic.rsplit("/", 1)[1] for m in transport.published]
    assert sent == ["gettvstate", "capability", "vidaa_app_connect"]


async def test_known_identity_skips_pin() -> None:
    transport, pairing = make()
    task = asyncio.create_task(pairing.start())
    await asyncio.sleep(0.01)
    await transport.deliver(f"{BASE}/capability", b'{"pvr":0}')
    assert await task is PairingOutcome.ALREADY_AUTHORISED


async def test_pin_accepted_sends_number_then_close() -> None:
    transport, pairing = make()
    task = asyncio.create_task(pairing.submit_pin("12-34"))
    await asyncio.sleep(0.01)
    await transport.deliver(f"{BASE}/authenticationcode", b'{"result":1,"info":""}')
    await task
    assert transport.published[0].payload == b'{"authNum":1234}'
    assert transport.published[1].topic.endswith("/actions/authenticationcodeclose")


async def test_pin_rejected_raises() -> None:
    transport, pairing = make()
    task = asyncio.create_task(pairing.submit_pin("0000"))
    await asyncio.sleep(0.01)
    await transport.deliver(f"{BASE}/authenticationcode", b'{"result":100,"info":"Wrong"}')
    with pytest.raises(AuthenticationError):
        await task


async def test_pin_without_digits_is_rejected_locally() -> None:
    _, pairing = make()
    with pytest.raises(AuthenticationError):
        await pairing.submit_pin("abc")


def test_new_device_id_is_locally_administered_unicast_mac() -> None:
    value = new_device_id()
    assert re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", value)
    first = int(value[:2], 16)
    assert first & 0x02 and not first & 0x01


async def test_pairing_flow_connects_pairs_and_closes() -> None:
    from vidaa_tv.pairing import PairingFlow

    transport = FakeTransport()
    flow = PairingFlow("tv", lambda host, creds: transport, timeout=1)
    task = asyncio.create_task(flow.start())
    await asyncio.sleep(0.02)
    await transport.deliver(
        f"/remoteapp/mobile/{flow.device_id}$vidaa_common/ui_service/data/authentication", b""
    )
    assert await task is PairingOutcome.PIN_REQUIRED
    assert transport.connected
    await flow.close()
    assert not transport.connected


async def test_pairing_flow_reads_the_tv_identity() -> None:
    from vidaa_tv.pairing import PairingFlow

    transport = FakeTransport()
    flow = PairingFlow("tv", lambda host, creds: transport, timeout=1)
    await flow._session.open()
    task = asyncio.create_task(flow.fetch_info())
    await asyncio.sleep(0.02)
    topic = f"/remoteapp/mobile/{flow.device_id}$vidaa_common/ui_service/data/capability"
    await transport.deliver(topic, b'{"softwareVersion":"V1","uniqueDeviceId":"abc"}')
    info = await task
    assert info is not None
    assert (info.software_version, info.device_id) == ("V1", "abc")


async def test_pairing_flow_info_is_none_when_the_tv_stays_silent() -> None:
    from vidaa_tv.pairing import PairingFlow

    flow = PairingFlow("tv", lambda host, creds: FakeTransport(), timeout=0.05)
    assert await flow.fetch_info() is None
