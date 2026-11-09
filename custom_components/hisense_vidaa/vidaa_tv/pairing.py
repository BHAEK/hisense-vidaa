"""Interactive pairing of a client identity with the TV.

Pairing authorises a *client identity* (see docs/reverse-engineering/pairing.md).
A known identity needs no PIN, and the TV refuses a PIN for one it already
knows, so ``start`` reports which situation applies.
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from enum import StrEnum

from .errors import AuthenticationError, ConnectionFailedError
from .models import TvInfo
from .protocol import parsers
from .protocol.auth import Credentials, static_credentials
from .protocol.reply import Reply
from .protocol.topics import Action
from .session import Session
from .transport.base import Transport

_CONNECT_PAYLOAD = {"app_version": 2, "connect_result": 0, "device_type": "Mobile App"}


class PairingOutcome(StrEnum):
    PIN_REQUIRED = "pin_required"
    ALREADY_AUTHORISED = "already_authorised"


def new_device_id() -> str:
    """Random locally-administered MAC-style id for a fresh client identity."""
    octets = bytearray(secrets.token_bytes(6))
    octets[0] = (octets[0] | 0x02) & 0xFE
    return ":".join(f"{octet:02X}" for octet in octets)


def _asks_for_pin(reply: Reply) -> bool:
    return reply.topic.endswith("/ui_service/data/authentication")


def _is_known_identity(reply: Reply) -> bool:
    return reply.topic.endswith(("/ui_service/data/capability", "/ui_service/data/state"))


def _is_auth_result(reply: Reply) -> bool:
    return reply.topic.endswith("/ui_service/data/authenticationcode") and (
        isinstance(reply.payload, dict) and "result" in reply.payload
    )


class Pairing:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def start(self) -> PairingOutcome:
        """Ask the TV to show a PIN, or detect that this identity is already trusted."""
        await self._session.open()
        decisive = self._session.watch(lambda r: _asks_for_pin(r) or _is_known_identity(r))
        await self._session.send(Action.GET_TV_STATE)
        await self._session.send(Action.CAPABILITY)
        await self._session.send(Action.APP_CONNECT, _CONNECT_PAYLOAD)
        reply = await self._session.wait(decisive, "pairing response")
        if _asks_for_pin(reply):
            return PairingOutcome.PIN_REQUIRED
        return PairingOutcome.ALREADY_AUTHORISED

    async def submit_pin(self, pin: str) -> None:
        """Send the PIN shown on screen; raise AuthenticationError if refused."""
        digits = re.sub(r"\D", "", pin)
        if not digits:
            raise AuthenticationError("the PIN must contain digits")
        await self._session.open()
        result = self._session.watch(_is_auth_result)
        # The vendor app sends the PIN as a string (it concatenates the four digit fields);
        # a JSON number cannot carry a leading zero.
        await self._session.send(Action.AUTHENTICATION_CODE, {"authNum": digits})
        reply = await self._session.wait(result, "PIN verdict")
        if reply.payload.get("result") != 1:
            raise AuthenticationError(f"PIN rejected: {reply.payload}")
        await self._session.send(Action.AUTHENTICATION_CODE_CLOSE)


class PairingFlow:
    """Owns the connection used while pairing a new client identity.

    Typical use (from a configuration UI)::

        flow = PairingFlow(host, transport_factory)
        outcome = await flow.start()          # PIN_REQUIRED or ALREADY_AUTHORISED
        if outcome is PairingOutcome.PIN_REQUIRED:
            await flow.submit_pin(pin_from_user)
        await flow.close()
        save(flow.device_id)
    """

    def __init__(
        self,
        host: str,
        transport_factory: Callable[[str, Credentials], Transport],
        *,
        device_id: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self.device_id = device_id or new_device_id()
        credentials = static_credentials(self.device_id)
        self._transport = transport_factory(host, credentials)
        self._session = Session(self._transport, credentials.client_id, timeout=timeout)
        self._pairing = Pairing(self._session)

    async def start(self) -> PairingOutcome:
        await self._transport.connect()
        return await self._pairing.start()

    async def submit_pin(self, pin: str) -> None:
        await self._pairing.submit_pin(pin)

    async def fetch_info(self) -> TvInfo | None:
        """Ask the (paired) TV who it is; ``None`` when it does not answer in time."""
        try:
            reply = await self._session.request(Action.CAPABILITY, parsers.is_capability)
        except ConnectionFailedError:
            return None
        return parsers.parse_tv_info(reply.payload)

    async def close(self) -> None:
        await self._transport.disconnect()
