import json
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from assertions import Assertions
from case_totals import CaseTotals
from time_series import TimeSeries

class SanMateoCounty:
    """
    San Mateo Data Scraper

    Starts on a page with multiple dashboards, progresses to a single dashboard
    using BeautifulSoup, then uses Selenium to read the page.

    Currently gets data by age group and timeseries.
    TODO: There is a second dashboard with testing data.
    TODO: There is gender data on this dashboard.
    TODO: There is ethnicity data on this dashboard.
    """
    LANDING_PAGE = 'https://www.smchealth.org/post/san-mateo-county-covid-19-data-1'

    def __init__(self) -> None:
        self.assertions = Assertions()
        with open('./data_models/data_model.json') as template_json:
            self.output = json.load(template_json)
        self.output['name'] = 'San Mateo County'
        self.output['source_url'] = self.LANDING_PAGE


    def get_county(self) -> Dict:
        landing_page_soup = self.__get_landing_page()
        iframes = landing_page_soup('iframe')
        self.assertions.iframes_match(iframes)

        cases_dashboard_url = iframes[0]['src']
        cases_dashboard_charts = self.__get_charts_with_selenium(cases_dashboard_url)
        self.assertions.charts_match(cases_dashboard_charts)

        self.output.update(CaseTotals(cases_dashboard_charts).extract_data())
        self.output['series'] = TimeSeries(cases_dashboard_charts).extract_data()
        return self.output

    def __get_landing_page(self) -> BeautifulSoup:
        response = requests.get(self.LANDING_PAGE)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html5lib')

    def __get_charts_with_selenium(self, url: str) -> List[Tag]:
        driver = webdriver.Firefox()
        driver.get(url)
        WebDriverWait(driver, 30).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'setFocusRing'), '90+')
        )

        return BeautifulSoup(driver.page_source, 'html5lib').find_all('svg', { 'class': 'svgScrollable' })

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(SanMateoCounty().get_county(), indent=4))
