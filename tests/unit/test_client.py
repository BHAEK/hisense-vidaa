import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

import pytest

from tests.fakes import FakeTransport
from vidaa_tv.client import VidaaClient
from vidaa_tv.models import PowerState
from vidaa_tv.protocol.auth import Credentials
from vidaa_tv.transport.base import Transport

STATE = "/remoteapp/mobile/broadcast/ui_service/state"


def make(transport: FakeTransport) -> VidaaClient:
    def factory(host: str, credentials: Credentials) -> Transport:
        return transport

    return VidaaClient("tv.local", "AA:BB:CC:DD:EE:FF", transport_factory=factory)


async def settle() -> None:
    for _ in range(5):
        await asyncio.sleep(0.01)


async def test_connects_and_tracks_pushed_state() -> None:
    transport = FakeTransport()
    client = make(transport)
    await client.start()
    assert await client.wait_connected(1)
    await transport.deliver(STATE, b'{"statetype":"sourceswitch","sourceid":"HDMI2"}')
    assert client.snapshot.power is PowerState.ON
    assert client.snapshot.state is not None
    assert client.snapshot.state.source_id == "HDMI2"
    await client.stop()


async def test_unreachable_tv_is_reported_as_off_and_reconnects_when_it_returns() -> None:
    transport = FakeTransport()
    transport.reachable = False
    client = make(transport)
    await client.start()
    await settle()
    assert not client.connected
    assert client.snapshot.power is PowerState.OFF
    transport.reachable = True
    client._supervisor.nudge()
    assert await client.wait_connected(1)
    await client.stop()


async def test_connection_drop_marks_off_then_recovers() -> None:
    transport = FakeTransport()
    client = make(transport)
    await client.start()
    assert await client.wait_connected(1)
    await transport.deliver(STATE, b'{"statetype":"livetv"}')
    transport.drop()
    await settle()
    assert client.snapshot.power is PowerState.OFF
    client._supervisor.nudge()
    await settle()
    assert transport.connect_calls >= 2
    await client.stop()


async def test_turn_off_presses_power() -> None:
    transport = FakeTransport()
    client = make(transport)
    await client.turn_off()
    assert transport.published[-1].payload == b"KEY_POWER"


async def test_unexpected_connect_error_does_not_end_supervision() -> None:
    transport = FakeTransport()
    transport.connect_error = RuntimeError("boom")
    client = make(transport)
    await client.start()
    await settle()
    assert not client.connected
    transport.connect_error = None
    client._supervisor.nudge()
    assert await client.wait_connected(1)
    await client.stop()


async def test_availability_transitions_are_logged_once(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="vidaa_tv.supervisor")
    transport = FakeTransport()
    transport.reachable = False
    client = make(transport)
    await client.start()
    await settle()
    client._supervisor.nudge()
    await settle()
    transport.reachable = True
    client._supervisor.nudge()
    assert await client.wait_connected(1)
    await client.stop()
    messages = [r.getMessage() for r in caplog.records]
    assert messages.count("tv.local is unavailable") == 1
    assert messages.count("tv.local is back online") == 1


async def test_supervision_uses_the_given_task_factory() -> None:
    created: list[str] = []

    def factory(coroutine: Coroutine[Any, Any, None]) -> asyncio.Task[None]:
        created.append("task")
        return asyncio.create_task(coroutine)

    transport = FakeTransport()

    def transport_factory(host: str, credentials: Credentials) -> Transport:
        return transport

    client = VidaaClient(
        "tv.local", "AA:BB:CC:DD:EE:FF", transport_factory=transport_factory, task_factory=factory
    )
    await client.start()
    assert created == ["task"]
    await client.stop()
