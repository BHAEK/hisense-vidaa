"""Turn raw reply payloads into models, and recognise which reply is which.

Every ``is_*`` function is a reply matcher usable with ``Session.request``; every
``parse_*`` function converts an already matched payload. Parsers are tolerant
about value types because firmware revisions disagree (numbers as strings, etc.).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..errors import ProtocolError
from ..models import (
    App,
    Channel,
    ChannelList,
    Programme,
    Source,
    TvInfo,
    TvState,
    Volume,
)
from .reply import Reply

_SOURCE_LIST_KEYS = ("sources", "sourcelist", "source_list")


def _as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"field {field!r} is not a number: {value!r}") from exc


def _as_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    return str(value).lower() not in {"0", "false"}


def _items(payload: Any, keys: Iterable[str]) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in keys:
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise ProtocolError(f"expected a list payload, got {type(payload).__name__}")
    return [item for item in payload if isinstance(item, dict)]


# ----------------------------------------------------------------- matchers
def is_tv_state(reply: Reply) -> bool:
    return isinstance(reply.payload, dict) and "statetype" in reply.payload


def is_volume(reply: Reply) -> bool:
    return isinstance(reply.payload, dict) and "volume_value" in reply.payload


def is_source_list(reply: Reply) -> bool:
    payload = reply.payload
    if isinstance(payload, list):
        return any(isinstance(item, dict) and "sourcename" in item for item in payload)
    return isinstance(payload, dict) and any(key in payload for key in _SOURCE_LIST_KEYS)


def is_app_list(reply: Reply) -> bool:
    payload = reply.payload
    return isinstance(payload, list) and any(
        isinstance(item, dict) and "url" in item for item in payload
    )


# ------------------------------------------------------------------ parsers
def _programme(payload: dict[str, Any]) -> Programme | None:
    title = str(payload.get("progname") or "")
    if not title:
        return None
    return Programme(
        title=title,
        description=str(payload.get("detail") or ""),
        start=_optional_int(payload.get("starttime")),
        end=_optional_int(payload.get("endtime")),
    )


def _optional_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number or None


def parse_tv_state(payload: Any) -> TvState:
    if not isinstance(payload, dict) or "statetype" not in payload:
        raise ProtocolError("not a TV state payload")
    source_id = payload.get("sourceid")
    return TvState(
        kind=str(payload["statetype"]),
        source_id=None if source_id is None else str(source_id),
        source_name=payload.get("sourcename") or payload.get("displayname"),
        has_signal=_as_bool(payload.get("is_signal")),
        channel_number=_optional_str(payload.get("channel_num")),
        channel_name=_optional_str(payload.get("channel_name")),
        channel_param=_optional_str(payload.get("channel_param")),
        programme=_programme(payload),
        app_name=_optional_str(payload.get("name")),
        app_url=_optional_str(payload.get("url")),
    )


def _optional_str(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


MUTE_VOLUME_TYPE = 2


def parse_mute(payload: Any) -> bool | None:
    """The mute state carried by a volume message of type 2, or ``None`` for any other type.

    The vendor app treats ``volume_type`` 2 as "mute state" (``volume_value`` 1 = muted)
    and the other types as audio levels, so a mute message must never be read as a level.
    """
    if not isinstance(payload, dict) or "volume_value" not in payload:
        return None
    if _as_int(payload.get("volume_type", 0), "volume_type") != MUTE_VOLUME_TYPE:
        return None
    return _as_int(payload["volume_value"], "volume_value") == 1


def parse_volume(payload: Any) -> Volume:
    if not isinstance(payload, dict) or "volume_value" not in payload:
        raise ProtocolError("not a volume payload")
    return Volume(
        level=_as_int(payload["volume_value"], "volume_value"),
        output_type=_as_int(payload.get("volume_type", 0), "volume_type"),
    )


def parse_sources(payload: Any) -> list[Source]:
    sources = []
    for item in _items(payload, _SOURCE_LIST_KEYS):
        name = str(item.get("sourcename", ""))
        sources.append(
            Source(
                id=str(item.get("sourceid", "")),
                name=name,
                display_name=str(item.get("displayname") or name),
                has_signal=_as_bool(item.get("is_signal")),
            )
        )
    return sources


def parse_apps(payload: Any) -> list[App]:
    return [
        App(
            id=str(item.get("appId", "")),
            name=str(item.get("name", "")),
            url=str(item["url"]),
            url_type=_as_int(item.get("urlType", 37), "urlType"),
            store_type=_as_int(item.get("storeType", 0), "storeType"),
        )
        for item in _items(payload, ())
        if "url" in item
    ]


def is_channel_list_info(reply: Reply) -> bool:
    payload = reply.payload
    return isinstance(payload, list) and any(
        isinstance(item, dict) and "list_para" in item for item in payload
    )


def is_channel_list(reply: Reply) -> bool:
    return isinstance(reply.payload, dict) and isinstance(reply.payload.get("list"), list)


def parse_channel_lists(payload: Any) -> list[ChannelList]:
    return [
        ChannelList(
            id=str(item["list_para"]),
            name=str(item.get("list_name", "")),
            version=str(item.get("list_version", "")),
        )
        for item in _items(payload, ())
        if "list_para" in item
    ]


def parse_channels(payload: Any) -> list[Channel]:
    if not isinstance(payload, dict):
        raise ProtocolError("not a channel list payload")
    return [
        Channel(
            number=str(item.get("channel_num", "")),
            name=str(item.get("channel_name", "")),
            param=str(item["channel_param"]),
        )
        for item in _items(payload.get("list"), ())
        if "channel_param" in item
    ]


def is_capability(reply: Reply) -> bool:
    return isinstance(reply.payload, dict) and "softwareVersion" in reply.payload


def parse_tv_info(payload: Any) -> TvInfo:
    if not isinstance(payload, dict) or "softwareVersion" not in payload:
        raise ProtocolError("not a capability payload")
    return TvInfo(
        software_version=str(payload.get("softwareVersion", "")),
        board=str(payload.get("boardVersion", "")),
        chip=str(payload.get("chipplatform", "")),
        model_code=str(payload.get("devicemsg", "")),
        brand=str(payload.get("vendorBrand", "")),
        device_id=str(payload.get("uniqueDeviceId", "")),
        has_pvr=bool(payload.get("pvr", 0)),
    )
