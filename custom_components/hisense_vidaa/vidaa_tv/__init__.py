"""Async client library for Hisense TVs running VIDAA OS."""

from .__version__ import __version__
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
    "__version__",
    "mqtt_transport_factory",
]
