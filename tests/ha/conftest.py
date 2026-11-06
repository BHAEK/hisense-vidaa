"""Fixtures for the Home Assistant integration tests (run with the Home Assistant test kit)."""

from __future__ import annotations

import sys
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.hisense_vidaa.const import CONF_DEVICE_ID, CONF_MAC, DOMAIN
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .fake_tv import TV_ID, FakeTv

DEVICE_ID = "AA:BB:CC:DD:EE:01"
HOST = "192.0.2.10"


if sys.platform == "win32":  # pragma: no cover - local runs on Windows only
    import pytest_socket

    # The Windows event loop builds its wake-up pipe from a socket pair, which the
    # Home Assistant test kit's socket guard would reject. Linux runs keep the guard.
    pytest_socket.disable_socket = lambda *args, **kwargs: None


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load the integration from this repository."""


@pytest.fixture
def tv() -> FakeTv:
    return FakeTv(paired_ids={DEVICE_ID})


@pytest.fixture(autouse=True)
def patched_network(tv: FakeTv) -> Generator[None]:
    """Route the integration to the fake TV and keep the tests off the real network."""
    factory = lambda *args, **kwargs: tv.factory  # noqa: E731 - mqtt_transport_factory()
    with (
        patch("custom_components.hisense_vidaa.mqtt_transport_factory", factory),
        patch("custom_components.hisense_vidaa.config_flow.mqtt_transport_factory", factory),
        patch(
            "custom_components.hisense_vidaa.vidaa_tv.client.lookup_mac",
            AsyncMock(return_value="AA:BB:CC:DD:EE:FF"),
        ),
        patch(
            "custom_components.hisense_vidaa.vidaa_tv.client.wake.send_wake", AsyncMock()
        ) as send_wake,
        patch(
            "custom_components.hisense_vidaa.vidaa_tv.client.wait_until_reachable",
            AsyncMock(return_value=True),
        ),
    ):
        tv.send_wake = send_wake  # type: ignore[attr-defined]
        yield


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Hisense TV",
        unique_id=TV_ID,
        data={CONF_HOST: HOST, CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_DEVICE_ID: DEVICE_ID},
    )
