import scrapy
from scrapy.selector import Selector
import time
from secondary_tix.items import EventListingGametime, EVENT_LISTING_GAMETIME_HEADERS
import logging
from bs4 import BeautifulSoup
from datetime import datetime, date
from .utility import create_csv, save_to_csv

logger = logging.getLogger(__name__)


class MySpider(scrapy.Spider):
    name = 'gametime'
    team = "" # name of team

    current_datetime = datetime.utcnow()
    file_timestamp = current_datetime.strftime("%Y%m%d%H%M")
    
    def start_requests(self):
        """
        Initial request to start the crawler
        """

        yield scrapy.Request(
            url = "", # URL HERE
            callback=self.parse_games,
            meta={"playwright": True, "playwright_include_page": True}
        )        


    async def parse_games(self, response):
        """
        Loop through the games so we can extract listings for each one

        response: request response from call to url
        """

        page = response.meta["playwright_page"]

        # Wait for selector that contains the upcoming events
        await page.wait_for_selector('section._2nM98ETTbcRZ87usbOF3tM')

        # Find the SHOW MORE button at the bottom of the list of games        
        show_more_button = await page.query_selector('button._2fYUaUKGPuVGvKyE_5wB0p')
        logger.info(f"show_more_button exists: {True if show_more_button else False}")

        # Click the SHOW MORE button as long as it exists
        # Only 15 games are initially displayed and each click produces 15 more games
        # May need to click multiple times to display all the games
        click_cnt = 1
        while show_more_button is not None:
            logger.info(f"Clicking SHOW MORE : {click_cnt}")

            # Click on the "Show More" button
            await page.click('button._2fYUaUKGPuVGvKyE_5wB0p')
            
            # Wait for some time to allow the content to load after clicking the button
            await page.wait_for_timeout(5000)
            
            show_more_button = await page.query_selector('button._2fYUaUKGPuVGvKyE_5wB0p')
            logger.info(f"show_more_button exists: {True if show_more_button else False}")
            click_cnt += 1                   

        logger.info("Show more button no longer present. Extracting the HTML from the page")
        updated_events_html = await page.content()

        # Extract all the urls for the games
        soup = BeautifulSoup(updated_events_html, 'html.parser')
        section = soup.find('section', class_='_2nM98ETTbcRZ87usbOF3tM')
        hrefs = [a['href'] for a in section.find_all('a')]
        # Some of the extracted URLS will be for concerts / non sports games
        # This will filter them out
        # HREFs are of the form: /mlb-baseball/AwayTeam-at-HomeTeam-tickets/date-city-venue/events/event_id
        hrefs = [x for x in hrefs if x.split("/")[2].endswith(f"at-{self.team.lower()}-tickets")]
        logger.info(f"# of events = {len(hrefs)}")

        base_url = "https://gametime.co"
        for href in hrefs:
            logger.info(f"{href = }")
            event_url = base_url + href
            logger.info(f"{event_url = }")

            yield scrapy.Request(
                url = event_url,
                callback=self.parse,
                meta={"playwright": True, "playwright_include_page": True}
            )                 


    async def parse(self, response):
        """
        Each event page will contain a dropdown with a selection for Ticket Quantity
        This will loop through all the quantities in the dropdown, click on the button
            to retrieve the listings, and then parse the listings
        
        response: request response from the call to the url
        """

        page = response.meta["playwright_page"]

        # The ticket quantity button will open a dropdown with the ticket quantity
        # options available. We must first click this and then we can click on each 
        # quantity option
        ticket_quantity_button = 'div._3jbsE7bPH2773pyaT0ayCf > :nth-child(2)'
        logger.info(f"ticket_quantity_button exists: {True if ticket_quantity_button else False}")
        await page.click(ticket_quantity_button)   
        
        logger.info("Ticket quantity button clicked, extracting the html")
        updated_html = await page.content()

        selector = Selector(text=updated_html)
        # This element holds all the ticket quantity options available
        ticket_quantity_elements = selector.css("div._1WI7N_Bs_b0gkDH7dzIdkV div._2dcu_9HNIoUpC8-dQyqvMR")
        logger.info(f"Len ticket_quantity_elements = {len(ticket_quantity_elements)}")
        tq_len = len(ticket_quantity_elements)
        logger.info(f"{tq_len} ticket quantity elements")

        # Loop through the ticket quantities and click each one
        # The listings for the quantity selected will appear on the side of the screen
        # Once we are done with the given quantity, we will need to click on the 
        # ticket quantity button again before we can click on the next quantity
        for i in range(1,tq_len+1):
            # Extract the ticket quantity
            div_element = selector.css(f'div#{i}')
            tickets_text = div_element.css('span._7in0Cl45Y3DqI27Uw8KET::text').get()
            # tickets_text = div_element.css('span._7in0Cl45Y3DqI27Uw8KET::text')[i].get()
            ticket_quantity = tickets_text.split(" ")[0]
            logger.info(f"{ticket_quantity = }")

            logger.info(f"Clicking the button for ticket quantity {ticket_quantity}")
            tq_button = f'div._1WI7N_Bs_b0gkDH7dzIdkV > :nth-child({i})'
            await page.click(tq_button)

            # Extract the html so we can then parse the listings from it
            listings_html = await page.content()
            soup = BeautifulSoup(listings_html, 'html.parser')

            await self.parse_listings(soup, ticket_quantity)
 
            # Click on the ticket quantity button again so we can then click
            # on the next quantity
            if i < tq_len:
                time.sleep(2)
                logger.info("Clicking ticket quantity button...")
                ticket_quantity_button = 'div._3jbsE7bPH2773pyaT0ayCf > :nth-child(2)'
                await page.click(ticket_quantity_button)

        await page.close()


    async def event_info(self, listings_soup: BeautifulSoup):
        """
        Extract event info from the html

        listings_soup: BeautifulSoup object of the html page of ticket listings
        return: event_date (string in YYYY-MM-DD format) and opponent
        """

        logger.info("Parsing the event info")
        title = listings_soup.title.text
        title_split = title.split(" - ")
        opponent = title_split[0].split(" at ")[0]
        event_date_raw = title_split[1].split(" at ")[0]
        logger.info(f"{event_date_raw = }")
        event_date = datetime.strptime(event_date_raw, "%m/%d/%y")
        event_date = event_date.strftime("%Y-%m-%d") 
        logger.info(f"{event_date = }, {opponent = }")
        
        return event_date, opponent 


    async def parse_listings(
        self, 
        listings_soup: BeautifulSoup, 
        quantity: int
    ):
        """
        Loop through all the listings and extract relevant info

        listings_soup: BeautifulSoup object of the html page of ticket listings
        quantity: # of tickets in the listing
            Each listings_soup contains a single quantity of tix per listing
        """

        event_date, opponent = await self.event_info(listings_soup)
        event_date_str = event_date.replace("-","")

        # Create a CSV that the listings will be appended to
        # If file already exists it won't be recreated
        # All listings for a game will be written to the same file
        csv_file_path = create_csv(
            self.file_timestamp, 
            self.name, 
            event_date_str, 
            EVENT_LISTING_GAMETIME_HEADERS
        )   

        # This element contains all of the listings
        div_elements = listings_soup.find_all('div', class_='_2h7x6MAQ0R9rPi2f7MFJXo')

        all_listings = []
        for div_elem in div_elements:
            # Extract section / row
            section_row = div_elem.select_one('div._1EShqotjRsBqatpuDDtfZ7 ._1-M9Q0QPzQQPipMVX0voMp').text
            logger.info(f"{section_row = }")
            section = section_row.split(",")[0].strip()
            row = section_row.split(",")[1].replace("Row","").strip()

            # Extract price
            price = div_elem.select_one('div._1Ez1uMaistdU48Vpp8XeO2 span').text
            price = price.replace("/ea","").replace("$","").replace(",","")
            logger.info(f"{section}, {row}, {price}")
         
            event_listing = EventListingGametime()
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

        logger.info(f"# listings for ticket quantity {quantity}: {len(all_listings)}")

        save_to_csv(
            self.file_timestamp, 
            self.name, 
            event_date_str, 
            all_listings, 
            is_append=True
        )   