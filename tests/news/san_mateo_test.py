from covid19_sfbayarea.news.san_mateo import SanMateoNews
from datetime import datetime, timezone
from unittest.mock import patch


def test_parses_news_data() -> None:
    mock_rss = """
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <channel>
            <item>
                <title>Sept. 25, 2020: Health Officer Order Prohibits Removal</title>
                <link>https://cmo.smcgov.org/press-release/sept-25-2020-health-officer-order-prohibits-removal-fire-debris-burn-sites-pending</link>
                <description><![CDATA[Sept. 25, 2020San Mateo County Health Officer Dr. Scott Morrow has issued a health order.]]></description>
                <pubDate>Fri, 25 Sep 2020 22:05:08 +0000</pubDate>
                <dc:creator>mwilson</dc:creator>
                <guid isPermaLink="false">12711 at https://cmo.smcgov.org</guid>
            </item>
        </channel>
    </rss>
    """.encode('utf-8')

    scraper = SanMateoNews()
    items = scraper.parse_feed(mock_rss, SanMateoNews.URL)
    assert 1 == len(items)
    assert 'Health Officer Order Prohibits Removal' == items[0].title
    assert ('San Mateo County Health Officer Dr. Scott Morrow has issued a '
            'health order.' == items[0].summary)
    assert (datetime(2020, 9, 25, 22, 5, 8, tzinfo=timezone.utc)
            == items[0].date_published)
    assert ('https://cmo.smcgov.org/press-release/sept-25-2020-health-officer-order-prohibits-removal-fire-debris-burn-sites-pending'
            == items[0].url)


def test_strips_non_abbreviated_prefixes_from_title() -> None:
    mock_rss = """
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <channel>
            <item>
                <title>September 25, 2020: Health Officer Order Prohibits Removal</title>
                <link>https://cmo.smcgov.org/press-release/sept-25-2020-health-officer-order-prohibits-removal-fire-debris-burn-sites-pending</link>
                <description><![CDATA[ ]]></description>
                <pubDate>Fri, 25 Sep 2020 22:05:08 +0000</pubDate>
                <dc:creator>mwilson</dc:creator>
                <guid isPermaLink="false">12711 at https://cmo.smcgov.org</guid>
            </item>
        </channel>
    </rss>
    """.encode('utf-8')

    scraper = SanMateoNews()
    items = scraper.parse_feed(mock_rss, SanMateoNews.URL)
    assert 1 == len(items)
    assert 'Health Officer Order Prohibits Removal' == items[0].title


def test_strips_prefixes_from_spanish_title_and_summary() -> None:
    mock_rss = """
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <channel>
            <item>
                <title>17 de septiembre de 2020: ¿Qué es necesario para pasar de morado a rojo?</title>
                <link>https://cmo.smcgov.org/press-release/17-de-septiembre-de-2020-%C2%BFqu%C3%A9-es-necesario-para-pasar-de-morado-rojo</link>
                <description><![CDATA[17 de septiembre de 2020Cualqier resumen.]]></description>
                <pubDate>Sat, 19 Sep 2020 16:14:15 +0000</pubDate>
                <dc:creator>mwilson</dc:creator>
                <guid isPermaLink="false">12656 at https://cmo.smcgov.org</guid>
            </item>
        </channel>
    </rss>
    """.encode('utf-8')

    scraper = SanMateoNews()
    items = scraper.parse_feed(mock_rss, SanMateoNews.URL)
    assert 1 == len(items)
    assert '¿Qué es necesario para pasar de morado a rojo?' == items[0].title
    assert 'Cualqier resumen.' == items[0].summary


def test_drops_news_older_than_from_date() -> None:
    mock_rss = """
    <rss version="2.0">
        <channel>
            <item>
                <title>This item should be kept</title>
                <link>https://cmo.smcgov.org/press-release/sept-25-2020-health</link>
                <description> </description>
                <pubDate>Fri, 25 Sep 2020 22:05:08 +0000</pubDate>
                <guid isPermaLink="false">2</guid>
            </item>
            <item>
                <title>This item should NOT be kept</title>
                <link>https://cmo.smcgov.org/press-release/sept-19-2020-health</link>
                <description> </description>
                <pubDate>Fri, 19 Sep 2020 22:05:08 +0000</pubDate>
                <guid isPermaLink="false">1</guid>
            </item>
        </channel>
    </rss>
    """.encode('utf-8')

    with patch.object(SanMateoNews, 'load_xml', return_value=mock_rss):
        scraper = SanMateoNews(
            from_date=datetime(2020, 9, 20, tzinfo=timezone.utc)
        )
        feed = scraper.scrape()

    assert 1 == len(feed.items)
    assert '2' == feed.items[0].id
