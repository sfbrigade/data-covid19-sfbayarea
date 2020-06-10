from os import getenv
from selenium import webdriver  # type: ignore


def get_firefox() -> webdriver.Firefox:
    """
    Get a properly configured Firefox webdriver instance.

    By default, this returns a headless Firefox. Set the ``FIREFOX_VISIBLE``
    environment variable to anything in order to get a non-headless browser.
    """
    options = webdriver.FirefoxOptions()
    options.headless = not getenv('FIREFOX_VISIBLE')
    return webdriver.Firefox(options=options)
