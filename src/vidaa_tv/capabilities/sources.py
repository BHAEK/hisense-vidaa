"""List and switch input sources."""

from __future__ import annotations

from vidaa_tv.errors import UnsupportedFeatureError
from vidaa_tv.models import Source
from vidaa_tv.protocol import parsers
from vidaa_tv.protocol.topics import Action
from vidaa_tv.session import Session


class Sources:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def list(self) -> list[Source]:
        reply = await self._session.request(Action.SOURCE_LIST, parsers.is_source_list)
        return parsers.parse_sources(reply.payload)

    async def select(self, source: Source | str) -> None:
        """Switch to a source given as a ``Source`` or by name (case-insensitive)."""
        target = source if isinstance(source, Source) else await self._find(source)
        await self._session.send(
            Action.CHANGE_SOURCE, {"sourceid": target.id, "sourcename": target.name}
        )

    async def _find(self, name: str) -> Source:
        for candidate in await self.list():
            if name.casefold() in {candidate.name.casefold(), candidate.display_name.casefold()}:
                return candidate
        raise UnsupportedFeatureError(f"unknown source: {name}")
