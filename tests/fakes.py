"""Test doubles shared by the unit tests."""

from __future__ import annotations

from vidaa_tv.transport.base import Message, MessageHandler


def _matches(topic_filter: str, topic: str) -> bool:
    if topic_filter.endswith("/#"):
        return topic.startswith(topic_filter[:-1])
    return topic_filter == topic


class FakeTransport:
    """In-memory Transport that records publications and lets tests inject replies."""

    def __init__(self) -> None:
        self.published: list[Message] = []
        self.handlers: dict[str, list[MessageHandler]] = {}

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def publish(self, message: Message) -> None:
        self.published.append(message)

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        self.handlers.setdefault(topic, []).append(handler)

    async def deliver(self, topic: str, payload: bytes) -> None:
        for topic_filter, handlers in self.handlers.items():
            if _matches(topic_filter, topic):
                for handler in handlers:
                    await handler(Message(topic, payload))
