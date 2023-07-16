# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SecondaryTixItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


# class GameItem(scrapy.Item):
#     game_date = scrapy.Field()
#     start_time = scrapy.Field()
#     game_title = scrapy.Field()
#     game_url = scrapy.Field()


class EventListing(scrapy.Item):
    event_date = scrapy.Field()
    opponent = scrapy.Field()
    section = scrapy.Field()
    row = scrapy.Field()
    quantity = scrapy.Field()
    price = scrapy.Field()
    listing_valid_as_of = scrapy.Field()


class EventListingGametime(scrapy.Item):
    event_date = scrapy.Field()
    opponent = scrapy.Field()
    section = scrapy.Field()
    row = scrapy.Field()
    quantity = scrapy.Field()
    price = scrapy.Field()
    listing_valid_as_of = scrapy.Field()

EVENT_LISTING_GAMETIME_HEADERS = [
    "event_date",
    "opponent",
    "section",
    "row",
    "quantity",
    "price",
    "listing_valid_as_of"
]
