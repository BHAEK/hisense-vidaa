"""A scripted TV: answers the way the real one does, for the integration tests."""

from __future__ import annotations

import json
from typing import Any

from custom_components.hisense_vidaa.vidaa_tv.errors import ConnectionFailedError
from custom_components.hisense_vidaa.vidaa_tv.protocol.auth import Credentials
from custom_components.hisense_vidaa.vidaa_tv.transport.base import (
    DisconnectHandler,
    Message,
    MessageHandler,
)

TV_ID = "tv-unique-id-1"
PIN = "1234"
MOBILE = "/remoteapp/mobile"

SOURCES = [
    {"sourceid": "0", "sourcename": "TV", "displayname": "TV", "is_signal": "1"},
    {"sourceid": "4", "sourcename": "HDMI1", "displayname": "HDMI1", "is_signal": "0"},
    {"sourceid": "5", "sourcename": "HDMI2", "displayname": "HDMI2", "is_signal": "1"},
]
APPS = [
    {"appId": "1", "name": "Netflix", "url": "netflix", "urlType": 37, "storeType": 0},
    {"appId": "3", "name": "YouTube", "url": "youtube", "urlType": 37, "storeType": 0},
]
CHANNELS = [
    {"channel_num": "1", "channel_name": "Rai 1", "channel_param": "P1"},
    {"channel_num": "5", "channel_name": "Canale5 HD", "channel_param": "P5"},
]
CAPABILITY = {
    "softwareVersion": "V0001.01.00a.P0219",
    "boardVersion": "MSD6886",
    "devicemsg": "65A_TEST",
    "uniqueDeviceId": TV_ID,
    "vendorBrand": "his",
    "pvr": 0,
}
HDMI_STATE = {
    "statetype": "sourceswitch",
    "sourceid": "HDMI2",
    "sourcename": "HDMI2",
    "is_signal": 1,
}
LIVE_STATE = {
    "statetype": "livetv",
    "channel_num": "1",
    "channel_name": "Rai 1",
    "progname": "News",
    "starttime": 1_000,
    "endtime": 1_600,
    "detail": "Daily news",
}


class FakeTv:
    """In-memory ``Transport`` that behaves like a paired (or unpaired) TV."""

    def __init__(
        self, *, paired_ids: set[str] | None = None, state: dict[str, Any] | None = None
    ) -> None:
        self.online = True
        self.pin = PIN
        self.paired_ids: set[str] = paired_ids if paired_ids is not None else set()
        self.accept_any_identity = False
        self.state = state or HDMI_STATE
        self.volume = {"volume_type": 1, "volume_value": 12}
        self.keys: list[str] = []
        self.commands: list[tuple[str, Any]] = []
        self.connected = False
        self.client_ids: list[str] = []
        self._handlers: dict[str, list[MessageHandler]] = {}
        self._on_disconnect: DisconnectHandler | None = None

    # -- the transport interface ------------------------------------------------
    def factory(self, host: str, credentials: Credentials) -> FakeTv:
        self.client_ids.append(credentials.client_id)
        return self

    async def connect(self) -> None:
        if not self.online:
            raise ConnectionFailedError("TV is off")
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    def set_disconnect_handler(self, handler: DisconnectHandler | None) -> None:
        self._on_disconnect = handler

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    async def publish(self, message: Message) -> None:
        if not self.connected:
            raise ConnectionFailedError("not connected")
        _, _, _, _service, client, _, action = message.topic.split("/")
        payload = message.payload.decode() if message.payload else ""
        self.commands.append((action, payload))
        await self._answer(client, action, payload)

    # -- test helpers ------------------------------------------------------------
    def drop(self) -> None:
        self.online = False
        self.connected = False
        if self._on_disconnect is not None:
            self._on_disconnect()

    async def push_state(self, state: dict[str, Any]) -> None:
        self.state = state
        await self._deliver(f"{MOBILE}/broadcast/ui_service/state", state)

    async def push_volume(self, level: int, output_type: int = 1) -> None:
        self.volume = {"volume_type": output_type, "volume_value": level}
        await self._deliver(
            f"{MOBILE}/broadcast/platform_service/actions/volumechange", self.volume
        )

    # -- behaviour ---------------------------------------------------------------
    def _is_paired(self, client: str) -> bool:
        return self.accept_any_identity or client.split("$")[0] in self.paired_ids

    async def _answer(self, client: str, action: str, payload: str) -> None:
        base = f"{MOBILE}/{client}"
        if action == "gettvstate":
            if not self._is_paired(client):
                await self._deliver(f"{base}/ui_service/data/authentication", None)
            await self._deliver(f"{MOBILE}/broadcast/ui_service/state", self.state)
        elif action == "getvolume":
            await self._deliver(
                f"{MOBILE}/broadcast/platform_service/actions/volumechange", self.volume
            )
        elif action == "capability":
            await self._deliver(f"{base}/ui_service/data/capability", CAPABILITY)
        elif action == "vidaa_app_connect":
            if not self._is_paired(client):
                await self._deliver(f"{base}/ui_service/data/authentication", None)
            else:
                await self._deliver(f"{base}/ui_service/data/capability", CAPABILITY)
        elif action == "authenticationcode":
            sent = json.loads(payload).get("authNum")
            ok = isinstance(sent, str) and sent == self.pin  # the real TV needs the string form
            if ok:
                self.paired_ids.add(client.split("$")[0])
            await self._deliver(
                f"{base}/ui_service/data/authenticationcode",
                {"result": 1 if ok else 100, "info": ""},
            )
        elif action == "sourcelist":
            await self._deliver(f"{base}/ui_service/data/sourcelist", SOURCES)
        elif action == "applist":
            await self._deliver(f"{base}/ui_service/data/applist", APPS)
        elif action == "getchannellistinfo":
            info = [{"list_name": "DTT", "list_para": "L1", "list_version": "1"}]
            await self._deliver(f"{base}/platform_service/data/getchannellistinfo", info)
        elif action == "channellist":
            listing = {"list_para": "L1", "list_name": "DTT", "list": CHANNELS}
            await self._deliver(f"{base}/platform_service/data/channellist", listing)
        elif action == "sendkey":
            self.keys.append(payload)

    async def _deliver(self, topic: str, body: Any) -> None:
        raw = b"" if body is None else json.dumps(body).encode()
        for topic_filter, handlers in list(self._handlers.items()):
            matches = (
                topic.startswith(topic_filter[:-1])
                if topic_filter.endswith("/#")
                else topic == topic_filter
            )
            if matches:
                for handler in handlers:
                    await handler(Message(topic, raw))
