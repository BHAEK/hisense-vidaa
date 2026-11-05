"""The decoded message type shared by the session and the parsers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Reply:
    """A decoded message received from the TV."""

    topic: str
    payload: Any
