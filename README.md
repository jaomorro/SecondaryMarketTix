## Legal Disclaimer
One should always review the websites and their policies before doing any web scraping.

## Overview
This will extract listings for the events from the provided starting URL in each spider. You will need to add the URLs to the spiders before running.

  - Gametime (gametime.py)
    - Go to the `https://gametime.co`
    - Seach for the Venue you are interested in
    - Copy/Paste the URL into the `start_requests` function

  - Vivid (vivid.py)
    - Go to `https://www.vividseats.com/`
    - Search for your team
    - Filter for Home Games only
    - Copy/Paste the URL into the `start_urls` attribute

Listings will be output to the directory provided in the `OUTPUT_DIRECTORY` variable in
    `settings.py`. By default the output directory is a folder called `output` in the root of the project directory.
Each spider run will create a folder with the name `[spider]YYYYMMDDHHMM` and the listings will be saved to a CSV called `[game_date].csv`
  - `YYYYMMDDHHMM` is the timestamp of when the spider was initiated
  - `[spider]` is the name of the spider (ex - gametime)
  - Listings for each game will be loaded into their own file


## Setup
Packages can be found in `requirements.txt`
Packages can be installed via: `pip install -r requirements.txt`

This is configured to use user-agent headers generated via `scraperops`. To use this, you will need to do the following:
1. Go to `https://scrapeops.io/`
2. Create an account
3. An account API key will be generated for you with your account
4. Create a `config.cnf` file in the root directory of the project
5. Add the following to the file, replacing `API_KEY` with your api key
```
[credentials]
SCRAPEOPS_API_KEY = API_KEY
```

## How to run
cd to the folder that contains `scrapy.cfg` (`[root]/secondary_tix`)

The following will extract listings for all events
  - `scrapy crawl gametime -a team=[team-name]`
    - `team` is a required argument and is just the team nickname of the team whose tickets you are interested in. Ex - dodgers
  - `scrapy crawl vivid`

If you only want a single event, you can use the `event_date` argument
  - `scrapy crawl gametime -a team=dodgers -a event_date=2023-07-29`
  - `scrapy crawl vivid -a event_date=2023-07-29`

By default there is a 15 second download delay but this can be changed in the 
    settings.py file `- DOWNLOAD_DELAY` variable. 
You can also alter this by adding `-s DOWNLOAD_DELAY=XX` to the end of the scrapy crawl command. Download delay defines how many seconds will be in between each URL request.