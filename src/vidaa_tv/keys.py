"""Remote control key identifiers.

Values follow the names used by the VIDAA remote service. The list is the
community-known subset and must be validated against the target firmware
(see docs/reverse-engineering/).
"""

from enum import StrEnum


class RemoteKey(StrEnum):
    POWER = "KEY_POWER"
    UP = "KEY_UP"
    DOWN = "KEY_DOWN"
    LEFT = "KEY_LEFT"
    RIGHT = "KEY_RIGHT"
    OK = "KEY_OK"
    BACK = "KEY_BACK"
    EXIT = "KEY_EXIT"
    MENU = "KEY_MENU"
    HOME = "KEY_HOME"
    VOLUME_UP = "KEY_VOLUMEUP"
    VOLUME_DOWN = "KEY_VOLUMEDOWN"
    MUTE = "KEY_MUTE"
    CHANNEL_UP = "KEY_CHANNELUP"
    CHANNEL_DOWN = "KEY_CHANNELDOWN"
    PLAY = "KEY_PLAY"
    PAUSE = "KEY_PAUSE"
    STOP = "KEY_STOP"
    REWIND = "KEY_REWIND"
    FAST_FORWARD = "KEY_FAST_FORWARD"
    SUBTITLE = "KEY_SUBTITLE"
