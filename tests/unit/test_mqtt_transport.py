"""The MQTT transport against a scripted stand-in for the aiomqtt client."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, ClassVar

import aiomqtt
import pytest

from vidaa_tv.errors import ConnectionFailedError
from vidaa_tv.protocol.auth import static_credentials
from vidaa_tv.transport import mqtt
from vidaa_tv.transport.base import Message
from vidaa_tv.transport.mqtt import MqttTransport, TlsConfig


class FakeIncoming:
    def __init__(self, topic: str, payload: bytes) -> None:
        self.topic = aiomqtt.Topic(topic)
        self.payload = payload


class FakeClient:
    """Stands in for ``aiomqtt.Client``; tests feed it messages and failures."""

    instances: ClassVar[list[FakeClient]] = []
    fail_connect = False
    fail_subscribe = False
    fail_publish = False

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.subscribed: list[str] = []
        self.published: list[tuple[str, bytes]] = []
        self.queue: asyncio.Queue[Any] = asyncio.Queue()
        self._stream = self._messages()
        FakeClient.instances.append(self)

    async def __aenter__(self) -> FakeClient:
        if FakeClient.fail_connect:
            raise aiomqtt.MqttError("connect refused")
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def subscribe(self, topic: str) -> None:
        if FakeClient.fail_subscribe:
            raise aiomqtt.MqttError("subscribe refused")
        self.subscribed.append(topic)

    async def publish(self, topic: str, payload: bytes) -> None:
        if FakeClient.fail_publish:
            raise aiomqtt.MqttError("publish refused")
        self.published.append((topic, payload))

    @property
    def messages(self) -> AsyncIterator[FakeIncoming]:
        return self._stream

    async def _messages(self) -> AsyncIterator[FakeIncoming]:
        while True:
            item = await self.queue.get()
            if item is None:
                return
            if isinstance(item, Exception):
                raise item
            yield item


@pytest.fixture(autouse=True)
def fake_client(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.instances = []
    FakeClient.fail_connect = FakeClient.fail_subscribe = FakeClient.fail_publish = False
    monkeypatch.setattr(mqtt.aiomqtt, "Client", FakeClient)


def make() -> MqttTransport:
    return MqttTransport("tv.local", static_credentials("AA:BB:CC:DD:EE:FF"))


async def settle() -> None:
    for _ in range(5):
        await asyncio.sleep(0)


async def test_connect_failure_is_a_connection_error() -> None:
    FakeClient.fail_connect = True
    with pytest.raises(ConnectionFailedError):
        await make().connect()


async def test_subscription_failure_after_connect_is_a_connection_error() -> None:
    transport = make()

    async def handler(message: Message) -> None:
        return None

    await transport.subscribe("/a/#", handler)  # remembered, applied on connect
    FakeClient.fail_subscribe = True
    with pytest.raises(ConnectionFailedError):
        await transport.connect()
    await transport.disconnect()


async def test_late_subscription_failure_is_a_connection_error() -> None:
    transport = make()
    await transport.connect()
    FakeClient.fail_subscribe = True

    async def handler(message: Message) -> None:
        return None

    with pytest.raises(ConnectionFailedError):
        await transport.subscribe("/a/#", handler)
    await transport.disconnect()


async def test_publish_failure_is_a_connection_error() -> None:
    transport = make()
    await transport.connect()
    FakeClient.fail_publish = True
    with pytest.raises(ConnectionFailedError):
        await transport.publish(Message("/x", b"1"))
    await transport.disconnect()


async def test_publish_when_not_connected_is_a_connection_error() -> None:
    with pytest.raises(ConnectionFailedError):
        await make().publish(Message("/x", b"1"))


async def test_messages_reach_only_matching_handlers() -> None:
    transport = make()
    seen: list[Message] = []

    async def handler(message: Message) -> None:
        seen.append(message)

    await transport.subscribe("/remoteapp/mobile/#", handler)
    await transport.connect()
    client = FakeClient.instances[-1]
    assert client.subscribed == ["/remoteapp/mobile/#"]
    await client.queue.put(FakeIncoming("/remoteapp/mobile/x/state", b"{}"))
    await client.queue.put(FakeIncoming("/other/topic", b"{}"))
    await settle()
    assert [m.topic for m in seen] == ["/remoteapp/mobile/x/state"]
    await transport.disconnect()


async def test_a_failing_handler_does_not_stop_the_stream() -> None:
    transport = make()
    seen: list[bytes] = []

    async def handler(message: Message) -> None:
        if message.payload == b"bad":
            raise RuntimeError("handler bug")
        seen.append(message.payload)

    await transport.subscribe("/t/#", handler)
    await transport.connect()
    client = FakeClient.instances[-1]
    await client.queue.put(FakeIncoming("/t/a", b"bad"))
    await client.queue.put(FakeIncoming("/t/b", b"good"))
    await settle()
    assert seen == [b"good"]
    await transport.disconnect()


@pytest.mark.parametrize("ending", [None, aiomqtt.MqttError("dropped"), RuntimeError("unexpected")])
async def test_any_end_of_the_stream_reports_a_lost_connection(ending: object) -> None:
    transport = make()
    lost: list[bool] = []
    transport.set_disconnect_handler(lambda: lost.append(True))
    await transport.connect()
    await FakeClient.instances[-1].queue.put(ending)
    await settle()
    assert lost == [True]
    await transport.disconnect()


async def test_deliberate_disconnect_is_not_reported_as_a_loss() -> None:
    transport = make()
    lost: list[bool] = []
    transport.set_disconnect_handler(lambda: lost.append(True))
    await transport.connect()
    await transport.disconnect()
    await settle()
    assert lost == []


def test_tls_context_without_client_certificate() -> None:
    context = TlsConfig().build_context()
    assert context.check_hostname is False
