import scrapy
import pdfplumber
import io
import re
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor

class Portugal2030Spider(scrapy.Spider):
    name = "botscraper"
    allowed_domains = ["portugal2030.pt"]
    start_urls = ["https://portugal2030.pt/"]

    # Seed keywords
    seed_keywords = ["aviso", "avisos", "programa", "programas"]

    def parse(self, response):
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        text = None

        # Extract content if HTML or PDF
        if "text/html" in content_type:
            text = self.extract_html_text(response.text)
        elif "application/pdf" in content_type:
            text = self.extract_pdf_text(response.body)

        # Yield only if relevant
        if text and (any(kw in response.url.lower() for kw in self.seed_keywords) or "application/pdf" in content_type):
            yield {
                "url": response.url,
                "type": "pdf" if "application/pdf" in content_type else "html",
                "depth": response.meta.get("depth", 0),
                "text": text
            }

        # Follow links
        # If the current page is a seed page or PDF, follow all internal links
        if any(kw in response.url.lower() for kw in self.seed_keywords) or "application/pdf" in content_type:
            link_extractor = LinkExtractor(allow_domains=self.allowed_domains)
            for link in link_extractor.extract_links(response):
                yield scrapy.Request(link.url, callback=self.parse)

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
