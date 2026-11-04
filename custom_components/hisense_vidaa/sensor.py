"""Sensors: what the TV is showing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from vidaa_tv import PowerState
from vidaa_tv.tracker import Snapshot

from . import VidaaConfigEntry
from .entity import VidaaEntity


@dataclass(frozen=True, kw_only=True)
class VidaaSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Snapshot], Any]


def _current_source(snapshot: Snapshot) -> str | None:
    state = snapshot.state
    if state is None:
        return None
    if state.kind == "livetv":
        return "TV"
    return state.app_name or state.source_name


def _programme_end(snapshot: Snapshot) -> datetime | None:
    programme = snapshot.state.programme if snapshot.state else None
    if programme is None or programme.end is None:
        return None
    return datetime.fromtimestamp(programme.end, tz=UTC)


SENSORS: tuple[VidaaSensorDescription, ...] = (
    VidaaSensorDescription(
        key="source",
        translation_key="source",
        icon="mdi:video-input-hdmi",
        value_fn=_current_source,
    ),
    VidaaSensorDescription(
        key="channel",
        translation_key="channel",
        icon="mdi:television-classic",
        value_fn=lambda s: s.state.channel_name if s.state else None,
    ),
    VidaaSensorDescription(
        key="programme",
        translation_key="programme",
        icon="mdi:television-play",
        value_fn=lambda s: s.state.programme.title if s.state and s.state.programme else None,
    ),
    VidaaSensorDescription(
        key="programme_end",
        translation_key="programme_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_programme_end,
    ),
    VidaaSensorDescription(
        key="volume",
        translation_key="volume",
        icon="mdi:volume-high",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.volume.level if s.volume else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: VidaaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(VidaaSensor(entry, description) for description in SENSORS)


class VidaaSensor(VidaaEntity, SensorEntity):
    entity_description: VidaaSensorDescription

    def __init__(self, entry: VidaaConfigEntry, description: VidaaSensorDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        return self._client.snapshot.power is PowerState.ON

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._client.snapshot)
