import pytest

from vidaa_tv import (
    AuthenticationError,
    ConnectionFailedError,
    ProtocolError,
    UnsupportedFeatureError,
    VidaaError,
)


@pytest.mark.parametrize(
    "error",
    [AuthenticationError, ConnectionFailedError, ProtocolError, UnsupportedFeatureError],
)
def test_all_errors_derive_from_base(error: type[Exception]) -> None:
    assert issubclass(error, VidaaError)
