import scrapy
import pdfplumber
import io
import re
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse



class Portugal2030Spider(scrapy.Spider):
    name = "botscraper"
    allowed_domains = ["portugal2030.pt", "www.portugal2030.pt"]
    start_urls = ["https://portugal2030.pt/"]

    def same_host(self, url):
        host = urlparse(url).netloc.lower()
        return host in {"portugal2030.pt", "www.portugal2030.pt"}

    def parse(self, response):
        content_type = response.headers.get("Content-Type", b"").decode().lower()

        text = None
        is_pdf = response.url.lower().endswith(".pdf") or "application/pdf" in content_type
        is_html = "text/html" in content_type

        # ---- Extract content ----
        if is_html:
            text = self.extract_html_text(response.text)
        elif is_pdf:
            text = self.extract_pdf_text(response.body)

        # ---- Yield item ----
        if text:
            yield {
                "url": response.url,
                "type": "pdf" if is_pdf else "html",
                "depth": response.meta.get("depth", 0),
                "text": text
            }

        # ---- FOLLOW LINKS ONLY FROM HTML ----
        if is_html:
            link_extractor = LinkExtractor()
            for link in link_extractor.extract_links(response):
                if self.same_host(link.url):
                    yield response.follow(
                        link.url,
                        callback=self.parse,
                        errback=self.errback_log
                    )



    # ---- Extraction Helpers ----
    def extract_html_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        if not soup.body:
            return None
        return self.clean_text(soup.body.get_text(" ", strip=True))

    def extract_pdf_text(self, content):
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
