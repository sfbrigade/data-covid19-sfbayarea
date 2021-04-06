from datetime import datetime, timezone
import dateutil.tz
import pytest
from covid19_sfbayarea.utils import parse_datetime


class TestParseDatetime:
    def test_iso8601_dates(self) -> None:
        result = parse_datetime('2021-09-10T00:03:18Z')
        assert result == datetime(2021, 9, 10, 0, 3, 18, tzinfo=timezone.utc)

    def test_always_sets_a_timezone(self) -> None:
        result = parse_datetime('2021-09-10T00:03:18')
        assert result.tzinfo is not None

    def test_default_timezone_is_used(self) -> None:
        default_tz = dateutil.tz.gettz('America/Chicago')
        result = parse_datetime('2021-09-10T00:03:18', timezone=default_tz)
        assert result.tzinfo is default_tz

    def test_default_timezone_is_ignored_if_date_specifies_one(self) -> None:
        default_tz = dateutil.tz.gettz('America/Chicago')
        result = parse_datetime('2021-09-10T00:03:18Z', timezone=default_tz)
        result_tz = result.tzinfo
        assert result_tz is not None
        assert result_tz.utcoffset(result) == timezone.utc.utcoffset(result)

    def test_raises_for_unlikely_dates(self) -> None:
        with pytest.raises(ValueError):
            parse_datetime('2010-09-10T00:00:00Z')

        with pytest.raises(ValueError):
            parse_datetime('2030-09-10T00:00:00Z')

    def test_corrects_century(self) -> None:
        result = parse_datetime('1921-09-10T00:00:00Z')
        assert result == datetime(2021, 9, 10, tzinfo=timezone.utc)

    def test_does_not_corrects_century_based_on_args(self) -> None:
        with pytest.raises(ValueError):
            parse_datetime('1921-09-10T00:00:00Z', correct_century=False)
