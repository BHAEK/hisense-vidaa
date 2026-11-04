from vidaa_tv.models import Programme


def test_programme_duration_and_position() -> None:
    programme = Programme("News", start=1000, end=1600)
    assert programme.duration == 600
    assert programme.position(1250) == 250
    assert programme.position(900) == 0  # before the start
    assert programme.position(5000) == 600  # after the end


def test_programme_without_times_has_no_duration() -> None:
    assert Programme("News").duration is None
    assert Programme("News").position(10) is None
    assert Programme("News", start=10, end=5).duration is None
