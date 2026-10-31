from vidaa_tv import RemoteKey


def test_remote_keys_use_vidaa_prefix() -> None:
    assert all(key.value.startswith("KEY_") for key in RemoteKey)


def test_remote_keys_are_unique() -> None:
    values = [key.value for key in RemoteKey]
    assert len(values) == len(set(values))
