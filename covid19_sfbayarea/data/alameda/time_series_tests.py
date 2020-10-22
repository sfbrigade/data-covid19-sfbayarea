from datetime import datetime
from typing import Any, Dict, List
from .time_series_tests_total import TimeSeriesTestsTotal
from .time_series_tests_percent import TimeSeriesTestsPercent

class TimeSeriesTests():
    def get_data(self) -> List[Dict[str, Any]]:
        total_tests = dict(TimeSeriesTestsTotal().get_data()[1:])
        percent_positive_tests = dict(TimeSeriesTestsPercent().get_data()[1:])
        self._assert_total_and_percent_cases_count_matches(total_tests, percent_positive_tests)

        return [{
            'date': self._timestamp_to_date(timestamp),
            'tests': total_tests[timestamp],
            'pending': -1, # we don't have data for this
            'cumul_tests': -1, # tests are a rolling 7-day average, so cumulative results don't add up
            'cumul_pend': -1,
            'cumul_pos': -1,
            'cumul_neg': -1,
            'cumul_pend': -1,
            **self._positive_and_negative_tests(total_tests[timestamp], percent_positive_tests[timestamp])
        } for timestamp in total_tests.keys()]


    def _positive_and_negative_tests(self, total_tests: int, percent_positive_tests: int) -> Dict[str, int]:
        positive_tests = round(total_tests * percent_positive_tests / 100)
        negative_tests = total_tests - positive_tests
        return { 'positive': positive_tests, 'negative': negative_tests }

    def _timestamp_to_date(self, timestamp_in_milliseconds: int) -> str:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _assert_total_and_percent_cases_count_matches(self, daily_cases: Dict[int, int], cumulative_cases: Dict[int, int]) -> None:
        if daily_cases.keys() != cumulative_cases.keys():
            raise(ValueError('The cumulative and daily cases do not have the same timestamps!'))
