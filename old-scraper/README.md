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

**NOTE:** Please be careful to check that the data you are scraping hasn't been co
