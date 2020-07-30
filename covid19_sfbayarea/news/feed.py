"""
Tools for modeling news feeds and serializing to multiple formats.
"""

from dataclasses import dataclass, field, fields
from datetime import datetime
import json
import locale
from lxml.builder import E  # type: ignore
import lxml.etree as ElementTree  # type: ignore
from operator import attrgetter
from typing import Dict, List, Optional, Any


def format_datetime_8601(date_obj: datetime) -> str:
    """
    Get an ISO 8601-formatted string for a datetime, but ensure that UTC is
    represented with the shortened 'Z' form (i.e. W3C-style).
    """
    formatted = date_obj.isoformat()
    if formatted.endswith('+00:00'):
        formatted = formatted[:-6] + 'Z'
    return formatted


def format_datetime_2822(date_obj: datetime) -> str:
    """
    Get an RFC 2822-formatted string for a datetime.
    """
    old = locale.setlocale(locale.LC_ALL)
    locale.setlocale(locale.LC_ALL, 'C')
    date = date_obj.strftime('%a, %d %b %Y %H:%M:%S %z')
    locale.setlocale(locale.LC_ALL, old)
    return date


@dataclass
class NewsItem:
    id: str
    # Technically url, title, and date_published are optional, but in practical
    # terms, we require them to always be set.
    url: str
    title: str
    date_published: datetime = field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    date_modified: Optional[datetime] = None
    author: Optional[Dict[str, str]] = None
    tags: List[str] = field(default_factory=list)

    def format_json_simple(self) -> Dict:
        return {
            'url': self.url,
            'text': self.title,
            'date': format_datetime_8601(self.date_published)
        }

    def format_json_feed(self) -> Dict:
        if not self.id:
            raise ValueError('You must specify an `id` for this news item')

        result = {}
        for item_field in fields(self):
            value = getattr(self, item_field.name)
            if value:
                if isinstance(value, datetime):
                    value = format_datetime_8601(value)
                result[item_field.name] = value

        return result

    def format_rss(self) -> ElementTree.Element:
        tags = (E('category', tag) for tag in (self.tags or []))
        return E.item(
            E('guid', self.id),
            E('title', self.title),
            E('link', self.url),
            E('pubDate', format_datetime_2822(self.date_published)),
            *tags
        )


@dataclass
class NewsFeed:
    title: str
    home_page_url: Optional[str] = None
    feed_url: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    # dict with keys: 'name', 'url', 'avatar' (all optional)
    author: Optional[Dict[str, str]] = None
    expired: bool = False
    items: List[NewsItem] = field(default_factory=list, init=False)

    def append(self, *items: NewsItem) -> None:
        self.items.extend(items)
        self.sort_items()

    def sort_items(self) -> None:
        # Sort primarily by date, then ID. Since date_published can be a
        # date + time but, in practice, is often just a date, we frequently see
        # items get shuffled between scraping runs because date_published is
        # not very unique. Use the ID a [relatively] stable secondary criteria.
        self.items.sort(reverse=True, key=attrgetter('id'))
        self.items.sort(reverse=True, key=attrgetter('date_published'))

    def format_json_simple(self, pretty: bool = True) -> bytes:
        indent = 2 if pretty else None
        data = json.dumps(self.format_json_simple_dict(), indent=indent)
        return data.encode('utf-8')

    def format_json_simple_dict(self) -> Dict:
        """
        Output this news feed in a simplified JSON format. The output is a
        JSON-serializable dict; not an actual string.

        Returns
        -------
        dict
        """
        return {
            'newsItems': [item.format_json_simple() for item in self.items]
        }

    def format_json_feed(self, pretty: bool = True) -> bytes:
        indent = 2 if pretty else None
        data = json.dumps(self.format_json_feed_dict(), indent=indent)
        return data.encode('utf-8')

    def format_json_feed_dict(self) -> Dict:
        """
        Output this news feed in JSON Feed format (https://jsonfeed.org/). The
        output is a JSON-serializable dict; not an actual string.

        Returns
        -------
        dict
        """
        if not self.title:
            raise ValueError('You must specify a `title` for this feed')

        feed: Dict[str, Any] = {
            'version': 'https://jsonfeed.org/version/1'
        }
        for item_field in fields(self):
            if item_field.name == 'items':
                value = [item.format_json_feed() for item in self.items]
            else:
                value = getattr(self, item_field.name)
            if value:
                feed[item_field.name] = value

        return feed

    # TODO: revisit whether this should really return a string -- when the XML
    # is serialized to bytes in a file, it should ideally have an XML encoding
    # declaration at the top, but `ElementTree.tostring` very reasonably won't
    # output that if you're asking for a string (`encoding='unicode'`) back
    # instead of bytes (e.g. with `encoding='utf-8'`).
    def format_rss(self, pretty: bool = True) -> bytes:
        """
        Output this news feed in RSS 2.0 format.
        https://www.rssboard.org/rss-specification

        Parameters
        ----------
        pretty
            Whether to "pretty print" the XML so there's generally one element
            per line, instead of shoving it all together in the most compact
            possible representation. (Default: True)

        Returns
        -------
        str
            An XML string. Note this is a *string*, not bytes, so you may want
            to add an XML encoding header (e.g.
            `<?xml version="1.0" encoding="UTF-8"?>`) when writing to disk.
        """
        if not self.title:
            raise ValueError('You must specify a `title` for this feed')
        if not self.home_page_url:
            raise ValueError('You must specify a `home_page_url` for this feed')

        rss = E.rss(
            E.channel(
                E('title', self.title),
                E('link', self.home_page_url),
                # Description is required in RSS 2.0, but we don't always
                # have anything useful to put there.
                E('description', self.description or ''),
                *(item.format_rss() for item in self.items)
            ),
            {'version': '2.0'}
        )

        return ElementTree.tostring(rss, encoding='utf-8', pretty_print=pretty,
                                    xml_declaration=True)
