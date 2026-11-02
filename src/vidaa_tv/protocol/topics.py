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
    PICTURE_SETTING = "picturesetting"
    CHANGE_CHANNEL = "changechannel"
    CHANNEL_LIST = "channellist"
    GET_BOOKING_LIST = "getbookinglist"
    CUR_ALL_PROGRAM = "curallprogram"
    APP_VERSION = "appversion"
    GET_CHANNEL_LIST_INFO = "getchannellistinfo"
    GET_DEVICE_INFO = "getdeviceinfo"
    GET_TV_INFO = "gettvinfo"
    SCREEN_CAPTURE = "screencapture"
    UNINSTALL_APP = "uninstallapp"
    APP_CONNECT = "vidaa_app_connect"
    AUTHENTICATION_CODE = "authenticationcode"
    AUTHENTICATION_CODE_CLOSE = "authenticationcodeclose"

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
    Action.PICTURE_SETTING: Service.PLATFORM,
    Action.CHANGE_CHANNEL: Service.UI,
    Action.CHANNEL_LIST: Service.PLATFORM,
    Action.GET_BOOKING_LIST: Service.PLATFORM,
    Action.CUR_ALL_PROGRAM: Service.PLATFORM,
    Action.APP_VERSION: Service.UI,
    Action.GET_CHANNEL_LIST_INFO: Service.PLATFORM,
    Action.GET_DEVICE_INFO: Service.PLATFORM,
    Action.GET_TV_INFO: Service.PLATFORM,
    Action.SCREEN_CAPTURE: Service.PLATFORM,
    Action.UNINSTALL_APP: Service.UI,
    Action.APP_CONNECT: Service.UI,
    Action.AUTHENTICATION_CODE: Service.UI,
    Action.AUTHENTICATION_CODE_CLOSE: Service.UI,
}

BROADCAST_FILTER = "/remoteapp/mobile/broadcast/#"
BROADCAST_STATE_TOPIC = "/remoteapp/mobile/broadcast/ui_service/state"


def command_topic(client_id: str, action: Action, service: Service | None = None) -> str:
    """Topic a command must be published to.

    ``service`` overrides the action's default owner for the few actions that
    exist on more than one service (e.g. ``picturesetting``).
    """
    owner = service or action.service
    return f"/remoteapp/tv/{owner}/{client_id}/actions/{action}"


def mobile_filter(client_id: str) -> tuple[str, str]:
    """Subscription filters that cover every message the TV sends to this client."""
    return (f"/remoteapp/mobile/{client_id}/#", BROADCAST_FILTER)
