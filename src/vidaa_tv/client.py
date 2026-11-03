"""The public entry point: one object per TV."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

from vidaa_tv.capabilities.apps import Apps
from vidaa_tv.capabilities.channels import Channels
from vidaa_tv.capabilities.power import PowerControl
from vidaa_tv.capabilities.remote import RemoteControl
from vidaa_tv.capabilities.sources import Sources
from vidaa_tv.capabilities.volume import VolumeControl
from vidaa_tv.discovery import wake
from vidaa_tv.discovery.reachability import DEFAULT_PORT, wait_until_reachable
from vidaa_tv.errors import UnsupportedFeatureError
from vidaa_tv.protocol.auth import Credentials, static_credentials
from vidaa_tv.protocol.topics import Action
from vidaa_tv.session import Session
from vidaa_tv.supervisor import Supervisor
from vidaa_tv.tracker import Snapshot, SnapshotListener, StateTracker
from vidaa_tv.transport.base import Transport

TransportFactory = Callable[[str, Credentials], Transport]


def mqtt_transport_factory(
    cert_file: Path | None = None, key_file: Path | None = None
) -> TransportFactory:
    """Build the default MQTT-over-TLS transport (needs the ``mqtt`` extra)."""

    def factory(host: str, credentials: Credentials) -> Transport:
        from vidaa_tv.transport.mqtt import MqttTransport, TlsConfig

        tls = TlsConfig(cert_file=cert_file, key_file=key_file)
        return MqttTransport(host, credentials, tls=tls)

    return factory


class VidaaClient:
    """Stays connected to one TV, tracks its state and exposes its features.

    ``device_id`` is the paired client identity (a MAC-style string); ``mac`` is the
    TV's own address, needed only to wake it.
    """

    def __init__(
        self,
        host: str,
        device_id: str,
        *,
        mac: str | None = None,
        transport_factory: TransportFactory | None = None,
        timeout: float = 4.0,
    ) -> None:
        self._host = host
        self._mac = mac
        credentials = static_credentials(device_id)
        factory = transport_factory or mqtt_transport_factory()
        self._transport = factory(host, credentials)
        self._session = Session(self._transport, credentials.client_id, timeout=timeout)
        self._tracker = StateTracker()
        self._session.add_listener(self._tracker.apply)
        self._supervisor = Supervisor(
            self._transport,
            on_connected=self._on_connected,
            on_lost=self._tracker.mark_unreachable,
        )
        self.remote = RemoteControl(self._session)
        self.power = PowerControl(self.remote)
        self.volume = VolumeControl(self._session, self.remote)
        self.sources = Sources(self._session)
        self.apps = Apps(self._session)
        self.channels = Channels(self._session)

    # -- lifecycle ---------------------------------------------------------
    async def start(self) -> None:
        """Begin connecting in the background; returns immediately."""
        self._supervisor.start()

    async def stop(self) -> None:
        await self._supervisor.stop()

    @property
    def connected(self) -> bool:
        return self._supervisor.connected.is_set()

    async def wait_connected(self, timeout: float | None = None) -> bool:
        try:
            await asyncio.wait_for(self._supervisor.connected.wait(), timeout)
        except TimeoutError:
            return False
        return True

    # -- state -------------------------------------------------------------
    @property
    def snapshot(self) -> Snapshot:
        return self._tracker.snapshot

    def add_listener(self, listener: SnapshotListener) -> Callable[[], None]:
        """Be notified whenever the snapshot changes; call the result to stop."""
        return self._tracker.add_listener(listener)

    # -- power -------------------------------------------------------------
    async def turn_on(self, *, wait: float = 60.0) -> bool:
        """Wake the TV over the network; True once it accepts connections."""
        if self._mac is None:
            raise UnsupportedFeatureError("the TV MAC address is needed to wake it")
        await wake.send_wake(self._mac, wake.broadcast_addresses(self._host))
        reachable = await wait_until_reachable(self._host, DEFAULT_PORT, timeout=wait)
        if reachable:
            self._supervisor.nudge()
        return reachable

    async def turn_off(self) -> None:
        await self.power.turn_off()

    # -- internals ---------------------------------------------------------
    async def _on_connected(self) -> None:
        await self._session.open()
        # The TV answers both through broadcast pushes, which feed the tracker.
        await self._session.send(Action.GET_TV_STATE)
        await self._session.send(Action.GET_VOLUME)
        await self._session.send(Action.CAPABILITY)
