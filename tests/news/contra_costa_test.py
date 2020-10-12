from covid19_sfbayarea.news import scrapers
from covid19_sfbayarea.news.contra_costa import ContraCostaNews
from covid19_sfbayarea.news.feed import NewsItem
from covid19_sfbayarea.news.utils import PACIFIC_TIME
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


def html_document(text):
    """Wrap an HTML snippet in <body> tags, etc. to make it a full document."""
    return f"""<!DOCTYPE html>
        <html>
            <body>
                {text}
            </body>
        </html>
    """


@pytest.mark.skipif('contra_costa' not in TEST_COUNTIES, reason='Live testing not enabled for Contra Costa county')
def test_basic_news() -> None:
    """Basic test of whether Contra Costa news works without obvious errors."""
    feed = ContraCostaNews.get_news()
    assert len(feed.items) > 1
    for item in feed.items:
        assert isinstance(item.id, str)
        assert '' != item.id
        assert isinstance(item.title, str)
        assert '' != item.title
        assert isinstance(item.date_published, datetime)
        assert item.date_published.tzinfo is not None


def test_parses_standard_items() -> None:
    # This is a stripped-down version of the Alameda page's current markup,
    # which may change.
    mock_html = html_document("""
        <div data-packed="false" data-vertical-text="false" style="width: 586px; min-height: 426px; pointer-events: none;" data-min-height="426" class="txtNew" id="comp-kdgm96ib">
            <h3 class="font_3" style="line-height:1.4em;">September 2020​</h3>
            <ul class="font_7">
                <li>
                    <p class="font_7" style="line-height:1.3em;">
                        <span style="color:#02618D;"><span style="text-decoration:underline;"><a href="https://cchealth.org/press-releases/2020/0930-Free-Flu-Shots.php" target="_blank" data-content="https://cchealth.org/press-releases/2020/0930-Free-Flu-Shots.php" data-type="external" rel="noopener">Press Release</a></span></span>:&nbsp;Contra Costa County to Begin Offering Free Flu Shots at COVID Testing Sites - 9/30/2020
                    </p>
                </li>
            </ul>
        </div>
    """)
    with patch.object(ContraCostaNews, 'load_html', return_value=mock_html):
        feed = ContraCostaNews.get_news()
        assert 1 == len(feed.items)
        assert NewsItem(
            id='https://cchealth.org/press-releases/2020/0930-Free-Flu-Shots.php',
            url='https://cchealth.org/press-releases/2020/0930-Free-Flu-Shots.php',
            title='Press Release:\u00a0Contra Costa County to Begin Offering Free Flu Shots at COVID Testing Sites',
            date_published=datetime(2020, 9, 30, tzinfo=PACIFIC_TIME)
        ) == feed.items[0]


def test_parses_items_with_inline_translation() -> None:
    # This is a stripped-down version of the Alameda page's current markup,
    # which may change.
    mock_html = html_document("""
        <div data-packed="false" data-vertical-text="false" style="width: 586px; min-height: 426px; pointer-events: none;" data-min-height="426" class="txtNew" id="comp-kdgm96ib">
            <h3 class="font_3" style="line-height:1.4em;">September 2020​</h3>
            <ul class="font_7">
                <li>
                    <p class="font_7" style="line-height:1.3em;">
                        <span style="text-decoration:underline;"><a href="https://813dcad3-2b07-4f3f-a25e-23c48c566922.filesusr.com/ugd/84606e_05b2f6cd4fff43ea9574506930a8edba.pdf" target="_blank" data-type="document"><span style="color:#02618D;">Flye</span></a></span><span style="text-decoration:underline;"><a href="https://813dcad3-2b07-4f3f-a25e-23c48c566922.filesusr.com/ugd/84606e_05b2f6cd4fff43ea9574506930a8edba.pdf" target="_blank" data-type="document"><span style="color:#02618D;">r</span></a></span>: Avoid the 3-C's|<a href="https://813dcad3-2b07-4f3f-a25e-23c48c566922.filesusr.com/ugd/84606e_a8695d376fc0490f970b4d339d5b99b6.pdf" target="_blank" data-type="document"><span style="color:#02618D;"><span style="text-decoration:underline;"><span style="font-style:italic;">Evite el 1-2-3</span></span></span></a>&nbsp;- 9/8/2020
                    </p>
                </li>
            </ul>
        </div>
    """)
    with patch.object(ContraCostaNews, 'load_html', return_value=mock_html):
        feed = ContraCostaNews.get_news()
        assert 1 == len(feed.items)
        assert NewsItem(
            id='https://813dcad3-2b07-4f3f-a25e-23c48c566922.filesusr.com/ugd/84606e_05b2f6cd4fff43ea9574506930a8edba.pdf',
            url='https://813dcad3-2b07-4f3f-a25e-23c48c566922.filesusr.com/ugd/84606e_05b2f6cd4fff43ea9574506930a8edba.pdf',
            title='Flyer: Avoid the 3-C\'s|Evite el 1-2-3',
            date_published=datetime(2020, 9, 8, tzinfo=PACIFIC_TIME)
        ) == feed.items[0]


def test_parses_items_with_list_of_translations() -> None:
    # This is a stripped-down version of the Alameda page's current markup,
    # which may change.
    mock_html = html_document("""
        <div data-packed="false" data-vertical-text="false" style="width: 586px; min-height: 426px; pointer-events: none;" data-min-height="426" class="txtNew" id="comp-kdgm96ib">
            <h3 class="font_3" style="line-height:1.4em;">September 2020​</h3>
            <ul class="font_7">
                <li style="line-height:1.3em;">
                    <p class="font_7" style="line-height:1.3em;">
                        <span style="color:#02618D;"><span style="text-decoration:underline;"><a href="https://www.coronavirus.cchealth.org/health-orders" target="_self" data-anchor="dataItem-kbv5g6t01">Health Order</a></span></span>: Updated Mass Quarantine Order - 10/8/2020
                    </p>

                    <ul>
                        <li>
                            <p class="font_7" style="line-height:1.3em;">
                                <a href="https://www.coronavirus.cchealth.org/ordenes-de-salud" target="_self" data-anchor="dataItem-kdrscaa8"><span style="color:#02618D;"><span style="text-decoration:underline;"><span style="font-style:italic;">Haga clic aquí </span></span></span><span style="color:#02618D;"><span style="text-decoration:underline;"><span style="font-style:italic;">para leer la orden de salud​&nbsp;</span></span></span><span style="text-decoration:underline;">​</span></a>
                            </p>
                        </li>
                    </ul>
                </li>
            </ul>
        </div>
    """)
    with patch.object(ContraCostaNews, 'load_html', return_value=mock_html):
        feed = ContraCostaNews.get_news()
        assert 1 == len(feed.items)
        assert NewsItem(
            id='https://www.coronavirus.cchealth.org/health-orders',
            url='https://www.coronavirus.cchealth.org/health-orders',
            title='Health Order: Updated Mass Quarantine Order',
            date_published=datetime(2020, 10, 8, tzinfo=PACIFIC_TIME)
        ) == feed.items[0]
