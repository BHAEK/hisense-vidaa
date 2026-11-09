"""The public entry point: one object per TV."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

from .capabilities.apps import Apps
from .capabilities.channels import Channels
from .capabilities.power import PowerControl
from .capabilities.remote import RemoteControl
from .capabilities.sources import Sources
from .capabilities.volume import VolumeControl
from .discovery import wake
from .discovery.neighbour import lookup_mac
from .discovery.reachability import DEFAULT_PORT, wait_until_reachable
from .errors import UnsupportedFeatureError
from .protocol.auth import Credentials, static_credentials
from .protocol.topics import Action
from .session import Session
from .supervisor import Supervisor, TaskFactory
from .tracker import Snapshot, SnapshotListener, StateTracker
from .transport.base import Transport

_LOGGER = logging.getLogger(__name__)

TransportFactory = Callable[[str, Credentials], Transport]


def mqtt_transport_factory(
    cert_file: Path | None = None, key_file: Path | None = None
) -> TransportFactory:
    """Build the default MQTT-over-TLS transport (needs the ``mqtt`` extra)."""

    def factory(host: str, credentials: Credentials) -> Transport:
        from .transport.mqtt import MqttTransport, TlsConfig

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
        task_factory: TaskFactory | None = None,
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
            name=host,
            task_factory=task_factory,
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

    # -- identity ----------------------------------------------------------
    @property
    def mac(self) -> str | None:
        return self._mac

    async def resolve_mac(self) -> str | None:
        """Learn the TV's MAC from the neighbour table; keeps a known value."""
        if self._mac is None:
            self._mac = await lookup_mac(self._host)
        return self._mac

    # -- power -------------------------------------------------------------
    async def wake(self) -> None:
        """Send the wake-up packets and return at once; the TV needs seconds to answer."""
        if self._mac is None:
            raise UnsupportedFeatureError("the TV MAC address is needed to wake it")
        addresses = wake.broadcast_addresses(self._host)
        _LOGGER.info("Sending wake-up packets to %s via %s", self._host, ", ".join(addresses))
        await wake.send_wake(self._mac, addresses)

    async def wait_for_wake(self, wait: float = 60.0) -> bool:
        """Wait for the TV to accept connections after ``wake``; True when it does."""
        reachable = await wait_until_reachable(self._host, DEFAULT_PORT, timeout=wait)
        if reachable:
            _LOGGER.info("%s is reachable again after the wake-up request", self._host)
            self._supervisor.nudge()
        else:
            _LOGGER.warning(
                "%s did not accept connections within %.0f s of the wake-up request; "
                "the TV may be in a standby that ignores network wake-up",
                self._host,
                wait,
            )
        return reachable

    async def turn_on(self, *, wait: float = 60.0) -> bool:
        """Wake the TV over the network; True once it accepts connections."""
        await self.wake()
        return await self.wait_for_wake(wait)

    async def turn_off(self) -> None:
        await self.power.turn_off()

    # -- internals ---------------------------------------------------------
    async def _on_connected(self) -> None:
        await self._session.open()
        # The TV answers both through broadcast pushes, which feed the tracker.
        await self._session.send(Action.GET_TV_STATE)
        await self._session.send(Action.GET_VOLUME)
        await self._session.send(Action.CAPABILITY)
        self._tracker.mark_connected()
