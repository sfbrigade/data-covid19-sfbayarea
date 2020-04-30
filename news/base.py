import requests


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
