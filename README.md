# data-covid19-sfbayarea
Manual (see at bottom) and automated processes of sourcing data for the stop-covid19-sfbayarea project

## SFDPH Scraper
This is a script to scrape COVID-19 data from the San Francisco Department of Public Health (SFDPH) website [here](https://www.sfdph.org/dph/alerts/coronavirus.asp) and add it to a CSV file to use in [this SF COVID-19 dashboard](https://github.com/sfbrigade/stop-covid19-sfbayarea).

### Installation
To install the dependencies for this project, run the following lines of code in your terminal:
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
### Use
Right now, you will need to run `python3 scraper.py` to run this tool. In a nutshell, it fetches an HTML page from the SFDPH website, gets the relevant data from the page, and writes a new line with that data to a CSV file in the `data` directory.

Alternatively, you can run `sh auto-scrape.sh`, which will make a new branch, fetch the data, then commit and push that data to that new branch, which you can merge in in GitHub.

**NOTE:** Please be careful to check that the data you are scraping hasn't been committed already before you merge it into `master`.

### Manual Input Needed!
In the data folder, find the spreadsheet of reporting agencies. Each tends to publish only current cumulative data. We want to use the [Wayback Machine](https://archive.org/web/) to grab the data present on those sites for each day since they started reporting (volunteers will have to determine the first date on a case by case basis).

#### Instructions for Manual Input

1) select an agency from the [CA County Health Sites COVID-19](https://docs.google.com/spreadsheets/d/1zeoRCdycgIr8AuJxhhtEaVnAHBfC48qHq9m96Ev_DpU/edit?usp=sharing) file (view only - create issue to add or correct info there)
2) open the [COVID-19 County Data Input](https://docs.google.com/spreadsheets/d/15qBL8ELWt1Xpct_u58XXQxZMQwmqZH5whEQ7lQ6-MRw/edit?usp=sharing) file
3) add (+) a new worksheet tab
4) rename it to the area represented by the website
5) visit website and all available datapoints being tracked by that agency, e.g. confirmed cases, deaths, number of tests conducted, etc.
6) Visit the [Wayback Machine](https://archive.org/web/) and enter the agency website
7) Iterate through each day starting with current, and transpose datapoints to appropriate columns in the data file.
8) When you enter a date before the agency started reporting, you may get the 404 error. You're done! If you have the time, start over with another agency on the list!
9) This data needs to be updated manually every day for the time being. Let us know in slack if you want to do the daily updates.
