from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import NewsScraper
from .utils import get_base_url, HEADING_PATTERN, ISO_DATETIME_PATTERN


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
