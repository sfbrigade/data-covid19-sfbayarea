import re
from typing import Dict, List, Tuple
from bs4.element import Tag

from assertions import Assertions
from charts import Charts

class CaseTotals:
    """
    Gets case totals and death totals grouped by:
    - Age
    - Race
    - Gender
    """
    def __init__(self, charts: List[Tag]) -> None:
        self.charts = charts
        # Match the sentence, get the numbers. The \w+ can be Cases or Deaths.
        self.label_regex = r'Age Group ([^\.]+)\. \w+ (\d+)\.'
        self.assertions = Assertions()


    def extract_data(self) -> Dict:
        return {
            'case_totals': {
                'age_group': self.__parse_case_data()
            },
            'death_totals': {
                'age_group': self.__parse_death_data()
            }
        }

    def __parse_case_data(self) -> Dict[str, int]:
        return self.__extract_labels(self.charts[Charts.CASE_DATA])

    def __parse_death_data(self) -> Dict[str, int]:
        return {
            f'Death_{label}': number for label, number in self.__extract_labels(self.charts[Charts.DEATH_DATA]).items()
        }

    def __extract_labels(self, chart: Tag) -> Dict[str, int]:
        labels = map(lambda rect: rect['aria-label'], chart.find_all('rect'))
        for label in labels:
            self.assertions.regex_match(self.label_regex, label, message='Age labels or cases missing.')

        return dict(map(self.__extract_numbers, labels))

    def __extract_numbers(self, label: str) -> Tuple[str, int]:
        matches = re.search(self.label_regex, label)
        age_group = self.__age_group_label(matches.group(1))
        count = int(matches.group(2))
        return (age_group, count)

    def __age_group_label(self, label: str) -> str:
        return {
            '0 to 19': 'Age_LT20',
            '20 to 29': 'Age_20_29',
            '30 to 39': 'Age_30_39',
            '49 to 49': 'Age_40_49',
            '50 to 59': 'Age_50_59',
            '60 to 69': 'Age_60_69',
            '70 to 79': 'Age_70_79',
            '80 to 89': 'Age_80_89',
            '90+': 'Age_90_Up',
            'Unknown': 'Unknown'
        }.get(label, label)
