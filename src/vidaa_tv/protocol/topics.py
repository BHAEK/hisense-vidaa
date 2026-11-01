"""Topic naming rules of the VIDAA remote service.

Commands are published to ``/remoteapp/tv/<service>/<client>/actions/<action>``;
replies and pushes arrive on ``/remoteapp/mobile/<client>/<service>/data/<type>``.
"""

from __future__ import annotations

from enum import StrEnum


class Service(StrEnum):
    REMOTE = "remote_service"
    UI = "ui_service"
    PLATFORM = "platform_service"


class Action(StrEnum):
    """Command actions, each bound to the service that owns it."""

    SEND_KEY = "sendkey"
    GET_VOLUME = "getvolume"
    CHANGE_VOLUME = "changevolume"
    GET_TV_STATE = "gettvstate"
    SOURCE_LIST = "sourcelist"
    CHANGE_SOURCE = "changesource"
    APP_LIST = "applist"
    LAUNCH_APP = "launchapp"
    CAPABILITY = "capability"
    APP_CONNECT = "vidaa_app_connect"
    AUTHENTICATION_CODE = "authenticationcode"

    @property
    def service(self) -> Service:
        return _ACTION_SERVICE[self]


_ACTION_SERVICE: dict[Action, Service] = {
    Action.SEND_KEY: Service.REMOTE,
    Action.GET_VOLUME: Service.PLATFORM,
    Action.CHANGE_VOLUME: Service.PLATFORM,
    Action.GET_TV_STATE: Service.UI,
    Action.SOURCE_LIST: Service.UI,
    Action.CHANGE_SOURCE: Service.UI,
    Action.APP_LIST: Service.UI,
    Action.LAUNCH_APP: Service.UI,
    Action.CAPABILITY: Service.UI,
    Action.APP_CONNECT: Service.UI,
    Action.AUTHENTICATION_CODE: Service.UI,
}

BROADCAST_FILTER = "/remoteapp/mobile/broadcast/#"
BROADCAST_STATE_TOPIC = "/remoteapp/mobile/broadcast/ui_service/state"


def command_topic(client_id: str, action: Action) -> str:
    """Topic a command must be published to."""
    return f"/remoteapp/tv/{action.service}/{client_id}/actions/{action}"


def mobile_filter(client_id: str) -> tuple[str, str]:
    """Subscription filters that cover every message the TV sends to this client."""
    return (f"/remoteapp/mobile/{client_id}/#", BROADCAST_FILTER)
