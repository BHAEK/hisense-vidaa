"""Remote control: send key presses."""

from __future__ import annotations

from vidaa_tv.keys import RemoteKey
from vidaa_tv.protocol.topics import Action
from vidaa_tv.session import Session


class RemoteControl:
    """Emulates the physical remote."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def press(self, key: RemoteKey | str) -> None:
        """Press a key; raw ``KEY_*`` names are accepted for undocumented keys."""
        await self._session.send(Action.SEND_KEY, str(key))
