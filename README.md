# data-covid19-sfbayarea
Processes for sourcing data for the Stop COVID-19 SF Bay Area dashboard, which you can find [here](https://stop-covid19-sfbayarea.netlify.com/), or [on GitHub](https://github.com/sfbrigade/stop-covid19-sfbayarea).  
**We are looking for feedback**! Did you come here looking for a data API? Do you have questions, comments, or concerns? Don't leave yet - let us know how you are using this project and what you'd like to see implemented. Please leave us your two cents over in Issues under [#101 Feedback Mega Thread](https://github.com/sfbrigade/data-covid19-sfbayarea/issues/101).

## Installation
This project requires Python 3 to run. It was built specifically with version `3.7.4`, but it may run with other versions. However, it does take advantage of insertion-ordered dictionaries which are only reliable in `3.7+`.
To install this project, you can simply run `./install.sh` in your terminal. This will set up the virtual environment and install all of the dependencies from `requirements.txt` and `requirements-dev.txt`. However, it will not keep the virtual environment running when the script ends. If you want to stay in the virtual environment, you will have to run `source env/bin/activate` separately from the install script.

## Running the scraper
To run the scraper, you can use the run script by typing `sh run_scraper.sh` into your terminal. This will enable the virtual environment and run `scraper.py`. Once again, the virtual environment will not stay active after the script finishes running. If you want to run the scraper without the run script, enable the virtual environment, then run `python3 scraper.py`.

## Running the API
The best way to run the API right now is to run the command `FLASK_APP="app.py" FLASK_ENV=development flask run;`. Note that this is not the best way to run the scraper at this time.

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

### Reviewing and Merging Pull Requests
1. **PRs that are hotfixes do not require review.**  
    - Hotfixes repair broken functionality that was previously vetted, they do not add functionality. For these PRs, please feel free to request a review from one or more people. 
    - If you are requested to review a hotfix, note that the first priority is to make sure the output is correct. "Get it working first, make it nice later." You do not have to be an expert in the function's history, nor understand every line of the diff changes. If you can verify whether the output is correct, you are qualified and encouraged to review a hotfix!
    - If no reviewers respond within 2 days, please merge in your PR yourself.  
    - Examples of hotfixes are:
        1. Fixing broken scrapers
        1. Fixing dependencies - libraries, virtual environments, etc.
        1. Fixing github actions running the scrapers, and fixing CircleCI

2. **PRs that add functionality/features require at least 1 passing review.**
    - If you are adding functionality, please explicitly require a review from at least one person. 
    - When at least one person has approved the PR, the  author of the PR is responsible for merging it in. You must have 1+ approving reviews to merge, but you don't need all requested reviewers to approve. 
    - If you are one of the people required for review, please either complete your review within 3 days, or let the PR author know you are unavailable for review. 
    - Examples of PRs that add functionality are:
        1. Adding new scrapers
        1. Structural refactors, such as changing the data model, or substantial rewrite of an existing scraper

3. **PRs that update the documentation require at least 1 passing review.**
    - Documentation PRs are in the same tier as #2. Please explicitly require a review from at least one person. 
    - When at least one person has approved the PR, the  author of the PR is responsible for merging it in. You must have 1+ approving reviews to merge, but you don't need all requested reviewers to approve. 
    - If you are one of the people required for review, please either complete your review within 3 days, or let the PR author know you are unavailable for review. 
    - Examples are:
        1. Updates to the data fetch README
        1. Commenting code
        1. Adding to metadata

4. Reviewers
    1. Everyone can review #1 hotfixes, or #3 documentation. If you want to proactively sign up to be first-string for these reviews, please add your github handle to the list below.
        - @elaguerta
        - @benghancock

    2. Experienced developers with deep knowledge of the project should be tapped for PRs that deal with complicated dependencies, language-specific implementation questions, structural/architectural concerns. If you want to be first-string for these reviews, please add your github handle to the list below.
        - @Mr0grog
        - @rickpr
        - @ldtcooper

    1. People who have interest in data, public health, and social science should be tapped for PRs that deal with decisions that affect how data is reported, structured, and provided to the user. If you want to be first-string for these reviews, please list your github name below.
        - @elaguerta
        - @benghancock
        - @ldtcooper

