#!/usr/bin/env python3
import json
from typing import Dict, List, Any
from collections import Counter
from data_scrapers.utils import get_data_model, SocrataApi

def get_county() -> Dict:
    """ Main method for populating county data.json """
    # TODO: Add deaths data when it is available through the api.
    # TODO: In get_race_eth_table(), update code when SF provides a race label for the Native American datapoint.

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
    out["meta_from_baypd"] = "SF county only reports tests with positive or negative results, excluding pending tests. The following datapoints are not directly reported, and were calculated by BayPD using available data: cumulative cases, cumulative deaths, cumulative positive tests, cumulative negative tests, cumulative total tests. \n\n Race and Ethnicity: individuals are assigned to just one category. Individuals identified as 'Hispanic or Latino' are assigned 'Latinx_or_Hispanic'. Individuals identified as 'Not Hispanic or Latino' are assigned to their race identification. Due to an error in the source data, it appears that Native American datapoint is not currently assigned a race category in the source data. BayPD assigns those cases without race category, and with ethnicity = 'Unknown', as 'Native American' race. BayPD is not currently reporting deaths by demographic groups. These will be made available when the data is accessible."

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

    def get_notes(self) -> str:
        """
        Get 'description' field of metadata for all resources. Collect into one string,
        separated by 2 newlines.
        """
        meta_from_source = ''
        for v in self.resource_ids.values():
            data = self.metadata(v)
            meta_from_source += data["description"] + '\n\n'
        return meta_from_source

    def get_update_times(self) -> List:
        """
        Return a list of update times for all resources.
        """
        update_times = []
        for v in self.resource_ids.values():
            data = self.metadata(v)
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
        data = self.resource(resource_id, params=params)
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
        series = self.resource(resource_id, params=params)
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
        series = self.resource(resource_id, params=params)

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
        # Dict of target_label:source_label for lookups
        AGE_KEYS = {"18_and_under": "under 18", "18_to_30": "18-30", "31_to_40": "31-40", "41_to_50": "41-50",
                    "51_to_60": "51-60", "61_to_70": "61-70", "71_to_80": "71-80", "81_and_older": "81+",}


        params = {'$select': 'age_group, sum(confirmed_cases)', '$order': 'age_group', '$group': 'age_group'}
        data = self.resource(resource_id, params=params)

        # flatten data into a dictionary of age_group:cases
        data = { item["age_group"] : int(item["sum_confirmed_cases"]) for item in data }
        age_table = []
        # fill in values in age table
        for target_key, source_key in AGE_KEYS.items():
            age_table.append( { "group": target_key, "raw_count": data[source_key] })

        return age_table

    def get_gender_table(self) -> Dict:
        """Get cases by gender"""
        # Dict of source_label:target_label for re-keying.
        # Note: non cis genders not currently reported
        resource_id = self.resource_ids['age_gender']
        GENDER_KEYS = {"Female": "female", "Male": "male", "Unknown": "unknown"}
        params = {'$select': 'gender, sum(confirmed_cases)', '$group': 'gender'}
        data = self.resource(resource_id, params=params)
        # re-key
        return {GENDER_KEYS[entry["gender"]]: int(entry["sum_confirmed_cases"])
                for entry in data}

    def get_transmission_table(self) -> Dict:
        """Get cases by transmission category"""
        resource_id = self.resource_ids['cases_deaths_transmission']
        # Dict of source_label:target_label for re-keying
        TRANSMISSION_KEYS = {"Community": "community",
                            "From Contact": "from_contact", "Unknown": "unknown"}
        params = { '$select': 'transmission_category, sum(case_count)', '$group': 'transmission_category'}
        data = self.resource(resource_id, params=params)
        # re-key
        transmission_data = { TRANSMISSION_KEYS[ entry["transmission_category"] ]: int(entry["sum_case_count"]) for entry in data}
        return transmission_data

    # Confirmed cases by race and ethnicity
    def get_race_eth_table(self) -> Dict:
        """
        Fetch race x ethnicity data. Individuals are assigned to one race/eth category.
        Individuals identified as 'Hispanic or Latino' are assigned 'Latinx_or_Hispanic'.
        Individuals identified as 'Not Hispanic or Latino' are assigned to their race identification.
        Due to an error in the source data, it appears that Native American datapoint is not currently assigned a race label.
        TO-DO: update this code when the Native American cases are assigned a race label.
        """
        resource_id = self.resource_ids["race_eth"]
        # Dict of source_label:target_label for re-keying.
        # Note: Native_Amer not currently reported
        RACE_ETH_KEYS = {'Hispanic or Latino': 'Latinx_or_Hispanic', 'Asian': 'Asian', 'Black or African American': 'African_Amer', 'White': 'White',
                        'Native Hawaiian or Other Pacific Islander': 'Pacific_Islander', 'Native American': 'Native_Amer', 'Multiple Race': 'Multiple_Race', 'Other': 'Other', 'Unknown': 'Unknown'}
        data = self.resource(resource_id)
        # re-key and aggregate to flatten race x ethnicity
        # initalize all categories to 0 for aggregating
        race_eth_data: Dict[str, int] = {v: 0 for v in RACE_ETH_KEYS.values()}

        for item in data:  # iterate through all race x ethnicity objects
            cases = int(item["confirmed_cases"])
            race = item.get('race','Native American') # if race not  reported, assign "Native American"
            ethnicity = item.get('ethnicity', 'Unknown') # all datapoints appear to report an ethnicity, but if not, default to 'Unknown'. This doesn't currently affect our final numbers.

            # assign 'Hispanic or Latino' individuals
            if ethnicity == "Hispanic or Latino":
                race_eth_data["Latinx_or_Hispanic"] += cases

            # for individuals who are not Hispanic or Latino, assign them their race.
            # This means that counts for all race categories, including Other and Unknown race, exclude individuals who also
            # identified as Hispanic or Latino.
            if ethnicity != "Hispanic or Latino":
                    re_key = RACE_ETH_KEYS[race] # look up this item's re-key
                    race_eth_data[re_key] += cases

        return race_eth_data

if __name__ == '__main__':
    """ When run as a script, logs data to console"""
    print(json.dumps(get_county(), indent=4))
