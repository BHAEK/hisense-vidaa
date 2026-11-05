"""Payload encoding and decoding."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ..errors import ProtocolError

Payload = Mapping[str, Any] | str | None


def encode(payload: Payload) -> bytes:
    """Serialise an outgoing payload.

    ``None`` becomes an empty body, a string is sent verbatim and a mapping is
    sent as compact JSON.
    """
    if payload is None:
        return b""
    if isinstance(payload, str):
        return payload.encode()
    return json.dumps(payload, separators=(",", ":")).encode()


def decode(raw: bytes) -> Any:
    """Parse an incoming payload; an empty body yields ``None``."""
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"payload is not valid JSON: {raw[:80]!r}") from exc
