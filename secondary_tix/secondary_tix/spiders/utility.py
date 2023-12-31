import os
import sys
import logging
from pathlib import Path
import csv
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)


settings = get_project_settings()
OUTPUT_DIRECTORY = settings.get('OUTPUT_DIRECTORY')
LOG_DIRECTORY = settings.get('LOG_DIRECTORY')


def create_csv(
    file_timestamp: str, 
    website: str, 
    event_date_str: str, 
    headers: list[str]
):
    """
    Create csv with a header row

    file_timestamp: YYYYMMDDHHMM timestamp that will be used for the folder name
    website: name of the website the listings are from
    event_date_str: YYYYMMDD of the event the listings are for
    headers: field names that will be written as the first row of the CSV
    """

    output_dir = OUTPUT_DIRECTORY / f"output/{website}/{file_timestamp}"
    filename = f'{event_date_str}.csv'
    full_path = os.path.join(output_dir, filename)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(full_path):
        try:
            with open(full_path, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(headers)    
            logger.info(f"File successfully created: {full_path}")
        except IOError as e:
            logger.info(f"Error creating file: {e}")
    else:
        logger.info(f"File already exists: {full_path}")

    return full_path

    
def save_to_csv(
        file_timestamp: int, 
        website: str, 
        event_date_str: str, 
        data: list[dict],
        is_append: bool=False
    ):
    """
    Creates CSV if one doesn't exist and writes to it.
    This will be used when the listings for an entire game are provided via one URL

    file_timestamp: YYYYMMDDHHMM timestamp that will be used for the folder name
    website: name of the website the listings are from
    event_date_str: YYYYMMDD of the event the listings are for
    data: list of dictionaries with the listings
    include_headers: True will write a header row in the file and False will skip 
        the header row and just write the data
    is_append: flag to determine if write or append should be used to open the file
        write overwrites the data in the file
        append will append to the end of the file
    """

    output_dir = OUTPUT_DIRECTORY / f"output/{website}/{file_timestamp}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f'{event_date_str}.csv'
    full_path = os.path.join(output_dir, filename)

    keys = data[0].keys() if data else []
    
    logger.info(f"Saving to {full_path}")
    with open(full_path, 'a' if is_append else 'w') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        # Append headers if file opened as "w"
        if not is_append:
            writer.writeheader()
        writer.writerows(data)        


def create_root_logger(output_to_file: bool=False, log_filename: str=None):
    """
    Create a logger 
    
    output_to_file: logs will only be streamed unless this parameter is set to True
        If True, then logs will be output to a file
    log_filename: filename that the logs will be output to
    """

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Get the logger
    logger = logging.getLogger()

    # Reset handlers on the logger
    # Helps avoid multiple handlers
    logger.handlers = []

    # Create a stream handler
    sh = logging.StreamHandler(stream=sys.stderr)

    # Add formatter to stream handler
    sh.setFormatter(formatter)

    # Add stream handler to logger
    logger.addHandler(sh)

    if output_to_file:
        if not os.path.exists(LOG_DIRECTORY):
            os.makedirs(LOG_DIRECTORY)
        fh = logging.FileHandler(LOG_DIRECTORY / log_filename if log_filename else 'log.txt')
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

    # Set logging level
    logger.setLevel(logging.INFO)

    return logger