#!/usr/bin/env python3
from typing import List, Dict
from datetime import datetime
from functools import reduce
import csv
import requests
import json

class CoronaDataFetcher:
    def __init__(self, url: str, csv_path: str) -> None:
        self.url = url
        self.csv_path = csv_path

    def run(self) -> None:
        """
        Puts together the other functions in this file to add new data from the
        specified URL to the specified CSV
        """
        self.results = []
        print(f'Fetching data from {self.url}')
        response_json = self.get_json()
        data_for_csv = self.transform_json_to_list(response_json)
        reduce(self.create_csv_row, data_for_csv, { 'cases': 0, 'deaths': 0 })
        self.write_csv()
        print(f'Updated {self.csv_path}:')

    def get_json(self) -> Dict:
        """
        Takes in a url string and returns a dict with San Francisco results
        """
        response = requests.get(self.url).content
        return json.loads(response)['San Francisco County, CA, USA']['dates']

    def write_csv(self) -> None:
        headers = [
            'date', 'time_updated', 'total_positive_cases', 'new_daily_cases',
            'total_deaths', 'new_daily_deaths', 'city', 'county', 'state'
        ]
        with open(self.csv_path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(headers)
            for result in self.results:
                csv_writer.writerow([result[header] for header in headers])

    def transform_json_to_list(self, data: Dict) -> List[dict]:
        """
        Takes in a dict and returns a list of dicts of each key-value pair, with
        the date now a value in each dict.
        """
        return [{ 'date': date, **cases } for date, cases in data.items()]

    def create_csv_row(self, previous_row: Dict, current_row: Dict) -> Dict:
        """
        Generates a new row in dict format and calculates the new cases and
        deaths for the new data. Designed to be used inside of a `reduce`.
        """
        new_row = {
            'date': self.reformat_date(current_row['date']),
            'time_updated': '09:00:00 AM',
            'total_positive_cases': current_row['cases'],
            'new_daily_cases': current_row['cases'] - previous_row['cases'],
            'total_deaths': current_row['deaths'],
            'new_daily_deaths': current_row['deaths'] - previous_row['deaths'],
            'city': 'San Francisco',
            'county': 'San Francisco',
            'state': 'CA'
        }
        self.results.append(new_row)
        return current_row

    def reformat_date(self, date: str) -> str:
        """
        Corona data scraper uses YYYY-MM-DD format, this converts it to
        MM/DD/YY
        """
        return datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%y')

sf_url = 'https://coronadatascraper.com/timeseries-byLocation.json'
sf_data = 'data/corona_data_scraper_sf.csv'
CoronaDataFetcher(url=sf_url, csv_path=sf_data).run()
