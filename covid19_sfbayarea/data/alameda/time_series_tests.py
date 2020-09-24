from datetime import datetime
from typing import Any, Dict, List, cast
from .power_bi_querier import PowerBiQuerier
from .time_series_tests_total import TimeSeriesTestsTotal
from .time_series_tests_percent import TimeSeriesTestsPercent

class TimeSeriesTests():
    def get_data(self) -> List[Dict[str, Any]]:
        total_tests = dict(TimeSeriesTestsTotal().get_data()[1:])
        percent_positive_tests = dict(TimeSeriesTestsPercent().get_data()[1:])
        self._assert_total_and_percent_cases_count_matches(total_tests, percent_positive_tests)

        results = [{
            'date': self._timestamp_to_date(timestamp),
            'tests': total_tests[timestamp],
            'pending': -1, # we don't have data for this
            'cumul_pend': -1, # no data for this
            **self._positive_and_negative_tests(total_tests[timestamp], percent_positive_tests[timestamp])
        } for timestamp in total_tests.keys()]
        self._add_cumulative_data(results)
        return results


    def _positive_and_negative_tests(self, total_tests: int, percent_positive_tests: int) -> Dict[str, int]:
        positive_tests = round(total_tests * percent_positive_tests / 100)
        negative_tests = total_tests - positive_tests
        return { 'positive': positive_tests, 'negative': negative_tests }

    def _timestamp_to_date(self, timestamp_in_milliseconds: int) -> str:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _assert_total_and_percent_cases_count_matches(self, daily_cases: Dict[int, int], cumulative_cases: Dict[int, int]) -> None:
        if daily_cases.keys() != cumulative_cases.keys():
            raise(ValueError('The cumulative and daily cases do not have the same timestamps!'))

    def _add_cumulative_data(self, results: List[Dict[str, Any]]) -> None:
        running_totals = { 'cumul_tests': 0, 'cumul_pos': 0, 'cumul_neg': 0, 'cumul_pend': 0 }
        for result in results:
            running_totals['cumul_tests'] += result['tests']
            running_totals['cumul_pos'] += result['positive']
            running_totals['cumul_neg'] += result['negative']
            result.update(running_totals)
