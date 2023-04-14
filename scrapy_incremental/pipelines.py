import logging
import os
import uuid

from itemadapter import ItemAdapter
from scrapinghub import ScrapinghubClient
from scrapinghub.client.exceptions import NotFound
from scrapy.exceptions import DropItem, NotConfigured


DEFAULT_ITEM_UNIQUE_FIELD = "url"
DEFAULT_BATCH_SIZE = 5000


class ScrapyIncrementalItemsPipeline:
    collection_suffix = "_seen_before"

    def __init__(self, sc_key, project_id, item_unique_field, batch_size):
        self.logger = logging.getLogger(__name__)
        self.client = ScrapinghubClient(sc_key)
        self.project = self.client.get_project(project_id)
        self.item_unique_field = item_unique_field
        self.batch_size = batch_size
        self.scraped_items = set()

        if item_unique_field == DEFAULT_ITEM_UNIQUE_FIELD:
            self.logger.info(
                f"Using DEFAULT_ITEM_UNIQUE_FIELD='{DEFAULT_ITEM_UNIQUE_FIELD}' as items ids."
            )

    @classmethod
    def from_crawler(cls, crawler):
        key = crawler.settings.get("SCRAPYCLOUD_API_KEY")
        project_id = (
            crawler.settings.get("SCRAPYCLOUD_PROJECT_ID") or cls.get_project_id()
        )
        batch_size = (
            crawler.settings.get("INCREMENTAL_PIPELINE_BATCH_SIZE")
            or DEFAULT_BATCH_SIZE
        )
        unique_field = (
            crawler.settings.get("INCREMENTAL_PIPELINE_ITEM_UNIQUE_FIELD")
            or DEFAULT_ITEM_UNIQUE_FIELD
        )
        if not key or not project_id:
            raise NotConfigured(
                "The settings 'SCRAPYCLOUD_API_KEY' and 'SCRAPYCLOUD_PROJECT_ID'"
                " are both necessary for ScrapyIncrementalItemsPipeline."
            )
        return cls(
            sc_key=key,
            project_id=project_id,
            item_unique_field=unique_field,
            batch_size=batch_size,
        )

    @classmethod
    def get_project_id(cls):
        return os.environ.get("SHUB_JOBKEY", "").split("/")[0]

    def open_spider(self, spider):
        self.items_seen_before = set()
        if hasattr(spider, "full_crawl") and spider.full_crawl:
            self.logger.info(
                "Spider running in 'full_crawl' mode. ScrapyIncrementalItemsPipeline "
                "will not filter previously scraped items."
            )
            return

        self.items_seen_before = self._get_collection_data(spider)
        if hasattr(spider, "_set_items_seen_before"):
            # Needed if using the middlleware
            spider._set_items_seen_before(self.items_seen_before)

    def _is_full_crawl(self, spider):
        if hasattr(spider, "full_crawl") and spider.full_crawl:
            self.logger.info(
                "Spider running in 'full_crawl' mode. IncrementalItemsPipeline "
                "will not filter previously scraped items."
            )
            return True

    def _get_collection_data(self, spider):
        try:
            store = self.project.collections.get_store(self._get_collection_name(spider))
            collection = {item["item_id"] for item in store.iter()}
            self.logger.info(f"{len(collection)} items found in {spider.name}'s collection")
            return collection
        except NotFound:
            self.logger.info(
                f"Collection '{self._get_collection_name(spider)}' was not found. "
                "It'll be created during the crawling process."
            )
            return set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_id = adapter.get(self.item_unique_field)
        if not item_id:
            self.logger.error(
                f"Unique item field '{self.item_unique_field}' not found in item: {item}"
            )
            return item
        elif item_id in self.items_seen_before:
            raise DropItem(f"Item {item_id} was seen before.")
        else:
            self.scraped_items.add(item_id)
        return item

    def _get_collection_name(self, spider):
        return f"{spider.name}{self.collection_suffix}"

    def close_spider(self, spider):
        store = self.project.collections.get_store(self._get_collection_name(spider))
        for batch in self._batch_scraped_items():
            store.set(batch)
        self.client.close()

    def _batch_scraped_items(self):
        while self.scraped_items:
            batch = []
            while self.scraped_items and len(batch) < self.batch_size:
                batch.append(
                    {"_key": str(uuid.uuid4()), "item_id": self.scraped_items.pop()}
                )
            yield batch
