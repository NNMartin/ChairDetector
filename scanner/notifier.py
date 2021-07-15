from pynotifier import Notification
from kijiji_scraper import KijijiScraper
import time
import warnings


def notify(repeat, unique_ids=set(), wait=300, iter=0):
    if iter >= repeat:
        return None
    url = ("https://www.kijiji.ca/b-chair-recliner/city-of-toronto/c245l170"
           "0273?ad=offering"
           )
    folder = ("/Users/nicholas/Documents/Experimentation/chairDetector"
              "/scanner/data"
              )
    model_path = ("/Users/nicholas/Documents/Experimentation/chairDetector"
                  "/detector/model.pt"
                  )
    db = "chairs.db"
    num_ads = 10  # less than 47
    price = 500
    driver_loc = '/Users/nicholas/chromedriver'
    thresh = 0.7
    timeout = 30

    browser_dict = {"driver_loc": driver_loc, "timeout": timeout}
    scraper = KijijiScraper(db, model_path, price, folder, thresh, num_ads)
    notifs = scraper.scrape_ads(url, browser_dict)
    for ad_id, ad_price in notifs:
        if ad_id in unique_ids:
            continue
        unique_ids.add(ad_id)
        Notification(title=str(ad_id), description=str(ad_price), duration=30)\
            .send()
        time.sleep(2)
    time.sleep(wait)
    notify(repeat=repeat, unique_ids=unique_ids, wait=wait, iter=iter+1)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    notify(5)



