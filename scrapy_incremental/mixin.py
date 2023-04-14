class ScrapyIncrementalItemsMixin:
    items_seen_before = set()

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings["DOWNLOADER_MIDDLEWARES"].update(
            {"scrapy_incremental.middleware.ScrapyIncrementalRequestFilterMiddleware": 100}
        )
        settings["ITEM_PIPELINES"].update(
            {"scrapy_incremental.pipelines.ScrapyIncrementalItemsPipeline": 100}
        )

    def _set_items_seen_before(self, items_set):
        self.items_seen_before = items_set
