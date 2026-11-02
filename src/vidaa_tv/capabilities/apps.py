"""List and launch TV applications."""

from __future__ import annotations

from vidaa_tv.errors import UnsupportedFeatureError
from vidaa_tv.models import App
from vidaa_tv.protocol import parsers
from vidaa_tv.protocol.topics import Action
from vidaa_tv.session import Session


class Apps:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def list(self) -> list[App]:
        reply = await self._session.request(Action.APP_LIST, parsers.is_app_list)
        return parsers.parse_apps(reply.payload)

    async def launch(self, app: App | str) -> None:
        """Launch an app given as an ``App`` or by name (case-insensitive)."""
        target = app if isinstance(app, App) else await self._find(app)
        await self._session.send(
            Action.LAUNCH_APP,
            {
                "appId": target.id,
                "name": target.name,
                "url": target.url,
                "urlType": target.url_type,
                "storeType": target.store_type,
            },
        )

    async def _find(self, name: str) -> App:
        for candidate in await self.list():
            if candidate.name.casefold() == name.casefold():
                return candidate
        raise UnsupportedFeatureError(f"app not installed: {name}")
