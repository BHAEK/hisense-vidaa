"""Async client library for Hisense TVs running VIDAA OS."""

from vidaa_tv.client import VidaaClient, mqtt_transport_factory
from vidaa_tv.errors import (
    AuthenticationError,
    ConnectionFailedError,
    ProtocolError,
    UnsupportedFeatureError,
    VidaaError,
)
from vidaa_tv.keys import RemoteKey
from vidaa_tv.models import PowerState

__all__ = [
    "AuthenticationError",
    "ConnectionFailedError",
    "PowerState",
    "ProtocolError",
    "RemoteKey",
    "UnsupportedFeatureError",
    "VidaaClient",
    "VidaaError",
    "mqtt_transport_factory",
]
