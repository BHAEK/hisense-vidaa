"""Keeps the latest known TV state, fed by the messages the TV pushes.

The TV answers many questions with broadcast pushes instead of dedicated
replies, so the current state is best obtained by listening rather than asking.
The tracker is pure: it consumes ``Reply`` objects and holds no I/O.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from .errors import ProtocolError
from .models import PowerState, TvInfo, TvState, Volume
from .protocol import parsers
from .protocol.reply import Reply


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Everything currently known about the TV."""

    power: PowerState = PowerState.UNKNOWN
    state: TvState | None = None
    volume: Volume | None = None
    info: TvInfo | None = None
    auth_required: bool = False  # the TV asked for a PIN: this identity is not paired


SnapshotListener = Callable[[Snapshot], None]


class StateTracker:
    def __init__(self) -> None:
        self._snapshot = Snapshot()
        self._listeners: list[SnapshotListener] = []

    @property
    def snapshot(self) -> Snapshot:
        return self._snapshot

    def add_listener(self, listener: SnapshotListener) -> Callable[[], None]:
        """Register a listener; the returned callable unregisters it."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener) if listener in self._listeners else None

    def mark_unreachable(self) -> None:
        """Record that the TV cannot be reached (it is off or unplugged)."""
        self._update(replace(self._snapshot, power=PowerState.OFF, auth_required=False))

    def apply(self, reply: Reply) -> None:
        """Fold one incoming message into the snapshot."""
        last = reply.topic.rsplit("/", 1)[-1]
        try:
            if reply.topic.endswith("/ui_service/state"):
                self._update(
                    replace(
                        self._snapshot,
                        power=PowerState.ON,
                        state=parsers.parse_tv_state(reply.payload),
                    )
                )
            elif last == "volumechange" and parsers.is_volume(reply):
                self._update(
                    replace(
                        self._snapshot,
                        power=PowerState.ON,
                        volume=parsers.parse_volume(reply.payload),
                    )
                )
            elif reply.topic.endswith("/ui_service/data/authentication"):
                self._update(replace(self._snapshot, auth_required=True))
            elif last == "capability" and parsers.is_capability(reply):
                self._update(replace(self._snapshot, info=parsers.parse_tv_info(reply.payload)))
            elif last == "tvsleep":
                self._update(replace(self._snapshot, power=PowerState.STANDBY))
        except ProtocolError:
            return  # a malformed push must not corrupt the snapshot

    def _update(self, snapshot: Snapshot) -> None:
        if snapshot == self._snapshot:
            return
        self._snapshot = snapshot
        for listener in self._listeners:
            listener(snapshot)
