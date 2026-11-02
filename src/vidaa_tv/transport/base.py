"""Transport abstraction.

The protocol and capability layers depend only on this interface, so the
concrete wire technology (MQTT over TLS today) can be swapped or faked in tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Message:
    """A raw message exchanged with the TV."""

    topic: str
    payload: bytes


MessageHandler = Callable[[Message], Awaitable[None]]
DisconnectHandler = Callable[[], None]


class Transport(Protocol):
    """Bidirectional, topic-addressed message channel."""

    async def connect(self) -> None:
        """Open the connection; raise ConnectionFailedError on failure."""
        ...

    async def disconnect(self) -> None:
        """Close the connection. Safe to call when already closed."""
        ...

    def set_disconnect_handler(self, handler: DisconnectHandler | None) -> None:
        """Call ``handler`` when an established connection is lost unexpectedly."""
        ...

    async def publish(self, message: Message) -> None: ...

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        """Deliver every message received on ``topic`` to ``handler``."""
        ...
