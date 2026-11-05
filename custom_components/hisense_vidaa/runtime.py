"""Runtime data kept for each config entry.

Kept apart from ``__init__`` so platforms and entities can import it without importing the
integration module (no circular import).
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .catalog import VidaaCatalog
from .vidaa_tv import VidaaClient


@dataclass
class VidaaData:
    client: VidaaClient
    catalog: VidaaCatalog


VidaaConfigEntry = ConfigEntry[VidaaData]
