#!/usr/bin/env python3
from bs4 import BeautifulSoup
import json
import re
import requests
from urllib.parse import urljoin


HEADING_PATTERN = re.compile(r'h\d')
ISO_DATETIME_PATTERN = re.compile(r'^\d{4}-\d\d-\d\d(T|\s)\d\d:\d\d:\d\d(\.\d+)?(Z|\d{4}|\d\d:\d\d)$')


def get_base_url(soup, url):
    base = soup.find('base')
    if base and base['href']:
        return urljoin(url, base['href'].strip())
    else:
        return url


class NewsScraper:
    START_URL = None

    def scrape(self):
        # TODO: we may want to iterate through multiple pages in the future
        response = requests.get(self.START_URL)
        response.raise_for_status()
        news = self.parse_page(response.text, self.START_URL)
        return news

    def parse_page(self, html, url):
        raise NotImplementedError()


class SanFranciscoNews(NewsScraper):
    START_URL = 'https://sf.gov/news/topics/794'

    def parse_page(self, html, url):
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        news = []
        articles = soup.main.find_all('article')
        for index, article in enumerate(articles):
            title_link = article.find(HEADING_PATTERN).find('a')

            url = title_link['href']
            if not url:
                raise ValueError(f'Not URL found for article {index}')
            else:
                url = urljoin(base_url, url)

            title = title_link.get_text(strip=True)
            if not title:
                raise ValueError(f'No title content found for article {index}')

            date = article.find('time')['datetime']
            if not ISO_DATETIME_PATTERN.match(date):
                raise ValueError(f'Article {index} date is not in ISO 8601'
                                 f'format: "{date}"')

            news.append({
                'url': url,
                'text': title,
                'date': date
            })

        return news


def main():
    scraper = SanFranciscoNews()
    news = scraper.scrape()
    news_data = {'newsItems': news}
    print(json.dumps(news_data, indent=2))


if __name__ == '__main__':
    main()
