"""Cached lists of sources, apps and channels, shared by every entity of one TV."""

from __future__ import annotations

from collections.abc import Callable

from .vidaa_tv import VidaaClient
from .vidaa_tv.errors import VidaaError
from .vidaa_tv.models import App, Channel, Source


class VidaaCatalog:
    def __init__(self, client: VidaaClient) -> None:
        self._client = client
        self.sources: list[Source] = []
        self.apps: list[App] = []
        self.channels: list[Channel] = []
        self.loaded = False
        self._loading = False
        self._listeners: list[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener) if listener in self._listeners else None

    def reset(self) -> None:
        """Forget the lists, e.g. because the TV went off; they reload when it is back."""
        self.loaded = False

    async def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        try:
            self.sources = await self._client.sources.list()
            self.apps = await self._client.apps.list()
            self.loaded = True
        except VidaaError:
            self.loaded = False
        else:
            await self._refresh_channels()
        finally:
            self._loading = False
        for listener in list(self._listeners):
            listener()

    async def _refresh_channels(self) -> None:
        """Channels are optional: a TV without a tuner must not break the rest."""
        try:
            channel_lists = await self._client.channels.lists()
            self.channels = (
                await self._client.channels.channels(channel_lists[0]) if channel_lists else []
            )
        except VidaaError:
            self.channels = []
