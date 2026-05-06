# Libraries
from scrapy.utils.project import get_project_settings
import os
import json

class PerSiteJsonWriter:
    """
    Writes scraped items into separate files per site.
    """

    def open_spider(self, spider):
        self.files = {}
        settings = get_project_settings()

        # Output directory
        self.base_path = settings.get("DATA_BASE_PATH")

        os.makedirs(self.base_path, exist_ok=True)

        spider.logger.info(f"Pipeline initialized at {self.base_path}")

    def close_spider(self, spider):
        # Close all open file handles safely
        for site, f in self.files.items():
            try:
                f.close()
            except Exception as e:
                spider.logger.warning(f"Error closing {site}: {e}")

        spider.logger.info("Pipeline closed successfully")

    def process_item(self, item, spider):
        site = item.get("site")

        if not site:
            site = "unknown"
            spider.logger.warning(f"Missing site field for URL: {item.get('url')}")

        # Create file lazily (only when needed)
        if site not in self.files:
            filepath = os.path.join(
                self.base_path,
                f"{site}.json"
            )

            try:
                self.files[site] = open(filepath, "w", encoding="utf-8")
                spider.logger.info(f"Created file for site: {site}")
            except Exception as e:
                spider.logger.error(f"Failed to open file {site}: {e}")
                return item

        # Write item
        f = self.files[site]

        try:
            f.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        except Exception as e:
            spider.logger.error(f"Write error for {site}: {e}")

        return item