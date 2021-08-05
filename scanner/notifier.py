from pynotifier import Notification
from kijiji_scraper import KijijiScraper
import time


URL = ("https://www.kijiji.ca/b-chair-recliner/city-of-toronto/c245l170"
       "0273?ad=offering"
       )
FOLDER = "scanner/data"
MODEL_PATH = "detector/model.pt"
DB_NAME = "scanner/chairs.db"
NUM_ADS = 10  # less than 47
MAX_PRICE = 500
DRIVER_LOC = '/Users/nicholas/chromedriver'
PROB_THRESH = 0.7
TIMEOUT = 30  # seconds


def notify():
    """
    Calls the scrape_ads method from KijijiScraper. Desktop notifications are
    sent for all Kijiji ads that satisfy the desired price and Herman Miller
    probability thresholds declared in the file constants. i.e, ads whose
    probability of being a Herman Miller are greater than or equal to
    PROB_THRESH and whose listed price is less than or equal to MAX_PRICE.

    :return: None
    """
    browser_dict = {"driver_loc": DRIVER_LOC, "timeout": TIMEOUT}
    unique_ids = set()
    scraper = KijijiScraper(
        DB_NAME, MODEL_PATH, MAX_PRICE, FOLDER, PROB_THRESH, NUM_ADS
    )
    notifs = scraper.scrape_ads(URL, browser_dict)
    for ad_id, ad_price in notifs:
        if ad_id in unique_ids:
            continue
        unique_ids.add(ad_id)
        Notification(
            title=str(ad_id),
            description=str(ad_price),
            duration=300,
            app_name="Herman Miller Detector"
        ).send()
        time.sleep(2)


if __name__ == '__main__':
    notify()
