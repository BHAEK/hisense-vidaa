import pytest

from vidaa_tv.errors import ProtocolError
from vidaa_tv.protocol import codec


def test_encode_variants() -> None:
    assert codec.encode(None) == b""
    assert codec.encode("KEY_POWER") == b"KEY_POWER"
    assert codec.encode({"sourceid": "1", "sourcename": "HDMI1"}) == (
        b'{"sourceid":"1","sourcename":"HDMI1"}'
    )


def test_decode_empty_is_none() -> None:
    assert codec.decode(b"") is None
    assert codec.decode(b"  ") is None


def test_decode_json() -> None:
    assert codec.decode(b'{"is_signal":1}') == {"is_signal": 1}


def test_decode_invalid_raises_protocol_error() -> None:
    with pytest.raises(ProtocolError):
        codec.decode(b"not json")
