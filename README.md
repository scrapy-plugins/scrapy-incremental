# scrapy-incremental

scrapy-incremental is a package that uses Zyte's [Collections API](https://docs.zyte.com/scrapy-cloud/reference/http/collections.html) to keep a persistent state of previously scraped items between jobs, allowing the spiders to run in an incremental behavior, returning only new items.

## Getting Started

### Installation

You can install scrapy-incremental using pip:

```bash
pip install scrapy-incremental
```

### Settings

- `SCRAPYCLOUD_API_KEY` **must be set** in your `settings.py`, otherwise the plugin will be disabled on start.
- `SCRAPYCLOUD_PROJECT_ID` It's your the project's ID assigned by Scrapy Cloud. If the code is running on Scrapy Cloud **the package will infer the project ID** by the environment variables. However if running in other enviorments it must be set on the `settings.py`, otherwise the plugin will be disabled on start.

`scrapy-incremental` stores a reference of each scraped item in a Collections store named after each individual spider and compares that reference to know if the item in process was already scraped in previous jobs. 

The **reference used by default** is the field `url` inside the item. If your Items don't contain a `url` field you can change the reference by setting the `INCREMENTAL_PIPELINE_ITEM_UNIQUE_FIELD` to the field name you want. The new field **must be a field that contains unique data for that item**, otherwise the pipeline won't behave as expected. 

## Usage
### Pipeline

Enabling the `ScrapyIncrementalItemsPipeline` in your project's settings `ITEM_PIPELINES` is the simplest and most flexible way to add the incremental features to your spiders.

```python
ITEM_PIPELINES = {
    'scrapy_incremental.pipelines.ScrapyIncrementalItemsPipeline': 100,
    #...
}
```

The pipeline will compare the unique field of each item against the references stored in the collections and if they are present the item will be dropped. At the end of the crawling process the collection's store will be updated with the newly scraped items.

**The pipeline alone won't prevent making requests to items scraped before,** in order to avoid unnecessary requests you will need to use the `ScrapyIncrementalItemsMixin`.

### ScrapyIncrementalItemsMixin

The `ScrapyIncrementalItemsMixin` will enable both the `ScrapyIncrementalRequestFilterMiddleware` and the `ScrapyIncrementalItemsPipeline`. The purpose of `ScrapyIncrementalRequestFilterMiddleware` is to filter requests to URLs that had been scraped in previous jobs and were present in the Items. The use of the middleware is optional and only meant to avoid unnecessary requests.

For this to be effective the references kept in the collections **must be of the URL of each item's page**. Therefore your items must either have the `url` field that contains the URL to the item's page or if using a different field defined in `INCREMENTAL_PIPELINE_ITEM_UNIQUE_FIELD` it must meet this same criteria.

```python
from scrapy.spiders import Spider
from scrapy_incremental import IncrementalItemsMixin

class MySpider(IncrementalItemsMixin, Spider):
    name = 'myspider'
    # ...
```

### Configuration

#### Crawling previously seen Items / Temporarily disabling the incremental features.

To temporarily disable the incremental feature of your spiders you can just pass the argument `full_crawl=True` when executing them.

```bash
scrapy crawl myspider -a full_crawl=True
```

#### INCREMENTAL_PIPELINE_BATCH_SIZE

When stopping the crawling process, the pipeline will update the Collection's store with the newly scraped items. This is automatically done in batches of 5000. 

If you are facing issues in this process you may want to change the batch size, which can be done by setting an integer value to the setting `INCREMENTAL_PIPELINE_BATCH_SIZE`.


## License

This project is licensed under the [LICENSE](LICENSE.txt) file for details.