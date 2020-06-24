import re
from bs4.element import Tag
from datetime import datetime
from typing import Dict, List, Any

from assertions import Assertions
from charts import Charts

class TimeSeriesOld:
    """
    Time series data parser. Receives Selenium dashboard charts and returns a list of the data.
    """
    def __init__(self, charts: List[Tag]) -> None:
        self.assertions = Assertions()
        self.charts = charts

    def extract_data(self) -> List[Dict[str, int]]:
        cumulative_cases = self.__parse_labels(self.charts[Charts.CUMULATIVE_CASES], 'Total')
        daily_cases = self.__parse_labels(self.charts[Charts.DAILY_CASES], 'New')
        self.assertions.dates_match(cumulative_cases, daily_cases) # The logic below requires this to hold

        return [
            { 'date': daily_case['date'], 'cases': daily_case['cases'], 'cumul_cases': cumulative_case['cases']}
            for daily_case, cumulative_case in zip(daily_cases, cumulative_cases)
        ]

    def __parse_labels(self, chart: Tag, data_type: str) -> List[Dict[str, int]]:
        labels = chart.select(f'rect[aria-label~={data_type}][aria-label~=Cases]')
        return list(map(self.__parse_label, labels))

    def __parse_label(self, label: Tag) -> Dict[str, Any]:
        """
        Drop the first two words because it says Date then the day of the week.
        Drop the last word because it's an empty string.
        Format: Date <Day of Week>, <Month> <Day>, <Year>. <New/Total> Cases by Day <Case Count>.
        """
        label_words = re.split('\W+', label['aria-label'])[2:-1]
        raw_date = ' '.join(label_words[:3])
        date = datetime.strptime(raw_date, '%B %d %Y').strftime('%Y-%m-%d')
        case_count = int(label_words[-1])
        return { 'date': date, 'cases': case_count }
