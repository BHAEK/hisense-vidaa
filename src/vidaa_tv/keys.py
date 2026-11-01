"""Remote control key identifiers.

Values are the raw names accepted by the ``remote_service/sendkey`` action.
They come from community protocol analysis and must be validated against the
target firmware (see docs/reverse-engineering/).
"""

from enum import StrEnum


class RemoteKey(StrEnum):
    POWER = "KEY_POWER"

    # Navigation
    UP = "KEY_UP"
    DOWN = "KEY_DOWN"
    LEFT = "KEY_LEFT"
    RIGHT = "KEY_RIGHT"
    OK = "KEY_OK"
    BACK = "KEY_RETURNS"
    EXIT = "KEY_EXIT"
    MENU = "KEY_MENU"
    HOME = "KEY_HOME"

    # Volume and audio
    VOLUME_UP = "KEY_VOLUMEUP"
    VOLUME_DOWN = "KEY_VOLUMEDOWN"
    MUTE = "KEY_MUTE"

    # Channels
    CHANNEL_UP = "KEY_CHANNELUP"
    CHANNEL_DOWN = "KEY_CHANNELDOWN"

    # Playback (the firmware names rewind "KEY_BACK" and fast-forward "KEY_FORWARDS")
    PLAY = "KEY_PLAY"
    PAUSE = "KEY_PAUSE"
    STOP = "KEY_STOP"
    REWIND = "KEY_BACK"
    FAST_FORWARD = "KEY_FORWARDS"

    # Digits
    DIGIT_0 = "KEY_0"
    DIGIT_1 = "KEY_1"
    DIGIT_2 = "KEY_2"
    DIGIT_3 = "KEY_3"
    DIGIT_4 = "KEY_4"
    DIGIT_5 = "KEY_5"
    DIGIT_6 = "KEY_6"
    DIGIT_7 = "KEY_7"
    DIGIT_8 = "KEY_8"
    DIGIT_9 = "KEY_9"

    # Colour buttons
    RED = "KEY_RED"
    GREEN = "KEY_GREEN"
    YELLOW = "KEY_YELLOW"
    BLUE = "KEY_BLUE"
