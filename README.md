# data-covid19-sfbayarea
Manual and automated processes of sourcing data for the stop-covid19-sfbayarea project

## SFDPH Scraper
This is a script to scrape COVID-19 data from the San Francisco Department of Public Health (SFDPH) website [here](https://www.sfdph.org/dph/alerts/coronavirus.asp) and add it to a CSV file to use in [this SF COVID-19 dashboard](https://github.com/sfbrigade/stop-covid19-sfbayarea).

### Installation
To install the dependencies for this project, run the following lines of code in your terminal:
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
