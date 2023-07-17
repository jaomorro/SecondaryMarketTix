import scrapy
from secondary_tix.items import EventListing
from bs4 import BeautifulSoup
from scrapy.selector import Selector
from datetime import datetime
import logging
from .utility import save_to_csv, create_root_logger

logger = create_root_logger(
    output_to_file=False, # Set to True to output logs to file
    log_filename=f'vivid_{datetime.now().strftime("%Y%m%d%H%M")}.log'
)


class VividSpider(scrapy.Spider):
    name = "vivid"
    allowed_domains = ["https://www.vividseats.com", "www.vividseats.com"]
    start_urls = [] # Put your URL in the list

    def __init__(self, event_date=None, *args, **kwargs):
        super(VividSpider, self).__init__(*args, **kwargs)
        self.event_date_filter = event_date
        if self.event_date_filter is not None:
            logger.info(f"Will be filtering for event date: {self.event_date_filter}")
        current_datetime = datetime.utcnow()
        self.file_timestamp = current_datetime.strftime("%Y%m%d%H%M%S")


    def parse(self, response):
        """
        Response received will be the Vivid homepage for the teams's games
        This page contains links to all the upcoming games
        We will loop through the list and extract the event id for each game
        We will then pass the event id into the AJAX URL which sends us to a page
            with a JSON of all the listings
        """

        logger.info(f"Response status = {response.status}")
        events = response.css('div.styles_box__QqP94 a.styles_link__1Scjm')
        for event in events:
            extracted_event_date = event.css('p.styles_md__1m2cS.styles_semi-bold__d780p::text').get()
            logger.info(f"{extracted_event_date = }")
            event_date = self.format_event_date_filter(extracted_event_date)
            logger.info(f"{event_date = }")
            event_title = event.css('div.styles_col__2dlgD p.styles_md__1m2cS.styles_semi-bold__d780p::text').get()
            logger.info(f"{event_title = }")
            event_url = event.attrib['href']
            logger.info(f"{event_url = }")
            event_id = event_url.split("/")[-1]
            logger.info(f"{event_id = }")

            # If event date filter is provided, and it doesn't equal the current
            #   event in the loop, then continue / don not call the URL
            if self.event_date_filter is not None:
                if self.event_date_filter != event_date:
                    logger.info(f"{self.event_date_filter} <> {event_date}")
                    continue

            # This URL will send us to a JSON of all the listings for the game
            ajax_url = f"https://www.vividseats.com/hermes/api/v1/listings?productionId={event_id}&includeIpAddress=true&priceGroupId=277"
            logger.info(f"{ajax_url = }")
            yield response.follow(
                ajax_url, 
                callback=self.parse_event_page, 
                meta={"event_date": event_date, "event_title": event_title}
            )


    def format_event_date_filter(self, event_date_to_format: str)->str:
        """
        Format event date into YYYY-MM-DD format
            Ex: July 24 -> 2023-07-24
        """

        date_obj = f"{event_date_to_format} {datetime.now().year}"
        date_obj = datetime.strptime(date_obj, "%b %d %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date


    def parse_event_page(self, response):
        """
        Parse the listings and save them as a CSV
        The response received is a JSON of all the listings for a given game
        """

        all_listings = []

        event_date = response.meta.get('event_date')
        # date_obj = f"{date_obj} {datetime.now().year}"
        # date_obj = datetime.strptime(date_obj, "%b %d %Y")
        # event_date = date_obj.strftime("%Y-%m-%d")

        event_title = response.meta.get("event_title")
        event_title_split = event_title.find(" at ")
        opponent = event_title[:event_title_split]

        logger.info(f"{event_date = }, {opponent = }")

        event_date_str = event_date.replace("-","")

        all_event_data = response.json()
        tickets = all_event_data["tickets"]
        for ticket in tickets:
            event_listing = EventListing()
            section = ticket["s"]
            row = ticket["r"]
            quantity = ticket["q"]
            price = ticket["p"]    
            event_listing["event_date"] = event_date
            event_listing["opponent"] = opponent 
            event_listing["section"] = section
            event_listing["row"] = row
            event_listing["quantity"] = quantity
            event_listing["price"] = price 
            # current time in YYYY-MM-DD H:M:S format
            event_listing["listing_valid_as_of"] = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
            logger.debug(f"{event_listing = }")
            all_listings.append(event_listing)

        save_to_csv(self.file_timestamp, self.name, event_date_str, all_listings)   

        





