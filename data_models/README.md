# The County Data Model
The county data model lives as [_data_model.json](./_data_model.json).  
This is a legal .json file with the standard structure and default values. Note which items are ordered lists/arrays, such as timeseries, and age groups. Note also that default values are set to -1, which represents any data not present (this could show up in the source data as 'null', 'N/A', etc.) Below is a brief walk-through of the model, with links to more details as needed.
1. Headers  
Below are the top-level datapoints. 

```
{   
    "name": "Name1 Name2 County",  
    "update_time": "yyyy-mm-ddThh:mmz",
    "source_url": "POINT TO LANDING PAGES, IN CASE ENDPOINTS CHANGE", 
    "meta_from_source" : "STORE IMPORTANT NOTES FROM SOURCE HERE",
    "meta_from_baypd": "STORE IMPORTANT NOTES ABOUT OUR METHODS HERE",
}
```
   * `name`: The county's full official name, ending in "County", with spaces, in title case. For example, `"San Mateo County"`.  
* `update_time`: A timestamp string in [ISO 8601](https://www.w3.org/TR/NOTE-datetime) format. If no timezone offset is specified, try converting the timestamp from UTC. We'll keep a running list of places to search for timezone info [here](#timezone).
* `source_url`: There may be a few endpoints that you're working with. In case these change, use a data landing page or data directory that's less likely to change. These are called things like "data portal." Try to point to a place where the user can view our download the source data directly (instead of a dashboard).
* `meta_from_source`: Even if you have access to a metadata file, you may want to look at the dashboards, landing pages, and even press releases surrounding the data in order to get important notes about data collection. Look for keywords like "Notes", "disclaimers", and any blocks of text in visualizations. We would like to scrape these automatically if possible. You may need to use a different process than the process used to fetch the data itself. See [Scraping Techniques](#scraping-techniques) for ideas. The default value if no metadata is available is the empty string `""`.
* `meta_from_paypd`: This field is for our use, to note any oddities transforming the source data to our data model. See [Non-Number Values](#non-number-values) for an example. 




2. [Age Group](#age-group)

## Non-Number Values

## Scraping Techniques

## Amending the Data Model
We aim to capture as much detail about cases as the county is capturing. You may find datapoints that our current data model does not track. For example, most counties were tracking non-binary and non-cis genders all under "Other Gender", so an early iteration of our data model followed suit. Alameda County later added columns for their gender tables for MTF and FTM, so we amended to model to reflect that. Even if the new categories have null values, we want to make space for them. If you notice new categories, please make PR to amend [_data_model.json](./_data_model.json).  
Scraper authors, please keep an eye out for amendments to the data model.

# Race and Ethnicity


# Age Group

The county data model does not specify standard age groups. This is because counties bucket age groups differently, and we would lose a lot of detail in order to sum the age-groups into standard buckets that would fit all counties. Our solution is to capture the age group data just as the county is reporting it. Please be sure to use the age group table provided by the county.  
Below is a snapshot of the age group brackets per county as of April 29, 2020. These may have changed, please inspect your county source. Note that the brackets may also vary by cases and deaths.


## San Francisco
### Cases
	"age_group": [
		{"group": "18_and_under", "raw_count": -1 },
		{"group": "18_to_30", "raw_count": -1 },
		{"group": "31_to_40", "raw_count": -1 },
		{"group": "41_to_50", "raw_count": -1 },
		{"group": "51_to_60", "raw_count": -1 },
		{"group": "61_to_70", "raw_count": -1 },
		{"group": "71_to_80", "raw_count": -1 },
		{"group": "81_and_older", "raw_count": -1}
		]
### Deaths
Data broken down by gender is not available on the json files, only on the dashboard.


## Alameda
### Cases
	"age_group": [
		{"group": "18_and_under", "raw_count": -1 },
		{"group": "18_to_30", "raw_count": -1 },
		{"group": "31_to_40", "raw_count": -1 },
		{"group": "41_to_50", "raw_count": -1 },
		{"group": "51_to_60", "raw_count": -1 },
		{"group": "61_to_70", "raw_count": -1 },
		{"group": "71_to_80", "raw_count": -1 },
		{"group": "81_and_older", "raw_count": -1 },
		{"group": "Unknown", "raw_count": -1 }
		]
### Deaths
Data broken down by gender is not available.


## Sonoma
### Cases
	"age_group": [
		{"group": "0_to_17", "raw_count": -1 },
		{"group": "18_to_49", "raw_count": -1 },
		{"group": "50_to_64", "raw_count": -1 },
		{"group": "65_and_older", "raw_count": -1 },
		{"group": "Unknown", "raw_count": -1 }
		]
### Deaths
Data broken down by gender is not available.


## Santa Clara
### Cases
	"age_group": [
		{"group": "20_and_under", "raw_count": -1 },
		{"group": "21_to_30", "raw_count": -1 },
		{"group": "31_to_40", "raw_count": -1 },
		{"group": "41_to_50", "raw_count": -1 },
		{"group": "51_to_60", "raw_count": -1 },
		{"group": "61_to_70", "raw_count": -1 },
		{"group": "71_to_80", "raw_count": -1 },
		{"group": "81_to_90", "raw_count": -1 },
		{"group": "90_and_older", "raw_count": -1 },
		{"group": "Unknown", "raw_count": -1 }
		]
### Deaths
	"age_group": [
		{"group": "20_and_under", "raw_count": -1 },
		{"group": "21_to_30", "raw_count": -1 },
		{"group": "31_to_40", "raw_count": -1 },
		{"group": "41_to_50", "raw_count": -1 },
		{"group": "51_to_60", "raw_count": -1 },
		{"group": "61_to_70", "raw_count": -1 },
		{"group": "71_to_80", "raw_count": -1 },
		{"group": "81_to_90", "raw_count": -1 },
		{"group": "90_and_older", "raw_count": -1 }
		]        


## San Mateo
### Cases
	"age": [
		{"group": "0_to_19", "raw_count": -1 },
		{"group": "20_to_29", "raw_count": -1 },
		{"group": "30_to_39", "raw_count": -1 },
		{"group": "40_to_49", "raw_count": -1 },
		{"group": "50_to_59", "raw_count": -1 },
		{"group": "60_to_69", "raw_count": -1 },
		{"group": "70_to_79", "raw_count": -1 },
		{"group": "80_to_89", "raw_count": -1 },
		{"group": "90_and_older", "raw_count": -1 }
		]  
### Deaths
	age_group": [
		{"group": "0_to_19", "raw_count": -1 },
		{"group": "20_to_29", "raw_count": -1 },
		{"group": "30_to_39", "raw_count": -1 },
		{"group": "40_to_49", "raw_count": -1 },
		{"group": "50_to_59", "raw_count": -1 },
		{"group": "60_to_69", "raw_count": -1 },
		{"group": "70_to_79", "raw_count": -1 },
		{"group": "80_to_89", "raw_count": -1 },
		{"group": "90_and_older", "raw_count": -1 }
		]  


## Contra Costa
### Cases
	age_group": [
		{"group": "0_to_20", "raw_count": -1 },
		{"group": "21_to_40", "raw_count": -1 },
		{"group": "41_to_60", "raw_count": -1 },
		{"group": "61_to_80", "raw_count": -1 },
		{"group": "81_to_100", "raw_count": -1 }
		]
### Deaths
Data broken down by gender is not available.


## Marin
### Cases and Deaths
	age_group": [
		{"group": "0_to_18", "raw_count": -1 },
		{"group": "19_to_34", "raw_count": -1 },
		{"group": "35_to_49", "raw_count": -1 },
		{"group": "50_to_64", "raw_count": -1 },
		{"group": "65_and_older", "raw_count": -1 }
		]



## Solano
### Cases and Deaths
	age_group": [
		{"group": "0_to_18", "raw_count": -1 },
		{"group": "19_to_64", "raw_count": -1 },
		{"group": "65_and_older", "raw_count": -1 }
		]


## Napa
### Cases
	age_group: [
		{"group": "0_to_17", "raw_count": -1 },
		{"group": "18_to_49", "raw_count": -1 },
		{"group": "50_to_64", "raw_count": -1 },
		{"group": "Over_64", "raw_count": -1 }
		]
### Deaths
Data broken down by gender is not available.

# Timezone  
Here are some places to search for timezone info.
* ArcGIS: On a feature service layer, try [editFieldsInfo.dateFieldsTemeReference](https://developers.arcgis.com/rest/services-reference/layer-feature-service-.htm#GUID-20D36DF4-F13A-4B01-AA05-D642FA455EB6)


