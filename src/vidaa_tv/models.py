"""Immutable value objects returned by the library."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

ARC_VOLUME_TYPE = 1


class PowerState(StrEnum):
    """What is known about the TV's power."""

    UNKNOWN = "unknown"
    ON = "on"
    STANDBY = "standby"  # the TV announced it is going to sleep
    OFF = "off"  # unreachable on the network


@dataclass(frozen=True, slots=True)
class TvInfo:
    """Identity of the TV as reported by its ``capability`` message."""

    software_version: str = ""
    board: str = ""
    chip: str = ""
    model_code: str = ""
    brand: str = ""
    device_id: str = ""
    has_pvr: bool = False


@dataclass(frozen=True, slots=True)
class Source:
    """An input source, e.g. HDMI1."""

    id: str
    name: str
    display_name: str
    has_signal: bool | None = None


@dataclass(frozen=True, slots=True)
class App:
    """An application installed on the TV."""

    id: str
    name: str
    url: str
    url_type: int = 37
    store_type: int = 0


@dataclass(frozen=True, slots=True)
class Volume:
    """Volume as reported by the TV."""

    level: int
    output_type: int

    @property
    def is_arc(self) -> bool:
        """True when audio goes to an ARC device; absolute volume cannot be set."""
        return self.output_type == ARC_VOLUME_TYPE


@dataclass(frozen=True, slots=True)
class Programme:
    """The programme currently on air on a live TV channel."""

    title: str
    description: str = ""
    start: int | None = None  # unix seconds
    end: int | None = None  # unix seconds

    @property
    def duration(self) -> int | None:
        """Length in seconds, when both ends are known."""
        if self.start is None or self.end is None or self.end <= self.start:
            return None
        return self.end - self.start

    def position(self, now: float) -> int | None:
        """Seconds elapsed at ``now`` (unix seconds), clamped to the programme."""
        duration = self.duration
        if duration is None or self.start is None:
            return None
        return max(0, min(duration, int(now - self.start)))


@dataclass(frozen=True, slots=True)
class TvState:
    """What the TV is currently showing.

    ``kind`` is the TV's own ``statetype`` (``sourceswitch``, ``livetv``, ``app``...).
    Only the fields relevant to that kind are filled.
    """

    kind: str
    source_id: str | None = None
    source_name: str | None = None
    has_signal: bool | None = None
    channel_number: str | None = None
    channel_name: str | None = None
    channel_param: str | None = None
    programme: Programme | None = None
    app_name: str | None = None
    app_url: str | None = None


@dataclass(frozen=True, slots=True)
class Channel:
    number: str
    name: str
    param: str  # opaque handle used to tune the channel


@dataclass(frozen=True, slots=True)
class ChannelList:
    id: str
    name: str
    version: str = ""
