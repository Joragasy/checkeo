import pytest

from checkeo.core.gtfs_time import day_offset, format_display, format_hhmm, parse_gtfs_time, parse_hhmm


def test_parse_standard_time():
    assert parse_gtfs_time("07:05:30") == 7 * 3600 + 5 * 60 + 30


def test_parse_time_beyond_midnight():
    assert parse_gtfs_time("24:25:00") == 24 * 3600 + 25 * 60
    assert parse_gtfs_time("25:10:00") == 90600


def test_parse_single_digit_hour_and_blank():
    assert parse_gtfs_time(" 7:00:00 ") == 7 * 3600
    assert parse_gtfs_time("") is None
    assert parse_gtfs_time(None) is None


@pytest.mark.parametrize("bad", ["7:00", "07:60:00", "aa:00:00"])
def test_parse_invalid(bad):
    with pytest.raises(ValueError):
        parse_gtfs_time(bad)


def test_format_beyond_midnight():
    s = parse_gtfs_time("24:40:00")
    assert format_hhmm(s) == "00:40"
    assert day_offset(s) == 1
    assert format_display(s) == "00:40 (+1)"
    assert format_display(parse_gtfs_time("23:59:00")) == "23:59"


def test_parse_hhmm():
    assert parse_hhmm("09:00") == 9 * 3600
    assert parse_hhmm("9h30") == 9 * 3600 + 30 * 60
    assert parse_hhmm("18h") == 18 * 3600
    with pytest.raises(ValueError):
        parse_hhmm("9:75")
