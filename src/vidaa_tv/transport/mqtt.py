"""MQTT-over-TLS transport (requires the ``mqtt`` extra)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import ssl
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import aiomqtt

from vidaa_tv.errors import ConnectionFailedError
from vidaa_tv.protocol.auth import Credentials
from vidaa_tv.transport.base import DisconnectHandler, Message, MessageHandler

DEFAULT_PORT = 36669
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TlsConfig:
    """Client-side TLS settings.

    The TV uses a private CA and a self-signed server certificate, so server
    verification is disabled by default. ``legacy_compat`` relaxes protocol and
    cipher floors for old firmware.
    """

    cert_file: Path | None = None
    key_file: Path | None = None
    key_password: str | None = None
    verify_server: bool = False
    legacy_compat: bool = True

    def build_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if self.legacy_compat:
            # Relax the floors for old firmware; a modern OpenSSL may refuse some of
            # them, in which case the defaults are kept and negotiation decides.
            with contextlib.suppress(ValueError, ssl.SSLError), warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                context.minimum_version = ssl.TLSVersion.TLSv1
            with contextlib.suppress(ssl.SSLError):
                context.set_ciphers("DEFAULT:@SECLEVEL=0")
        if not self.verify_server:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        if self.cert_file is not None:
            context.load_cert_chain(self.cert_file, self.key_file, self.key_password)
        return context


class MqttTransport:
    """``Transport`` implementation on top of aiomqtt."""

    def __init__(
        self,
        host: str,
        credentials: Credentials,
        *,
        port: int = DEFAULT_PORT,
        tls: TlsConfig | None = None,
        timeout: float = 4.0,
    ) -> None:
        self._host = host
        self._credentials = credentials
        self._port = port
        self._tls = tls
        self._timeout = timeout
        self._client: aiomqtt.Client | None = None
        self._listener: asyncio.Task[None] | None = None
        self._handlers: dict[str, list[MessageHandler]] = defaultdict(list)
        self._on_disconnect: DisconnectHandler | None = None

    async def connect(self) -> None:
        context = await asyncio.to_thread(self._tls.build_context) if self._tls else None
        client = aiomqtt.Client(
            hostname=self._host,
            port=self._port,
            identifier=self._credentials.client_id,
            username=self._credentials.username,
            password=self._credentials.password,
            tls_context=context,
            tls_insecure=bool(self._tls and not self._tls.verify_server),
            timeout=self._timeout,
        )
        try:
            await client.__aenter__()
        except (aiomqtt.MqttError, OSError) as exc:
            raise ConnectionFailedError(f"cannot connect to {self._host}: {exc}") from exc
        self._client = client
        self._listener = asyncio.create_task(self._listen(client))
        try:
            for topic in list(self._handlers):
                await client.subscribe(topic)
        except aiomqtt.MqttError as exc:
            await self.disconnect()
            raise ConnectionFailedError(f"subscription failed: {exc}") from exc

    async def disconnect(self) -> None:
        if self._listener is not None:
            self._listener.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener
            self._listener = None
        if self._client is not None:
            client, self._client = self._client, None
            with contextlib.suppress(aiomqtt.MqttError, OSError):
                await client.__aexit__(None, None, None)

    def set_disconnect_handler(self, handler: DisconnectHandler | None) -> None:
        self._on_disconnect = handler

    async def publish(self, message: Message) -> None:
        client = self._require_client()
        try:
            await client.publish(message.topic, message.payload)
        except aiomqtt.MqttError as exc:
            raise ConnectionFailedError(f"publish failed: {exc}") from exc

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        first = topic not in self._handlers
        self._handlers[topic].append(handler)
        if first and self._client is not None:
            try:
                await self._client.subscribe(topic)
            except aiomqtt.MqttError as exc:
                raise ConnectionFailedError(f"subscription failed: {exc}") from exc

    def _require_client(self) -> aiomqtt.Client:
        if self._client is None:
            raise ConnectionFailedError("transport is not connected")
        return self._client

    async def _listen(self, client: aiomqtt.Client) -> None:
        try:
            async for incoming in client.messages:
                payload = incoming.payload
                message = Message(
                    topic=str(incoming.topic),
                    payload=payload if isinstance(payload, bytes) else b"",
                )
                await self._dispatch(incoming, message)
        except aiomqtt.MqttError as exc:
            _LOGGER.debug("message stream ended: %s", exc)
        except Exception:
            _LOGGER.exception("message stream failed unexpectedly")
        # Reaching this point without cancellation means the connection was lost.
        if self._client is client and self._on_disconnect is not None:
            self._on_disconnect()

    async def _dispatch(self, incoming: aiomqtt.Message, message: Message) -> None:
        for topic_filter, handlers in list(self._handlers.items()):
            if not incoming.topic.matches(topic_filter):
                continue
            for handler in list(handlers):
                try:
                    await handler(message)
                except Exception:  # a faulty handler must not stop the listener
                    _LOGGER.exception("handler failed for %s", message.topic)
