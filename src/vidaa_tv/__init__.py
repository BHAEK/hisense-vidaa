"""Async client library for Hisense TVs running VIDAA OS."""

from vidaa_tv.errors import (
    AuthenticationError,
    ConnectionFailedError,
    ProtocolError,
    UnsupportedFeatureError,
    VidaaError,
)
from vidaa_tv.keys import RemoteKey

__all__ = [
    "AuthenticationError",
    "ConnectionFailedError",
    "ProtocolError",
    "RemoteKey",
    "UnsupportedFeatureError",
    "VidaaError",
]
