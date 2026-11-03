"""Keeps a transport connected, reconnecting with back-off.

A TV in standby refuses connections, so failing to connect is normal and is
reported through ``on_lost`` (the TV is considered off) rather than raised.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable, Sequence

from vidaa_tv.errors import VidaaError
from vidaa_tv.transport.base import Transport

_LOGGER = logging.getLogger(__name__)
DEFAULT_BACKOFF: Sequence[float] = (1.0, 2.0, 5.0, 10.0, 20.0, 30.0)


class Supervisor:
    def __init__(
        self,
        transport: Transport,
        *,
        on_connected: Callable[[], Awaitable[None]],
        on_lost: Callable[[], None],
        backoff: Sequence[float] = DEFAULT_BACKOFF,
    ) -> None:
        self._transport = transport
        self._on_connected = on_connected
        self._on_lost = on_lost
        self._backoff = backoff
        self._lost = asyncio.Event()
        self._skip = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self.connected = asyncio.Event()
        transport.set_disconnect_handler(self._lost.set)

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self.connected.clear()
        await self._transport.disconnect()

    def nudge(self) -> None:
        """Skip the current back-off wait, e.g. right after waking the TV."""
        self._skip.set()

    async def _run(self) -> None:
        attempt = 0
        while True:
            try:
                await self._transport.connect()
                await self._on_connected()
            except VidaaError as exc:
                _LOGGER.debug("connection attempt failed: %s", exc)
                await self._transport.disconnect()
                self._on_lost()
                await self._sleep(attempt)
                attempt += 1
                continue
            attempt = 0
            self._lost.clear()
            self.connected.set()
            await self._lost.wait()
            self.connected.clear()
            await self._transport.disconnect()
            self._on_lost()

    async def _sleep(self, attempt: int) -> None:
        delay = self._backoff[min(attempt, len(self._backoff) - 1)]
        self._skip.clear()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._skip.wait(), delay)
