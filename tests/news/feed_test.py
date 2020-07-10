from covid19_sfbayarea.news.feed import NewsFeed, NewsItem
from datetime import datetime, timezone


def test_feed_items_sort_latest_first() -> None:
    feed = NewsFeed(title='Test Feed')
    a = NewsItem(id='a', title='a', url='a',
                 date_published=datetime(2020, 6, 2, tzinfo=timezone.utc))
    b = NewsItem(id='b', title='b', url='b',
                 date_published=datetime(2020, 6, 3, tzinfo=timezone.utc))
    feed.append(a, b)

    assert feed.items == [b, a]


def test_feed_items_sort_stable() -> None:
    '''
    Unique feed items should always appear in the same order regardless of the
    order in which they were added to the feed.
    '''
    a = NewsItem(id='a', title='a', url='a',
                 date_published=datetime(2020, 6, 2, tzinfo=timezone.utc))
    b = NewsItem(id='b', title='b', url='b',
                 date_published=datetime(2020, 6, 2, tzinfo=timezone.utc))

    feed = NewsFeed(title='Test Feed')
    feed.append(a, b)
    assert feed.items == [b, a]

    # Make sure sorting is still stable even when added in the opposite order
    feed2 = NewsFeed(title='Test Feed 2')
    feed2.append(b, a)
    assert feed.items == [b, a]
