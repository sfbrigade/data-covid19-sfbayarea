"""
Contra Costa County

Contra Costa builds its dashboard with Qlik. Qlik can be a bit complicated, so
we've also got an API client called ``qlik.QlikClient``.

There's not an obvious way to pull directly from whatever raw data the Qlik
charts are based on, so instead we have to pull the data that backs each chart.
(For example, if you dig around enough, it appears there is a single table with
all timeseries, but there's no clear way to get the data from the table.
Instead, we get the data behind each of the cases by date chart, deaths by date
chart, and so on.)

How do we determine the chart IDs to pull data from? When browsing one of the
dashboard pages, you'll a JS file loaded that is named for the dashboard.
For example, on the https://www.coronavirus.cchealth.org/overview dashboard, a
JS file named dashboard.cchealth.org/extensions/COVIDDashboard/Overview.js.
That JS file will have a series of calls to
``getObject('<dom_id>', '<chart_id>', ...)`` like so:

    overviewApp.getObject('QV01','gumQeX',{noSelections: true, noInteraction: false});
    overviewApp.getObject('QV02','LuVGBZ',{noSelections: true, noInteraction: false});
    overviewApp.getObject('QV03','jWjFxe',{noSelections: true, noInteraction: false});
    overviewApp.getObject('QV04','cWjnGdK',{noSelections: true, noInteraction: false});
    overviewApp.getObject('QV05','bZFxmu',{noSelections: true, noInteraction: false});

For each line, the first string is the ID of a DOM element on the page that
contains the chart and the second string is the chart ID in Qlik.

To get the Qlik chart ID for any chart on the page, use your browser's web
inspector to find the ``<div>`` that holds the chart and get its ID. Example:

    <div class="chart qvobject" id="QV05">...</div>

Then look in the JS file for the line like above that maps that DOM ID to a
Qlik chart ID. In the example above, the DOM ID was ``'QV05'``, and you can see
in the example JS that the matching Qlik chart ID would be ``'bZFxmu'``.

Dashboards:
Overview - https://www.coronavirus.cchealth.org/overview
           https://dashboard.cchealth.org/extensions/COVIDDashboard/Overview.html
           ID: b7d7f869-fb91-4950-9262-0b89473ceed6

Vaccines - https://www.coronavirus.cchealth.org/vaccine
           ID: 8dea25ae-3782-48ef-9199-508a3163297e
"""

from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List
from ..errors import FormatError
from ..utils import assert_equal_sets, parse_datetime
from .qlik import QlikClient


CHART_IDS = {
    # Timeseries
    'new_cases': 'cWjnGdK',
    'total_cases': 'jWjFxe',
    'deaths': 'zKvfuW',
    'total_tests': 'ejpTS',
    'test_positivity': 'VapZPL',

    # Case demographics
    'cases_by_gender': 'tAqmEW',
    'cases_by_age': 'mmXYJhJ',
    'cases_by_race': 'ppmdr',
    'cases_by_ethnicity': 'PEqthPy',

    # Death demographics
    'deaths_by_gender': 'KHwxYe',
    'deaths_by_age': 'pWrYQeL',
    'deaths_by_race': 'LjJk',
    'deaths_by_ethnicity': 'ffcHDa',

    # Contra Costa does not publish demographic breakdowns for testing.
}


def get_county() -> Dict:
    """
    Get data for Contra Costa County.
    """
    api = QlikClient('wss://dashboard.cchealth.org/app/',
                     'b7d7f869-fb91-4950-9262-0b89473ceed6',
                     ssl_verify=False)
    notes = ('Positive test counts are not published by the county, so they '
             'are estimated from daily positivity rates. Positivity rates are '
             'are not published for dates as early as some tests are, so '
             'positive test counts before 2020-03-18 may incorrectly show 0. '
             'Unlike other counties, Contra Costa separates hispanic '
             'ethnicity from racial demographics, so "latinx" is not included '
             'in `case_totals.race_eth` or `death_totals.race_eth`. Latinx '
             'vs. non-latinx is shown in separate `case_totals.ethnicity` and '
             '`death_total.ethnicity` groupings. '
             'Contra Costa also does not tally native american or pacific '
             'islander as races, and they are instead included as "other".'
             'Demographic information is not available for tests.')

    with api:
        # Set language to English (so we only get one language's entries, e.g.
        # we only get "Female" instead of "Female" + "Femenino").
        api.select_field_value('LabelLanguage', 'English')

        return {
            'name': 'Contra Costa',
            'update_time': get_latest_update(api).isoformat(),
            'source_url': 'https://www.coronavirus.cchealth.org/overview',
            'meta_from_source': '',
            'meta_from_baypd': notes,
            'series': {
                'cases': get_timeseries_cases(api),
                'deaths': get_timeseries_deaths(api),
                'tests': get_timeseries_tests(api),
            },
            'case_totals': get_case_totals(api),
            'death_totals': get_death_totals(api),
        }


def get_latest_update(api: QlikClient) -> datetime:
    return parse_datetime(api.get_app_layout()['qLayout']['qLastReloadTime'])


def get_chart_data(api: QlikClient, chart_id: str) -> List[List[Dict]]:
    """
    Get the underlying data for a standard chart by its Qlik object ID. This
    does *not* work for "stacked" charts, with multiple overlaid series.
    """
    chart = api.get_data(chart_id)
    return chart['qLayout']['qHyperCube']['qDataPages'][0]['qMatrix']


def get_timeseries_cases(api: QlikClient) -> List[dict]:
    new_cases_data = get_chart_data(api, CHART_IDS['new_cases'])
    total_cases_data = get_chart_data(api, CHART_IDS['total_cases'])

    cases = {api.parse_date(x['qNum']): {'date': api.parse_date(x['qNum']).isoformat(),
                                         'cases': y['qNum']}
             for x, y in new_cases_data}
    for x, y in total_cases_data:
        day = api.parse_date(x['qNum'])
        record = cases.get(day)
        if not record:
            record = {'date': day.isoformat()}
            cases[day] = record

        record['cumul_cases'] = y['qNum']

    result = [cases[day] for day in sorted(cases.keys())]

    # Sanity-check daily cases vs. totals
    total = 0
    for index, record in enumerate(result):
        # We can't find a reliable county-level source that covers all time, so
        # so the total cases on the first day of the timeseries may include
        # past cases, and can't be reconciled with any other data.
        if index == 0:
            total = record['cumul_cases']
        else:
            total += record['cases']

        if record['cumul_cases'] != total:
            raise FormatError(f'Sum of daily cases != cumul_cases at record {index} (date: {record["date"]})')

    return result


def get_timeseries_deaths(api: QlikClient) -> List[dict]:
    data = get_chart_data(api, CHART_IDS['deaths'])

    total = 0
    results = []
    # LTCF = Long Term Care Facility (e.g. nursing homes)
    # LTCF deaths include both residents and staff.
    for x, non_ltcf, ltcf in data:
        day = api.parse_date(x['qNum'])
        deaths = non_ltcf['qNum'] + ltcf['qNum']
        total += deaths
        results.append({
            'date': day.isoformat(),
            'deaths': deaths,
            'cumul_deaths': total,
            # TODO: consider adding these for counties that include them?
            # 'ltcf_deaths': ltcf['qNum'],
            # 'non_ltcf_deaths': non_ltcf['qNum'],
        })

    return results


def get_timeseries_tests(api: QlikClient) -> List[dict]:
    """
    Calculate a timeseries of tests.

    The dashboard has daily tests and daily total tests as separate charts, but
    they don't quite agree. We use the daily total tests chart and calculate
    daily tests by taking the difference between each day.

    More detail: daily total tests starts earlier (but clearly not on the first
    day there were tests, given the values). Daily tests starts later *and* has
    ``0`` as the value for the first several days, despite the daily totals
    having > 0 differences on those days. Once daily tests starts having values
    it lines up with the differences between daily total tests entries, so it
    seems like daily total tests is a more complete and accurate chart.
    """
    tests: Dict[date, Dict] = defaultdict(lambda: {
        'tests': -1,
        'positive': -1,
        'negative': -1,
        'pending': -1,
        'cumul_tests': -1,
        'cumul_pos': -1,
        'cumul_neg': -1,
        'cumul_pend': -1,
        'positivity': -1
    })

    total_tests_data = get_chart_data(api, CHART_IDS['total_tests'])
    for x, y in total_tests_data:
        day = api.parse_date(x['qNum'])
        tests[day]['cumul_tests'] = y['qNum']

    # There's no chart with total positive tests, so we use the *rate* to
    # calculate it. Note also that this is a rolling average, not the actual
    # rate on the day, so this is not the most accurate. :(
    #
    # This chart is a "stacked" chart (it has two series -- rate and equity
    # metric rate), so is structured in a more complex way.
    # The data is a list of dates, where each has a `qSubNodes` list with one
    # item from each series. Those items each have their own `qSubNodes` list
    # with one item that contains the actual value.
    positive_rate_chart = api.get_data(CHART_IDS['test_positivity'])
    positive_rate_data = positive_rate_chart['qLayout']['qHyperCube']['qStackedDataPages'][0]['qData'][0]['qSubNodes']
    for node in positive_rate_data:
        day = api.parse_date(node['qValue'])
        # In the first list of subnodes:
        #   0 = "% Positive Equity Metric"
        #   1 = "% Tested Positive 7-Day Average"
        # In the nested list of subnodes, there's only one item, which has the
        # actual value.
        rate = node['qSubNodes'][1]['qSubNodes'][0]['qValue']
        # Store the rate; we need to do anothe pass to calculate daily tests
        # before we can use the rate to calculate daily positives.
        tests[day]['positivity'] = rate

    # Clean up, sanity-check, and put the results in order.
    result = []
    total = 0
    total_positive = 0
    found_first = False
    for day in sorted(tests.keys()):
        record = tests[day]
        # Skip over all items earlier than the first day with total tests.
        # (It might be possible for the positivity rate chart to start first.)
        if not found_first:
            if record['cumul_tests'] > -1:
                found_first = True
                total = record['cumul_tests']
            continue

        record['date'] = day.isoformat()
        record['tests'] = record['cumul_tests'] - total
        total = record['cumul_tests']

        # Estimate positive tests from positivity rate.
        if record['positivity'] > -1:
            record['positive'] = round(record['tests'] * record['positivity'])
            total_positive += record['positive']
        else:
            record['positive'] = 0
        record['cumul_pos'] = total_positive

        result.append(record)

    return result


def get_case_totals(api: QlikClient) -> Dict:
    # Gender and age groups are published as counts, but race and ethnicity are
    # published as percentages, so we need thet total to calculate counts.
    gender = get_cases_by_gender(api)
    total = sum(gender.values())

    return {
        'gender': gender,
        'age_group': get_cases_by_age(api),
        'race_eth': get_cases_by_race(api, total),
        'ethnicity': get_cases_by_ethnicity(api, total),
        # No data for these right now:
        # 'underlying_cond': get_cases_by_condition(api),
        # 'transmission_cat': get_cases_by_transmission(api),
    }


def get_cases_by_gender(api: QlikClient) -> Dict:
    gender_data = get_chart_data(api, CHART_IDS['cases_by_gender'])
    result = {x['qText'].lower(): y['qNum']
              for x, y in gender_data}
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories '
                          f'for cases, got: {list(result.keys())}')
    return result


def get_cases_by_age(api: QlikClient) -> List[Dict]:
    age_data = get_chart_data(api, CHART_IDS['cases_by_age'])
    return [{'group': x['qText'], 'raw_count': y['qNum']}
            for x, y in age_data]


def get_cases_by_race(api: QlikClient, total: int) -> Dict:
    raw = get_chart_data(api, CHART_IDS['cases_by_race'])
    mapping = {
        'asian': 'Asian',
        'black or african american': 'African_Amer',
        'multiple races': 'Multiple_Race',
        'other': 'Other',
        'white': 'White',
        'unknown': 'Unknown',
    }
    data = {group['qText'].lower(): round(total * cases['qNum'])
            for group, _population, cases in raw}
    assert_equal_sets(mapping.keys(), data.keys())
    result = {mapping[race]: count
              for race, count in data.items()}
    # These are included in "other".
    result['Native_Amer'] = -1
    result['Pacific_Islander'] = -1
    # Latinx is separated out as an ethnicity (unlike other counties, Contra
    # Costa publishes race and ethnicity separately, rather than as a single,
    # intersecting set).
    result['Latinx_or_Hispanic'] = -1
    return result


def get_cases_by_ethnicity(api: QlikClient, total: int) -> Dict:
    raw = get_chart_data(api, CHART_IDS['cases_by_ethnicity'])
    mapping = {
        'hispanic or latino': 'Latinx_or_Hispanic',
        'not hispanic or latino': 'Other',
        'unknown': 'Unknown',
    }
    data = {group['qText'].lower(): round(total * cases['qNum'])
            for group, _population, cases in raw}
    assert_equal_sets(mapping.keys(), data.keys())
    result = {mapping[race]: count
              for race, count in data.items()}
    return result


def get_death_totals(api: QlikClient) -> Dict:
    return {
        'gender': get_deaths_by_gender(api),
        'age_group': get_deaths_by_age(api),
        'race_eth': get_deaths_by_race(api),
        'ethnicity': get_deaths_by_ethnicity(api),
        # No data for these right now:
        # 'underlying_cond': get_deaths_by_condition(api),
        # 'transmission_cat': get_deaths_by_transmission(api),
    }


def get_deaths_by_gender(api: QlikClient) -> Dict:
    gender_data = get_chart_data(api, CHART_IDS['deaths_by_gender'])
    result = {x['qText'].lower(): y['qNum']
              for x, y in gender_data}
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories '
                          f'for deaths, got: {list(result.keys())}')
    return result


def get_deaths_by_age(api: QlikClient) -> List[Dict]:
    age_data = get_chart_data(api, CHART_IDS['deaths_by_age'])
    return [{'group': x['qText'], 'raw_count': y['qNum']}
            for x, y in age_data]


def get_deaths_by_race(api: QlikClient) -> Dict:
    raw = get_chart_data(api, CHART_IDS['deaths_by_race'])
    mapping = {
        'asian': 'Asian',
        'black or african american': 'African_Amer',
        'multiple races': 'Multiple_Race',
        'other': 'Other',
        'white': 'White',
        'unknown': 'Unknown',
    }
    data = {group['qText'].lower(): count['qNum']
            for group, count in raw}
    assert_equal_sets(mapping.keys(), data.keys())
    result = {mapping[race]: count
              for race, count in data.items()}
    # These are included in "other".
    result['Native_Amer'] = -1
    result['Pacific_Islander'] = -1
    # Latinx is separated out as an ethnicity (unlike other counties, Contra
    # Costa publishes race and ethnicity separately, rather than as a single,
    # intersecting set).
    result['Latinx_or_Hispanic'] = -1
    return result


def get_deaths_by_ethnicity(api: QlikClient) -> Dict:
    raw = get_chart_data(api, CHART_IDS['deaths_by_ethnicity'])
    mapping = {
        'hispanic or latino': 'Latinx_or_Hispanic',
        'not hispanic or latino': 'Other',
        'unknown': 'Unknown',
    }
    data = {group['qText'].lower(): count['qNum']
            for group, count in raw}
    assert_equal_sets(mapping.keys(), data.keys())
    result = {mapping[race]: count
              for race, count in data.items()}
    return result
