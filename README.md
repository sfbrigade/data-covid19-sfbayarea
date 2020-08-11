# data-covid19-sfbayarea
Processes for sourcing data for the Stop COVID-19 SF Bay Area dashboard, which you can find [here](https://stop-covid19-sfbayarea.netlify.com/), or [on GitHub](https://github.com/sfbrigade/stop-covid19-sfbayarea).  
**We are looking for feedback**! Did you come here looking for a data API? Do you have questions, comments, or concerns? Don't leave yet - let us know how you are using this project and what you'd like to see implemented. Please leave us your two cents over in Issues under [#101 Feedback Mega Thread](https://github.com/sfbrigade/data-covid19-sfbayarea/issues/101).

## Installation
This project requires Python 3 to run. It was built specifically with version `3.7.4`, but it may run with other versions. However, it does take advantage of insertion-ordered dictionaries which are only reliable in `3.7+`.
To install this project, you can simply run `./install.sh` in your terminal. This will set up the virtual environment and install all of the dependencies from `requirements.txt` and `requirements-dev.txt`. However, it will not keep the virtual environment running when the script ends. If you want to stay in the virtual environment, you will have to run `source env/bin/activate` separately from the install script.

## Running the scraper
To run the scraper, you can use the run script by typing `sh run_scraper.sh` into your terminal. This will enable the virtual environment and run `scraper.py`. Once again, the virtual environment will not stay active after the script finishes running. If you want to run the scraper without the run script, enable the virtual environment, then run `python3 scraper.py`.

## Development

We use CircleCI to lint the code and run tests in this repository, but you can (and should!) also run tests locally.

The commands described below should all be run from within the virtual environment you’ve created for this project. If you used `install.sh` to get set up, you’ll need to activate your virtual environment before running them with the command:

```sh
$ source env/bin/activate
```

If you manage your environments differently (e.g. with Conda or Pyenv-Virtualenv), use whatever method you normally do to set up your environment.

### Tests

You can run tests using `pytest` like so:

```sh
# In the root directory of the project:
$ python -m pytest -v .
```

### Linting and Code Conventions

We use Pyflakes for linting. Many editors have support for running it while you type (either built-in or via a plugin), but you can also run it directly from the command line:

```sh
# In the root directory of the project:
$ pyflakes .
```

We also use type annotations throughout the project. To check their validity with Mypy, run:

```sh
# In the root directory of the project:
$ mypy .
```
