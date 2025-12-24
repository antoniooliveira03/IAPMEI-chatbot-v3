import scrapy
from bs4 import BeautifulSoup
import re

class Portugal2030TagSpider(scrapy.Spider):
    name = "botscraper_v2"
    start_urls = ["https://european-social-fund-plus.ec.europa.eu/pt"]

    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "DOWNLOAD_DELAY": 1,
    }

    def parse(self, response):
        # Extract visible text
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script, style etc
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        # Yield the main tag page
        yield {
            "url": response.url,
            "type": "html",
            "depth": response.meta.get("depth", 0),
            "text": text
        }

        # Additionally follow links to individual posts on the tag page
        for link in soup.select("article a"):
            href = link.get("href")
            if href and href.startswith("https://portugal2030.pt"):
                yield scrapy.Request(
                    url=href,
                    callback=self.parse_article
                )

    def parse_article(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        yield {
            "url": response.url,
            "type": "html",
            "depth": response.meta.get("depth", 0),
            "text": text
        }
