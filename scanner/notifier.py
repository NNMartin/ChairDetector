from pynotifier import Notification
from kijiji_scraper import KijijiScraper
import time


URL = ("https://www.kijiji.ca/b-chair-recliner/city-of-toronto/c245l170"
           "0273?ad=offering"
           )
FOLDER = ("/Users/nicholas/Documents/Experimentation/chairDetector"
          "/scanner/data"
          )
MODEL_PATH = ("/Users/nicholas/Documents/Experimentation/chairDetector"
              "/detector/model.pt"
              )
DB_NAME = "chairs.db"
NUM_ADS = 10  # less than 47
MAX_PRICE = 500
DRIVER_LOC = '/Users/nicholas/chromedriver'
PROB_THRESH = 0.7
TIMEOUT = 30  # seconds


def notify(repeat: int, wait=300):
    """
    Calls the scrape_ads method from KijijiScraper <repeat> number of times. On
    each call, desktop notifications are sent for all Kijiji ads that
    satisfy the desired price and Herman Miller probability thresholds declared
    in the file constants. i.e, ads whose probability of being a Herman Miller
    are greater than or equal to PROB_THRESH and whose listed price is less
    than or equal to MAX_PRICE.

    :param repeat: The number of times to scrape Kijiji consecutively.
    :param wait: The amount of time in seconds to wait between calls of
            scrape_ads.
    :return: None
    """
    browser_dict = {"driver_loc": DRIVER_LOC, "timeout": TIMEOUT}
    unique_ids = set()
    for i in range(repeat):
        scraper = KijijiScraper(
            DB_NAME, MODEL_PATH, MAX_PRICE, FOLDER, PROB_THRESH, NUM_ADS
            )
        notifs = scraper.scrape_ads(URL, browser_dict)
        for ad_id, ad_price in notifs:
            if ad_id in unique_ids:
                continue
            unique_ids.add(ad_id)
            Notification(
                title=str(ad_id), description=str(ad_price), duration=30
                ).send()
            time.sleep(2)
        if i < repeat - 1:
            time.sleep(wait)


if __name__ == '__main__':
    notify(5)



