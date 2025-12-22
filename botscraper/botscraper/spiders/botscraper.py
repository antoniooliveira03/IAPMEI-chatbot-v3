import scrapy
import pdfplumber
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
    allowed_domains = ["portugal2030.pt", "www.portugal2030.pt"]
    start_urls = ["https://portugal2030.pt/"]

    # ---------- Helpers ----------
    def same_host(self, url):
        """Allow only exact portugal2030.pt domains (no subdomains)."""
        host = urlparse(url).netloc.lower()
        return host in {"portugal2030.pt", "www.portugal2030.pt"}

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

    def extract_pdf_text(self, content):
        """Extract and clean text from PDFs."""
        pages = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages.append(page_text)
        except Exception as e:
            self.logger.warning(f"Failed to extract PDF: {e}")
        if not pages:
            return None
        return self.clean_text("\n\n".join(pages))

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
        content_type = response.headers.get("Content-Type", b"").decode().lower()
        is_pdf = response.url.lower().endswith(".pdf") or "application/pdf" in content_type
        is_html = "text/html" in content_type

        text = None
        if is_html:
            text = self.extract_html_text(response.text)
        elif is_pdf:
            text = self.extract_pdf_text(response.body)

        # Yield the page/PDF
        if text:
            yield {
                "url": response.url,
                "type": "pdf" if is_pdf else "html",
                "depth": response.meta.get("depth", 0),
                "text": text
            }

        # FOLLOW LINKS ONLY FOR HTML
        if is_html:
            cleaned_html = self.extract_main_html(response.text)
            if not cleaned_html:
                return

            # Create a temporary response with cleaned HTML
            fake_response = response.replace(body=cleaned_html)

            link_extractor = LinkExtractor(
                allow_domains=self.allowed_domains,
                unique=True
            )

            for link in link_extractor.extract_links(fake_response):
                if self.same_host(link.url):
                    # Skip obvious junk pages (login, privacy, termos)
                    if any(x in link.url.lower() for x in ["login", "cookies", "privacy", "termos"]):
                        continue
                    yield response.follow(
                        link.url,
                        callback=self.parse,
                        errback=self.errback_log,
                        dont_filter=False
                    )
