import os

from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapinghub import ScrapinghubClient


class ScrapyIncrementalRequestFilterMiddleware:
    def __init__(self, sc_key, project_id):
        self.client = ScrapinghubClient(sc_key)
        self.project = self.client.get_project(project_id)

    @classmethod
    def from_crawler(cls, crawler):
        key = crawler.settings.get("SCRAPYCLOUD_API_KEY")
        project_id = (
            crawler.settings.get("SCRAPYCLOUD_PROJECT_ID") or cls.get_project_id()
        )
        if not key or not project_id:
            raise NotConfigured(
                "The settings 'SCRAPYCLOUD_API_KEY' and 'SCRAPYCLOUD_PROJECT_ID'"
                " are both necessary for ScrapyIncrementalRequestFilterMiddleware."
            )
        return cls(sc_key=key, project_id=project_id)

    @classmethod
    def get_project_id(cls):
        return os.environ.get("SHUB_JOBKEY", "").split("/")[0]

    def process_request(self, request, spider):
        if hasattr(spider, "full_crawl") and spider.full_crawl:
            self.logger.info(
                "Spider running in 'full_crawl' mode. ScrapyIncrementalRequestFilterMiddleware "
                "will not filter requests."
            )
            return

        if request.url in spider.items_seen_before:
            raise IgnoreRequest(f"{request.url} was seen before.")
