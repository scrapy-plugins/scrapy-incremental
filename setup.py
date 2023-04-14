from setuptools import setup, find_packages

setup(
    name="scrapy-incremental",
    version="0.1",
    description=(
        "The package uses Zyte's Collections API to keep a persistent state of previously scraped "
        "items between jobs, allowing the spiders to run in an incremental behavior, only returning"
        "new items."
    ),
    packages=find_packages(),
    install_requires=[
        "scrapy",
        "scrapinghub[msgpack]",
    ],
)
