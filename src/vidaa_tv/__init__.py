"""Async client library for Hisense TVs running VIDAA OS."""

from .client import VidaaClient, mqtt_transport_factory
from .errors import (
    AuthenticationError,
    ConnectionFailedError,
    ProtocolError,
    UnsupportedFeatureError,
    VidaaError,
)
from .keys import RemoteKey
from .models import PowerState

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
