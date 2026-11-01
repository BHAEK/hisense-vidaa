from vidaa_tv.protocol.topics import Action, Service, command_topic, mobile_filter


def test_command_topic_uses_owning_service() -> None:
    assert (
        command_topic("AA$vidaa_common", Action.SEND_KEY)
        == "/remoteapp/tv/remote_service/AA$vidaa_common/actions/sendkey"
    )
    assert command_topic("c", Action.GET_VOLUME).startswith("/remoteapp/tv/platform_service/")
    assert command_topic("c", Action.SOURCE_LIST).startswith("/remoteapp/tv/ui_service/")


def test_every_action_has_a_service() -> None:
    assert all(isinstance(action.service, Service) for action in Action)


def test_mobile_filter_covers_client_and_broadcast() -> None:
    assert mobile_filter("c") == ("/remoteapp/mobile/c/#", "/remoteapp/mobile/broadcast/#")
