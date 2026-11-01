from vidaa_tv.protocol.auth import dynamic_credentials, static_credentials


def test_static_credentials() -> None:
    creds = static_credentials("AA:BB:CC:DD:EE:FF")
    assert creds.client_id == "AA:BB:CC:DD:EE:FF$vidaa_common"
    assert creds.username == "hisenseservice"
    assert creds.password == "multimqttservice"


def test_dynamic_credentials_match_published_vector() -> None:
    creds = dynamic_credentials("56:b8:88:4e:f7:19", timestamp=1766974704)
    assert creds.client_id == "56:b8:88:4e:f7:19$his$256DBF_vidaacommon_001"
    assert creds.username == "his$6239759786168176024"
    assert creds.password == "C3BA44782E18ABF4892AC44D79A622D2"
