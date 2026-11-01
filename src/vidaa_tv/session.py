"""A session binds a transport to one client identity and speaks the protocol."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from vidaa_tv.errors import ConnectionFailedError
from vidaa_tv.protocol import codec
from vidaa_tv.protocol.topics import Action, command_topic, mobile_filter
from vidaa_tv.transport.base import Message, Transport

DEFAULT_TIMEOUT = 4.0


@dataclass(frozen=True, slots=True)
class Reply:
    """A decoded message received from the TV."""

    topic: str
    payload: Any


ReplyMatcher = Callable[[Reply], bool]
ReplyListener = Callable[[Reply], None]


class Session:
    """Sends commands and correlates replies.

    The TV does not use a dedicated reply topic per command, so replies are
    recognised by the shape of their payload (``ReplyMatcher``). Capabilities
    receive a ``Session`` and never touch the transport directly.
    """

    def __init__(
        self, transport: Transport, client_id: str, *, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        self._transport = transport
        self._client_id = client_id
        self._timeout = timeout
        self._opened = False
        self._waiters: list[tuple[ReplyMatcher, asyncio.Future[Reply]]] = []
        self._listeners: list[ReplyListener] = []

    @property
    def client_id(self) -> str:
        return self._client_id

    async def open(self) -> None:
        """Start receiving messages addressed to this client and broadcasts."""
        if self._opened:
            return
        for topic_filter in mobile_filter(self._client_id):
            await self._transport.subscribe(topic_filter, self._on_message)
        self._opened = True

    def add_listener(self, listener: ReplyListener) -> None:
        """Be called for every message received, including unsolicited pushes."""
        self._listeners.append(listener)

    async def send(self, action: Action, payload: codec.Payload = None) -> None:
        """Publish a command without waiting for a reply."""
        message = Message(command_topic(self._client_id, action), codec.encode(payload))
        await self._transport.publish(message)

    async def request(
        self, action: Action, matcher: ReplyMatcher, payload: codec.Payload = None
    ) -> Reply:
        """Publish a command and return the first reply accepted by ``matcher``."""
        await self.open()
        future: asyncio.Future[Reply] = asyncio.get_running_loop().create_future()
        entry = (matcher, future)
        self._waiters.append(entry)
        try:
            await self.send(action, payload)
            return await asyncio.wait_for(future, self._timeout)
        except TimeoutError as exc:
            raise ConnectionFailedError(f"no reply to {action} within {self._timeout:g}s") from exc
        finally:
            if entry in self._waiters:
                self._waiters.remove(entry)

    async def _on_message(self, message: Message) -> None:
        reply = Reply(message.topic, codec.decode(message.payload))
        for listener in self._listeners:
            listener(reply)
        for matcher, future in list(self._waiters):
            if not future.done() and matcher(reply):
                future.set_result(reply)
