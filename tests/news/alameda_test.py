from covid19_sfbayarea.news import scrapers
from covid19_sfbayarea.news.alameda import AlamedaNews
from covid19_sfbayarea.news.feed import NewsItem
from covid19_sfbayarea.utils import PACIFIC_TIME
from datetime import datetime
import os
import pytest
from typing import List
from unittest.mock import patch


# Determine whether to run tests that make actual live web requests.
# See `tests/data/test_valid_output.py` for more explanation.
# FIXME: create a pytest fixture that centralizes this code and the original
# version in `tests/data/test_valid_output.py`.
LIVE_TESTS = os.getenv('LIVE_TESTS', '').lower().strip()
TEST_COUNTIES: List[str] = []
if LIVE_TESTS in ('1', 't', 'true', '*', 'all'):
    TEST_COUNTIES = list(scrapers.keys())
elif LIVE_TESTS:
    TEST_COUNTIES = [county
                     for county in (county.strip()
                                    for county in LIVE_TESTS.split(','))
                     if county]


@pytest.mark.skipif('alameda' not in TEST_COUNTIES, reason='Live testing not enabled for Alameda county')
def test_alameda_news() -> None:
    """Basic test of whether Alameda news works without obvious errors."""
    feed = AlamedaNews.get_news()
    assert len(feed.items) > 1
    for item in feed.items:
        assert isinstance(item.id, str)
        assert '' != item.id
        assert isinstance(item.title, str)
        assert '' != item.title
        assert isinstance(item.date_published, datetime)
        assert item.date_published.tzinfo is not None


def test_parses_titles_with_single_word_links() -> None:
    # This is a stripped-down version of the Alameda page's current markup,
    # which may change.
    mock_html = """<!DOCTYPE html>
        <html>
            <body>
                <div id="mainCol">
                    <strong>September 28, 2020</strong>
                    Guidance on How to Celebrate Halloween and D<a title="Joint Statement 9/28/2020" href="/covid19-assets/docs/press/joint-statement-2020.09.28.pdf" target="_blank">&iacute;</a>a de los Muertos Safely
                    <a title="Joint Statement 9/28/2020" href="/covid19-assets/docs/press/joint-statement-2020.09.28.pdf" target="_blank">English</a>
                    |
                    <a title="Joint Statement re: Halloween &amp; Dia de los Muertos" href="/covid19-assets/docs/press/joint-health-officer-statement-about-reopening-spa-2020.09.28.pdf" target="_blank">Spanish</a>
                </div>
            </body>
        </html>
    """
    with patch.object(AlamedaNews, 'load_html', return_value=mock_html):
        feed = AlamedaNews.get_news()
        assert 1 == len(feed.items)
        assert NewsItem(
            id='https://covid-19.acgov.org/covid19-assets/docs/press/joint-statement-2020.09.28.pdf',
            url='https://covid-19.acgov.org/covid19-assets/docs/press/joint-statement-2020.09.28.pdf',
            title='Guidance on How to Celebrate Halloween and Día de los Muertos Safely',
            date_published=datetime(2020, 9, 28, tzinfo=PACIFIC_TIME),
            summary=''
        ) == feed.items[0]
