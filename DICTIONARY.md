# Bay Area Pandemic Dashboard Data Dictionary #
-----------------------------------------------

## About ##

This file is a guide to the data that is output when running the data scraper
scripts in this repository (either `run_scraper_data.sh` or `scraper_data.py`).
The data is sourced from various local and state government agencies via public
APIs and websites using the automated scripts in this project, which were
written by a volunteer team organized under Code for San Francisco. All the
code in this repository is publicly available on GitHub at the following URL:

https://github.com/sfbrigade/data-covid19-sfbayarea

These scripts seek to standardize field names and data types across disparate
data sets, sometimes running calculations on other data to derive a value. This
means that while the underlying information is present in that source's
original data set, the calculated value itself may not be, and the resulting
values may be imprecise or inaccurate.

Standardizing field names means that values may be summed or grouped
differently in this data set compared to the original source's data set. This
document, where appropriate, will try to explain and call out those
differences. A full listing of the original data sources is below.

## Original Data Sources ##

**Alameda County**

* https://covid-19.acgov.org/data.page

**Contra Costa County**

* https://www.coronavirus.cchealth.org/overview

**Marin County**

* https://coronavirus.marinhhs.org/surveillance

**Napa County**

* (Cases) https://services1.arcgis.com/Ko5rxt00spOfjMqj/ArcGIS/rest/services/CaseDataDemographics/FeatureServer

* (Tests)
  https://legacy.livestories.com/dataset.json?dashId=6014a050c648870017b6dc84

**San Francisco County**

* https://data.sfgov.org/stories/s/San-Francisco-COVID-19-Data-and-Reports/fjki-2fab

**San Mateo County**

* https://www.smchealth.org/post/san-mateo-county-covid-19-data-1

**Santa Clara County**

* https://www.sccgov.org/sites/covid19/Pages/dashboard.aspx

**Solano County**

* https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID19Surveypt1v3_view/FeatureServer/0/query

**Sonoma County**

* https://socoemergency.org/emergency/novel-coronavirus/coronavirus-cases/


## General Data Formatting Notes ##

The automated scripts in this project store the resulting data as JSON, which
supports a limited number of data types natively. Data types such as datetimes
are expressed as strings. This project follows certain conventions when
formatting the data, described below:

* **integers**: null values for integer fields are expressed as "-1". Care should
  be taking when summing values on these fields, as null values in the series
  could affect the calculations

* **dates**: all fields with the type `date` are ISO-8601 formatted date
     strings, (i.e. "yyyy-mm-dd")

* **datetimes** fields whose name end with the string "time" generally
    correspond to a datetime, and should be timezone-aware timestamp strings
    (i.e "yyyy-mm-ddThh:mmz")

For more details, see the `data_models` directory.

## Time Series Data (`"series"`) ##

Time series data is stored in the JSON data under the key `"series"`. The
following data sets are typically present for all counties:

### Cases ###

* "date" (date): Date of the observation

* "cases" (int): The number of positive COVID-19 cases observed on the
  date. Figure may be preliminary and is subject to change

* "cumul_cases" (int): The cumulative number of COVID-19 cases for the county
  since the start of data collection. Figure may be subject to change.


### Deaths ###

TODO

### Tests ###

TODO

## Aggregate Statistics (`"case_totals"`) ##

TODO

## County-Specific Notes ##

### Alameda County ###

* Alameda County only provides a seven-day rolling average for the number of
  tests on any given date, so the cumulative number of tests is not
  available. This data limitation also affects the precision of the number of
  positive and negative tests for any given day. The number of postive tests is
  calculated by multiplying the rolling average number of tests for the day by
  the rolling average of the positivity rate for the same day; to calculate
  negative tests, we take that figure and subtract it from the rolling average
  number of tests.


### Marin County ###
* Data for Marin only accounts for Marin residents and does not include
  inmates at San Quentin State Prison. 

* The "tests" timeseries only includes the number of tests performed and not
  how many were positive or negative. 

* Demographic breakdowns for testing are not available.
