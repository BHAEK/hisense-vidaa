import json

from vidaa_tv.models import PowerState
from vidaa_tv.protocol.reply import Reply
from vidaa_tv.tracker import Snapshot, StateTracker

STATE = "/remoteapp/mobile/broadcast/ui_service/state"
VOLUME = "/remoteapp/mobile/broadcast/platform_service/actions/volumechange"
SLEEP = "/remoteapp/mobile/broadcast/platform_service/actions/tvsleep"


def push(topic: str, payload: object) -> Reply:
    return Reply(topic, payload)


def test_starts_unknown() -> None:
    assert StateTracker().snapshot == Snapshot()


def test_live_tv_push_updates_channel_and_programme() -> None:
    tracker = StateTracker()
    tracker.apply(
        push(
            STATE,
            {
                "statetype": "livetv",
                "channel_num": "4",
                "progname": "News",
                "starttime": 100,
                "endtime": 200,
                "detail": "Daily news",
            },
        )
    )
    snap = tracker.snapshot
    assert snap.power is PowerState.ON
    assert snap.state is not None
    assert snap.state.channel_number == "4"
    assert snap.state.programme is not None
    assert (snap.state.programme.title, snap.state.programme.end) == ("News", 200)


def test_state_without_programme_has_none() -> None:
    tracker = StateTracker()
    tracker.apply(push(STATE, {"statetype": "livetv", "channel_num": "5", "progname": ""}))
    assert tracker.snapshot.state is not None
    assert tracker.snapshot.state.programme is None


def test_app_push_sets_app_name() -> None:
    tracker = StateTracker()
    tracker.apply(push(STATE, {"statetype": "app", "name": "youtube_kids", "url": "yk"}))
    assert tracker.snapshot.state is not None
    assert tracker.snapshot.state.app_name == "youtube_kids"


def test_volume_and_sleep() -> None:
    tracker = StateTracker()
    tracker.apply(push(VOLUME, json.loads('{"volume_type": 1, "volume_value": 12}')))
    assert tracker.snapshot.volume is not None
    assert tracker.snapshot.volume.level == 12
    tracker.apply(push(SLEEP, None))
    assert tracker.snapshot.power is PowerState.STANDBY
    tracker.mark_unreachable()
    assert tracker.snapshot.power is PowerState.OFF


def test_listener_called_only_on_change() -> None:
    tracker = StateTracker()
    seen: list[Snapshot] = []
    tracker.add_listener(seen.append)
    message = push(VOLUME, {"volume_type": 1, "volume_value": 12})
    tracker.apply(message)
    tracker.apply(message)
    assert len(seen) == 1


def test_malformed_push_is_ignored() -> None:
    tracker = StateTracker()
    tracker.apply(push(STATE, "garbage"))
    tracker.apply(push(VOLUME, {"volume_value": "loud"}))
    assert tracker.snapshot == Snapshot()


def test_capability_reply_fills_tv_info() -> None:
    tracker = StateTracker()
    tracker.apply(
        Reply(
            "/remoteapp/mobile/x/ui_service/data/capability",
            {
                "softwareVersion": "V1",
                "boardVersion": "MSD6886",
                "devicemsg": "65A_0001",
                "pvr": 0,
                "vendorBrand": "his",
            },
        )
    )
    info = tracker.snapshot.info
    assert info is not None
    assert (info.software_version, info.board, info.model_code) == ("V1", "MSD6886", "65A_0001")


def test_authentication_push_marks_the_identity_as_unpaired_until_reconnect() -> None:
    tracker = StateTracker()
    tracker.apply(Reply("/remoteapp/mobile/x/ui_service/data/authentication", None))
    assert tracker.snapshot.auth_required
    tracker.mark_unreachable()
    assert not tracker.snapshot.auth_required
