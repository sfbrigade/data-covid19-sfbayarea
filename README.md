# data-covid19-sfbayarea

Processes for sourcing data for the Stop COVID-19 SF Bay Area dashboard, which you can find [here](https://stop-covid19-sfbayarea.netlify.com/), or [on GitHub](https://github.com/sfbrigade/stop-covid19-sfbayarea).  
**We are looking for feedback**! Did you come here looking for a data API? Do you have questions, comments, or concerns? Don't leave yet - let us know how you are using this project and what you'd like to see implemented. Please leave us your two cents over in Issues under [#101 Feedback Mega Thread](https://github.com/sfbrigade/data-covid19-sfbayarea/issues/101).


## Installation

This project requires Python 3 to run. It was built specifically with version `3.7.4`, but it may run with other versions. However, it does take advantage of insertion-ordered dictionaries which are only reliable in `3.7+`.
To install this project, you can simply run `./install.sh` in your terminal. This will set up the virtual environment and install all of the dependencies from `requirements.txt` and `requirements-dev.txt`. However, it will not keep the virtual environment running when the script ends. If you want to stay in the virtual environment, you will have to run `source env/bin/activate` separately from the install script.


## Running the scraper

This project includes three separate scraping tools for different purposes:

- [Legacy CDS (Corona Data Scraper) Scraper](#legacy-scraper)
- [County Website Scraper](#county-scraper)
- [County News Scraper](#news-scraper)

**You can also run each of these tools in Docker.** See the [“using Docker”](#using-docker) section below.


### <a id="legacy-scraper"></a> Legacy CDS Scraper

The Legacy CDS Scraper loads Bay Area county data from the [Corona Data Scraper][CDS] project. Run it by typing into your terminal:

```console
$ ./run_scraper.sh
```

This takes care of activating the virtual environment and running the actual Python scraping script. **If you are managing your virtual environments separately,** you can run the Python script directly with:

```console
$ python3 scraper.py
```


### <a id="county-scraper"></a> County Website Scraper

The newer county website scraper loads data directly from county data portals or by scraping counties’ public health websites. Running the shell script wrapper will take care of activating the virtual environment for you, or you can run the Python script directly:

```console
# Run the wrapper:
$ ./run_scraper_data.sh

# Or run the script directly if you are managing virtual environments youself:
$ python3 scraper_data.py
```

By default, it will output a JSON object with data for all currently supported counties. Use the `--help` option to see a information about additional arguments (the same options also work when running the Python script directly):

```console
$ ./run_scraper_data.sh --help
Usage: scraper_data.py [OPTIONS] [COUNTY]...

  Create a .json with data for one or more counties. Supported counties:
  alameda, san_francisco, solano.

Options:
  --output PATH  write output file to this directory
  --help         Show this message and exit.
```

- To scrape a specific county or counties, list the counties you want. For example, to scraper only Alameda and Solano counties:

    ```console
    $ ./run_scraper_data.sh alameda solano
    ```

- `--output` specifies a file to write to instead of your terminal’s STDOUT.


### <a id="news-scraper"></a> County News Scraper

The news scraper finds official county news, press releases, etc. relevant to COVID-19 and formats it as news feeds. Running the shell script wrapper will take care of activating the virtual environment for you, or you can run the Python script directly:

```console
# Run the wrapper:
$ ./run_scraper_news.sh

# Or run the script directly if you are managing virtual environments youself:
$ python3 scraper_news.py
```

By default, it will output a series of JSON Feed-formatted JSON objects — one for each county. Use the `--help` option to see a information about additional arguments (the same options also work when running the Python script directly):

```console
$ ./run_scraper_news.sh --help
Usage: scraper_news.py [OPTIONS] [COUNTY]...

  Create a news feed for one or more counties. Supported counties: alameda,
  contra_costa, marin, napa, san_francisco, san_mateo, santa_clara, solano,
  sonoma.

Options:
  --from CLI_DATE                 Only include news items newer than this
                                  date. Instead of a date, you can specify a
                                  number of days ago, e.g. "14" for 2 weeks
                                  ago.

  --format [json_feed|json_simple|rss]
  --output PATH                   write output file(s) to this directory
  --help                          Show this message and exit.
```

- To scrape a specific county or counties, list the counties you want. For example, to scraper only Alameda and Solano counties:

    ```console
    $ ./run_scraper_data.sh alameda solano
    ```

- `--from` sets the earliest date/time from which to include news items. It can be a date, like `2020-07-15`, a specific time, like `2020-07-15T10:00:00` for 10 am on July 15th, or a number of days before the current time, like `14` for the last 2 weeks.

- `--format` sets the output format. Acceptable values are: `json_feed` (see the [JSON Feed spec][json_feed_spec]), `json_simple` (a simplified JSON format), or `rss` ([RSS v2][rss_spec]). Specify this option multiple times to output multiple formats, e.g:

    ```console
    $ ./run_scraper_data.sh --format rss --format json_feed
    ```

- `--output` specifies a directory to write to instead of your terminal’s STDOUT. Each county and `--format` combination will create a separate file in the directory. If the directory does not exist, it will be created.


## Using Docker

As an alternative to installing and running the tools normally, you can use [Docker](https://www.docker.com/) to install and run them. This is especially helpful on Windows, where setting up Selenium and other Linux tools the scraper can be complicated.

1. Download and install Docker from https://www.docker.com/ (You’ll probably need to create a Docker account as well if you don’t already have one.)

2. Now run [any of the tools](#running-the-scraper) by adding their command after `./run_docker.sh`. For example, to run the news scraper:

    ```sh
    $ ./run_docker.sh python scraper_data.py
    ```

    Under the hood, this builds the Docker container and then runs the specified command in it.

    Docker acts kind of like a virtual machine, and you can also simply get yourself a command prompt inside the docker container by running `./run_docker.sh` with no arguments:

    ```sh
    $ ./run_docker.sh
    # This will output information about the build, and then give you a
    # command prompt:
    root@ca87fa64d822:/app#

    # You can now run commands like the data scraper as normal from the prompt:
    root@ca87fa64d822:/app# python scraper_data.py
    root@ca87fa64d822:/app# python scraper_news.py
    ```


## Data Models
The data models are in JSON format and are located in the `data_models` directory. For more information, see the [data model readme](./data_models/README.md).

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

[CDS]: https://coronadatascraper.com/
[json_feed_spec]: https://jsonfeed.org/
[rss_spec]: https://www.rssboard.org/rss-specification

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



