"""Keeps a transport connected, reconnecting with back-off.

A TV in standby refuses connections, so failing to connect is normal and is
reported through ``on_lost`` (the TV is considered off) rather than raised. Nothing
that happens while connecting may end the loop: unexpected errors are logged and
the attempt is retried.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from typing import Any

from .errors import VidaaError
from .transport.base import Transport

_LOGGER = logging.getLogger(__name__)
DEFAULT_BACKOFF: Sequence[float] = (1.0, 2.0, 5.0, 10.0, 20.0, 30.0)

TaskFactory = Callable[[Coroutine[Any, Any, None]], "asyncio.Task[None]"]


def _default_task_factory(coroutine: Coroutine[Any, Any, None]) -> asyncio.Task[None]:
    return asyncio.create_task(coroutine)


class Supervisor:
    def __init__(
        self,
        transport: Transport,
        *,
        on_connected: Callable[[], Awaitable[None]],
        on_lost: Callable[[], None],
        backoff: Sequence[float] = DEFAULT_BACKOFF,
        name: str = "TV",
        task_factory: TaskFactory | None = None,
    ) -> None:
        self._transport = transport
        self._on_connected = on_connected
        self._on_lost = on_lost
        self._backoff = backoff
        self._name = name
        self._task_factory = task_factory or _default_task_factory
        self._lost = asyncio.Event()
        self._skip = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._available: bool | None = None  # None until the first outcome is known
        self.connected = asyncio.Event()
        transport.set_disconnect_handler(self._lost.set)

    def start(self) -> None:
        if self._task is None:
            self._task = self._task_factory(self._run())

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
            if not await self._connect_once():
                self._mark_unavailable()
                await self._transport.disconnect()
                self._on_lost()
                await self._sleep(attempt)
                attempt += 1
                continue
            attempt = 0
            self._lost.clear()
            self._mark_available()
            self.connected.set()
            await self._lost.wait()
            self.connected.clear()
            await self._transport.disconnect()
            self._mark_unavailable()
            self._on_lost()

    async def _connect_once(self) -> bool:
        try:
            await self._transport.connect()
            await self._on_connected()
        except VidaaError as exc:
            _LOGGER.debug("%s: connection attempt failed: %s", self._name, exc)
            return False
        except Exception:
            _LOGGER.exception("%s: unexpected error while connecting; will retry", self._name)
            return False
        return True

    def _mark_available(self) -> None:
        if self._available is False:
            _LOGGER.info("%s is back online", self._name)
        elif self._available is None:
            _LOGGER.info("%s is connected", self._name)
        self._available = True

    def _mark_unavailable(self) -> None:
        if self._available is not False:
            _LOGGER.info("%s is unavailable", self._name)
        self._available = False

    async def _sleep(self, attempt: int) -> None:
        delay = self._backoff[min(attempt, len(self._backoff) - 1)]
        self._skip.clear()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._skip.wait(), delay)
