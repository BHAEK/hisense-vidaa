"""MQTT credential generation.

Two schemes exist in the field:

* ``static`` - fixed credentials, used by older firmware (this project's primary
  target).
* ``dynamic`` - time-based credentials derived from the device id, used by
  newer firmware.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

STATIC_USERNAME = "hisenseservice"
STATIC_PASSWORD = "multimqttservice"

_DYNAMIC_PATTERN = "38D65DC30F45109A369A86FCE866A85B"
_DYNAMIC_SUFFIX = "h!i@s#$v%i^d&a*a"
_DYNAMIC_XOR = 0x5698_1477_2B03_A968


@dataclass(frozen=True, slots=True)
class Credentials:
    """Everything the broker needs to accept a connection."""

    client_id: str
    username: str
    password: str


def static_credentials(device_id: str, suffix: str = "vidaa_common") -> Credentials:
    """Credentials for firmware that uses the fixed username and password."""
    return Credentials(
        client_id=f"{device_id}${suffix}",
        username=STATIC_USERNAME,
        password=STATIC_PASSWORD,
    )


def _md5_upper(text: str) -> str:
    return hashlib.md5(text.encode(), usedforsecurity=False).hexdigest().upper()


def dynamic_credentials(
    device_id: str,
    *,
    brand: str = "his",
    operation: str = "vidaacommon",
    timestamp: int | None = None,
) -> Credentials:
    """Time-based credentials for newer firmware."""
    now = int(time.time()) if timestamp is None else timestamp
    race = _md5_upper(f"{_DYNAMIC_PATTERN}${device_id}")[:6]
    remainder = sum(int(digit) for digit in str(now)) % 10
    value = _md5_upper(f"{brand}{remainder}{_DYNAMIC_SUFFIX}")[:6]
    return Credentials(
        client_id=f"{device_id}${brand}${race}_{operation}_001",
        username=f"{brand}${now ^ _DYNAMIC_XOR}",
        password=_md5_upper(f"{now}${value}"),
    )
