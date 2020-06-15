# data-covid19-sfbayarea
Processes for sourcing data for the Stop COVID-19 SF Bay Area dashboard, which you can find [here](https://stop-covid19-sfbayarea.netlify.com/), or [on GitHub](https://github.com/sfbrigade/stop-covid19-sfbayarea).

## Installation
This project requires Python 3 to run. It was built specifically with version `3.7.4`, but it may run with other versions. However, it does take advantage of insertion-ordered dictionaries which are only reliable in `3.7+`.
To install this project, you can simply run `./install.sh` in your terminal. This will set up the virtual environment and install all of the dependencies from `requirements.txt` and `requirements-dev.txt`. However, it will not keep the virtual environment running when the script ends. If you want to stay in the virtual environment, you will have to run `source env/bin/activate` separately from the install script.

## Running the scraper
To run the scraper, you can use the run script by typing `sh run_scraper.sh` into your terminal. This will enable the virtual environment and run `scraper.py`. Once again, the virtual environment will not stay active after the script finishes running. If you want to run the scraper without the run script, enable the virtual environment, then run `python3 scraper.py`.

## Running the API
The best way to run the API right now is to run the command `FLASK_APP="app.py" FLASK_ENV=development flask run;`. Note that this is not the best way to run the scraper at this time.
