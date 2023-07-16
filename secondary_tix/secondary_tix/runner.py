from scrapy.crawler import CrawlerProcess
from spiders.gametime_selenium import MySpider

process = CrawlerProcess(settings={
    'SELENIUM_DRIVER_NAME': 'chrome',
    'SELENIUM_DRIVER_EXECUTABLE_PATH': '/users/jimmymorrow/downloads/chromedriver',
    'SELENIUM_DRIVER_ARGUMENTS': ['--headless'],  # Optional: Run in headless mode
})
process.crawl(MySpider)
process.start()
