import scrapy
import io
import re
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
import logging

# Silence PDF miner DEBUG logs
logging.getLogger("pdfminer").setLevel(logging.WARNING)


class Portugal2030Spider(scrapy.Spider):
    name = "botscraper"
    start_urls = ["https://www.iapmei.pt/"]

    allowed_domains = ["iapmei.pt", "www.iapmei.pt"]

    # ---------- Helpers ----------

    def errback_log(self, failure):
        """Log failed requests without crashing the spider."""
        self.logger.warning(f"Request failed: {failure.request.url} - {failure.value}")

    def extract_main_html(self, html):
        """Remove header/footer/nav to avoid crawling menu links repeatedly."""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["header", "nav", "footer", "aside"]):
            tag.decompose()
        main = soup.find("main")
        if main:
            return str(main)
        if soup.body:
            return str(soup.body)
        return None

    def extract_html_text(self, html):
        """Extract and clean visible text from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        if not soup.body:
            return None
        return self.clean_text(soup.body.get_text(" ", strip=True))

    def clean_text(self, text):
        """Standard cleaning: remove excessive dots, whitespace, and line breaks."""
        if not text:
            return ""
        text = re.sub(r'\.{3,}', ' ', text)              # remove dot leaders
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        return text.strip()

    # ---------- Spider Logic ----------
    def parse(self, response):
        # Skip pages whose URL contains "arquivo"
        if "arquivo" in response.url.lower():
            self.logger.info(f"Skipping arquivo page: {response.url}")
            return  # skip processing this page entirely

        content_type = response.headers.get("Content-Type", b"").decode().lower()
        is_html = "text/html" in content_type

        text = None
        if is_html:
            text = self.extract_html_text(response.text)

            link_extractor = LinkExtractor(
                allow_domains=self.allowed_domains,
                unique=True
            )

            for link in link_extractor.extract_links(response):
                # Skip unwanted links
                if any(x in link.url.lower() for x in ["login", "cookies", "privacy", "termos", "arquivo", 
                                                       "ligacoes-uteis", "politica-de", "legislacao", 
                                                       "aviso-2024", "2023", "operacao", "regulamentacao",
                                                       "operacoes", "pt/en/", "REACH"]):
                    continue

                yield response.follow(
                    link.url,
                    callback=self.parse,
                    errback=self.errback_log
                )

        # Yield the page
        if text:
            yield {
                "url": response.url,
                "type": "html",
                "depth": response.meta.get("depth", 0),
                "text": text
            }
