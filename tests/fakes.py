"""Test doubles shared by the unit tests."""

from __future__ import annotations

from vidaa_tv.errors import ConnectionFailedError
from vidaa_tv.transport.base import DisconnectHandler, Message, MessageHandler


def _matches(topic_filter: str, topic: str) -> bool:
    if topic_filter.endswith("/#"):
        return topic.startswith(topic_filter[:-1])
    return topic_filter == topic


class FakeTransport:
    """In-memory Transport that records publications and lets tests inject replies."""

    def __init__(self) -> None:
        self.published: list[Message] = []
        self.handlers: dict[str, list[MessageHandler]] = {}
        self.reachable = True
        self.connect_error: Exception | None = None
        self.connected = False
        self.connect_calls = 0
        self._on_disconnect: DisconnectHandler | None = None

    async def connect(self) -> None:
        self.connect_calls += 1
        if self.connect_error is not None:
            raise self.connect_error
        if not self.reachable:
            raise ConnectionFailedError("unreachable")
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    def set_disconnect_handler(self, handler: DisconnectHandler | None) -> None:
        self._on_disconnect = handler

    def drop(self) -> None:
        """Simulate the TV disappearing."""
        self.connected = False
        if self._on_disconnect is not None:
            self._on_disconnect()

    async def publish(self, message: Message) -> None:
        self.published.append(message)

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        self.handlers.setdefault(topic, []).append(handler)

    async def deliver(self, topic: str, payload: bytes) -> None:
        for topic_filter, handlers in self.handlers.items():
            if _matches(topic_filter, topic):
                for handler in handlers:
                    await handler(Message(topic, payload))
