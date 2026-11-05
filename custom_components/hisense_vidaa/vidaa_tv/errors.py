"""Exception hierarchy. Every error raised by the library derives from VidaaError."""


class VidaaError(Exception):
    """Base class for all library errors."""


class ConnectionFailedError(VidaaError):
    """The TV could not be reached or the connection was lost."""


class AuthenticationError(VidaaError):
    """Pairing or token validation was rejected by the TV."""


class ProtocolError(VidaaError):
    """The TV sent a message that does not match the expected protocol."""


class UnsupportedFeatureError(VidaaError):
    """The connected firmware does not expose the requested feature."""
