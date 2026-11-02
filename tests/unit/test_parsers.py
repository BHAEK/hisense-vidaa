import pytest

from vidaa_tv.errors import ProtocolError
from vidaa_tv.protocol import parsers
from vidaa_tv.protocol.reply import Reply


def reply(payload: object) -> Reply:
    return Reply("t", payload)


def test_parse_tv_state() -> None:
    state = parsers.parse_tv_state(
        {"statetype": "sourceswitch", "sourceid": "HDMI2", "sourcename": "HDMI2", "is_signal": 1}
    )
    assert (state.kind, state.source_id, state.has_signal) == ("sourceswitch", "HDMI2", True)


def test_parse_volume_accepts_string_numbers_and_flags_arc() -> None:
    volume = parsers.parse_volume({"volume_type": "1", "volume_value": "13"})
    assert volume.level == 13
    assert volume.is_arc


def test_parse_volume_rejects_garbage() -> None:
    with pytest.raises(ProtocolError):
        parsers.parse_volume({"volume_value": "loud"})


def test_parse_sources_from_list_and_wrapped_list() -> None:
    raw = [{"sourceid": "4", "sourcename": "HDMI1", "displayname": "HDMI 1", "is_signal": "0"}]
    expected = parsers.parse_sources(raw)
    assert expected[0].id == "4"
    assert expected[0].display_name == "HDMI 1"
    assert expected[0].has_signal is False
    assert parsers.parse_sources({"sourcelist": raw}) == expected


def test_parse_apps_skips_entries_without_url() -> None:
    apps = parsers.parse_apps(
        [
            {"url": "netflix", "name": "Netflix", "appId": "1", "urlType": 37, "storeType": 0},
            {"name": "broken"},
        ]
    )
    assert [app.name for app in apps] == ["Netflix"]


def test_matchers_distinguish_replies() -> None:
    assert parsers.is_tv_state(reply({"statetype": "x"}))
    assert not parsers.is_tv_state(reply({"volume_value": 1}))
    assert parsers.is_volume(reply({"volume_value": 1}))
    assert parsers.is_app_list(reply([{"url": "a"}]))
    assert not parsers.is_app_list(reply([{"sourcename": "TV"}]))
    assert parsers.is_source_list(reply([{"sourcename": "TV"}]))
    assert not parsers.is_source_list(reply(None))
