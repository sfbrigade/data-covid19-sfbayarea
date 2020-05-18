#!/usr/bin/env python3
import json
from typing import Dict, List
from collections import Counter
from data_scrapers.utils import get_data_model, SocrataApi

def get_county() -> Dict:
    """ Main method for populating county data.json """

    # Load data model template into a local dictionary called 'out'.
    out = get_data_model()
    # create a SanFranciscoApi instance
    session = SanFranciscoApi()
    # fetch metadata
    meta_from_source = session.get_notes()
    update_times = session.get_update_times()

    # populate headers
    out["name"] = "San Francisco County"
    out["source_url"] = "https://data.sfgov.org/stories/s/San-Francisco-COVID-19-Data-and-Reports/fjki-2fab"
    out["update_time"] = sorted(update_times)[0]  # get earliest update time
    out["meta_from_source"] = meta_from_source
    out["meta_from_baypd"] = "SF county only reports tests with positive or negative results, excluding pending tests. The following datapoints are not directly reported, and were calculated by BayPD using available data: cumulative cases, cumulative deaths, cumulative positive tests, cumulative negative tests, cumulative total tests."

    # get timeseries and demographic totals
    out["series"] = session.get_timeseries()
    demo_totals = session.get_demographics()
    out.update(demo_totals)

    return out


class SanFranciscoApi(SocrataApi):
    """
    Inherits from utils.SocratApi. Creates a session to query the resource ids.
    Re-keys and re-structures data to fit our data model.
    """

    def __init__(self):
        super().__init__('https://data.sfgov.org/')
        self.resource_ids = {'cases_deaths_transmission': 'tvq9-ec9w', 'age_gender': 'sunc-2t3k',
                             'race_eth': 'vqqm-nsqg', 'tests': 'nfpa-mg4g'}


    def request(self, resource_id, **kwargs):
        return super().request(f'{self.resource_url}{resource_id}', **kwargs)

    def get_notes(self) -> str:
        """
        Get 'description' field of metadata for all resources. Collect into one string,
        separated by 2 newlines.
        """
        meta_from_source = ''
        for v in self.resource_ids.values():
            url = f"{self.metadata_url}{v}.json"
            data = super().request(url)
            meta_from_source += data["description"] + '\n\n'
        return meta_from_source

    def get_update_times(self) -> List:
        """
        Return a list of update times for all resources.
        """
        update_times = []
        for v in self.resource_ids.values():
            url = f"{self.metadata_url}{v}.json"
            data = super().request(url)
            update_times.append(data["dataUpdatedAt"])
        return update_times

    def get_demographics(self) -> Dict:
        """
        Fetch cases by age, gender, race_eth. Fetch cases by transmission category
        Returns the dictionary value for {"cases_totals": {}, "death_totals":{}}.
        Note that SF does not provide death totals, so these datapoints will be -1.
        To crete a DataFrame from the dictionary, run 'pd.DataFrame(get_demographics())'
        """
        # copy dictionary structure of global 'out' dictionary to local variable
        demo_totals: Dict[str,Dict] = { "case_totals": dict(), "death_totals": dict() }
        demo_totals["case_totals"]["gender"] = self.get_gender_table()
        demo_totals["case_totals"]["age_group"] = self.get_age_table()
        demo_totals["case_totals"]["transmission_cat"] = self.get_transmission_table()
        demo_totals["case_totals"]["race_eth"] = self.get_race_eth_table()
        return demo_totals

    def get_timeseries(self) -> Dict[str,List[Dict]]:
        """
        Returns the dictionary value for "series": {"cases":[], "deaths":[], "tests":[]}.
        To create a DataFrame from this dictionary, run
        'pd.DataFrame(get_timeseries())'
        """
        out_series: Dict[str, List[Dict]] = {"cases": [], "deaths": [
        ], "tests": []}  # dictionary structure for time_series
        out_series["cases"] = self.get_cases_series()
        out_series["deaths"] = self.get_deaths_series()
        out_series["tests"] = self.get_tests_series()
        return out_series

    # Confirmed Cases and Deaths by Date and Transmission
    # Note that cumulative totals are not directly reported, we are summing over the daily reported numbers
    def get_cases_series(self) -> List[Dict]:
        """Get cases timeseries json, sum over transmision cat by date"""
        resource_id = self.resource_ids['cases_deaths_transmission']
        params = {'case_disposition': 'Confirmed',
                '$select': 'date,sum(case_count) as cases', '$group': 'date', '$order': 'date'}
        data = self.request(resource_id, params=params)
        # convert date from ISO string to 'yyyy-mm-dd'. convert number strings to int.
        # calculate daily cumulative
        cases_series = []
        cumul = 0
        for entry in data:
            entry["date"] = entry["date"][0:10]
            entry["cases"] = int(entry["cases"])
            cumul += entry["cases"]
            entry["cumul_cases"] = cumul
            cases_series.append(entry)
        return cases_series


    def get_deaths_series(self) -> List[Dict]:
        """Get  deaths timeseries, sum over transmision cat by date"""
        resource_id = self.resource_ids['cases_deaths_transmission']
        params = {'case_disposition': 'Death',
                '$select': 'date,sum(case_count) as deaths', '$group': 'date', '$order': 'date'}
        series = self.request(resource_id, params=params)
        death_series = []
        # convert date from ISO string to 'yyyy-mm-dd'. convert number strings to int.
        # calculate daily cumulative
        cumul = 0
        for entry in series:
            entry["date"] = entry["date"][0:10]
            entry["deaths"] = int(entry["deaths"])
            cumul += entry["deaths"]
            entry["cumul_deaths"] = cumul
            death_series.append(entry)
        return death_series

    # Daily count of tests with count of positive tests
    # Note that SF county does not include pending tests, and does not directly report negative tests or cumulative tests.
    def get_tests_series(self) -> List[Dict]:
        """Get tests by day, order by date ascending"""
        resource_id = self.resource_ids['tests']
        test_series = []
        params = {'$order': 'result_date'}
        series = self.request(resource_id, params=params)

        # parse source series into out series, calculating cumulative values
        # Counter is from the built-in `collections` module.
        totals:Counter = Counter()
        for entry in series:
            out_entry = dict(date=entry["result_date"][0:10],
                            tests=int(entry["tests"]),
                            positive=int(entry["pos"]))
            out_entry['negative'] = out_entry["tests"] - out_entry["positive"]
            totals.update(out_entry)
            out_entry.update(cumul_tests=totals['tests'],
                            cumul_pos=totals['positive'],
                            cumul_neg=totals['negative'])
            test_series.append(out_entry)
        return test_series

    def get_age_table(self) -> List[Dict]:
        """Get cases by age"""
        resource_id = self.resource_ids['age_gender']
        params = {'$select': 'age_group, sum(confirmed_cases)', '$order': 'age_group', '$group': 'age_group'}
        data = self.request(resource_id, params=params)
        age_table = []
        for entry in data:
            age_table.append(
                {entry["age_group"]: int(entry["sum_confirmed_cases"])})
        return age_table

    def get_gender_table(self) -> Dict:
        """Get cases by gender"""
        # Dict of source_label:target_label for re-keying.
        # Note: non cis genders not currently reported
        resource_id = self.resource_ids['age_gender']
        GENDER_KEYS = {"Female": "female", "Male": "male", "Unknown": "unknown"}
        params = {'$select': 'gender, sum(confirmed_cases)', '$group': 'gender'}
        data = self.request(resource_id, params=params)
        # re-key
        return {GENDER_KEYS[entry["gender"]]: entry["sum_confirmed_cases"]
                for entry in data}

    def get_transmission_table(self) -> Dict:
        """Get cases by transmission category"""
        resource_id = self.resource_ids['cases_deaths_transmission']
        # Dict of source_label:target_label for re-keying
        TRANSMISSION_KEYS = {"Community": "community",
                            "From Contact": "from_contact", "Unknown": "unknown"}
        params = { '$select': 'transmission_category, sum(case_count)', '$group': 'transmission_category'}
        data = self.request(resource_id, params=params)
        # re-key
        transmission_data = { TRANSMISSION_KEYS[ entry["transmission_category"] ]: int(entry["sum_case_count"]) for entry in data}
        return transmission_data

    # Confirmed cases by race and ethnicity
    # Note that SF reporting race x ethnicty requires special handling
    # "In the race/ethnicity data shown below, the "Other” category
    # includes those who identified as Other or with a race/ethnicity that does not fit the choices collected.
    # The “Unknown” includes individuals who did not report a race/ethnicity to their provider,
    # could not be contacted, or declined to answer."

    def get_race_eth_table(self) -> Dict:
        """ fetch race x ethnicity data """
        resource_id = self.resource_ids["race_eth"]
        # Dict of source_label:target_label for re-keying.
        # Note: Native_Amer not currently reported
        RACE_ETH_KEYS = {'Hispanic or Latino': 'Latinx_or_Hispanic', 'Asian': 'Asian', 'Black or African American': 'African_Amer', 'White': 'White',
                        'Native Hawaiian or Other Pacific Islander': 'Pacific_Islander', 'Native American': 'Native_Amer', 'Multiple Race': 'Multiple_Race', 'Other': 'Other', 'Unknown': 'Unknown'}
        data = self.request(resource_id)
        # re-key and aggregate to flatten race x ethnicity
        # initalize all categories to 0 for aggregating
        race_eth_data: Dict[str, int] = {v: 0 for v in RACE_ETH_KEYS.values()}

        for item in data:  # iterate through all race x ethnicity objects
            cases = int(item["confirmed_cases"])
            # if race not  reported, assign "Unknown"
            race = item.get('race', 'Unknown')
            # if ethnicity not reported, assign "Unknown"
            ethnicity = item.get('ethnicity', 'Unknown')

            # add cases where BOTH race and ethnicity are Unknown or not reported to our "Unknown"
            if race == 'Unknown' and ethnicity == 'Unknown':
                race_eth_data['Unknown'] += cases

            #per SF county, include Unknown Race/Not Hispanic or Latino ethnicity in Unknown
            if race == 'Unknown' and ethnicity == 'Not Hispanic or Latino':
                race_eth_data['Unknown'] += cases

            # sum over 'Hispanic or Latino', all races
            if ethnicity == "Hispanic or Latino":
                race_eth_data["Latinx_or_Hispanic"] += cases

            # sum over all known races
            if race != "Unknown":
                if race == "Other" and ethnicity != "Hispanic or Latino":  # exclude Other/Hispanic Latino from Other
                    race_eth_data["Other"] += cases
                if race == "White" and ethnicity == "Hispanic or Latino":  # exclude White/Hispanic Latino from White
                    continue
                else:  # look up this item's re-key
                    re_key = RACE_ETH_KEYS[item["race"]]
                    race_eth_data[re_key] += cases

        return race_eth_data

if __name__ == '__main__':
    """ When run as a script, logs data to console"""
    print(json.dumps(get_county(), indent=4))
