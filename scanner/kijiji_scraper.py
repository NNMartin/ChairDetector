from selenium.common.exceptions import ElementNotInteractableException
from datetime import datetime
import classify
import chair_sqlite
import browserconn


class KijijiAd(dict):
    def __init__(self, ad_id, time, probs, price, names, *args, **kwargs):
        super(KijijiAd, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.id = ad_id
        self.time = time
        self.probs = probs
        self.names = names
        self.price = price
        self.var_names = "(:id, :date, :prob, :price, :filename)"

    def has_hm(self, threshold=0.7):
        return max(self.probs) >= threshold

    def get_ith_value_dict(self, i):
        return {
            "id": self.id,
            "date": self.time,
            "prob": self.probs[i],
            "price": self.price,
            "filename": self.names[i]
            }

    def insert_into_db(self, db_conn):
        for i in range(len(self.names)):
            item_dict = self.get_ith_value_dict(i)
            chair_sqlite.insert(db_conn, self.var_names, item_dict)


class KijijiScraper:
    def __init__(self, db, model_path, max_price, folder, thresh):
        self.db = chair_sqlite.open_conn(db_name=db)  # tuple
        self.max_price = max_price
        self.model_path = model_path
        self.notifs = []
        self.folder = folder
        self.thresh = thresh

    def _init_model(self):
        return classify.init_model(self.model_path)

    def init_browser_conn(self, driver_loc, timeout, headless):
        return browserconn.BrowserConnection(driver_loc, timeout, headless)

    def new_id(self, ad_id):
        """ check if ad_id is in the database"""
        return chair_sqlite.is_in_db(self.db, ad_id, "id")

    def insert_into_db(self, ad):
        """ inserts ad into database
        """
        ad.insert_into_db(self.db)

    def _close_db(self):
        chair_sqlite.close_db(self.db)

    def _quit_browser(self, conn):
        conn.quit_conn()

    def scrape_images(self, conn, time, model):
        names, predictions = [], []
        try:
            for i, image in enumerate(conn.get_images()):
                if image is None:
                    continue
                name = "{}/{}_{}.png".format(self.folder, time, str(i))
                names.append(name)
                [predictions].append(classify.hm_prob(image, name, model))
            return names, predictions
        except ElementNotInteractableException:
            return None

    def scrape_ad(self, web_ad, conn, model):
        ad_dict = {}
        ad_title = web_ad.find_element_by_class_name("title")
        # ad_link = ad_title.find_element_by_tag_name("a").get_attribute("href")
        conn.click_element(ad_title, "xpath", '../../..').click()
        ad_dict["id"] = conn.get_id()
        if ad_dict["id"] is None or not self.new_id(ad_dict["id"]):
            conn.go_back_n_pages()
            return None
        ad_dict["time"] = current_time()
        ad_dict["price"] = conn.get_price()
        scraped_data = self.scrape_images(conn, ad_dict["now"], model)
        if scraped_data is not None:
            ad_dict["names"], ad_dict["probs"] = scraped_data
            ad = KijijiAd(**ad_dict)
            if ad.has_hm(self.thresh) and ad.price <= self.max_price:
                self.notifs.append((ad.id, ad.price))
            self.insert_into_db(ad)
        conn.go_back_n_pages()

    def scrape_ads(self, browser_dict):
        model = self._init_model()
        conn = self.init_browser_conn(**browser_dict)
        num_ads, _ = conn.get_ads(1)
        for i in range(1, num_ads):
            _, web_ad = conn.get_ads(i)
            self.scrape_ad(web_ad, conn, model)
        self._quit_browser(conn)
        self._close_db()
        return self.notifs


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    url = "https://www.kijiji.ca/b-chair-recliner/city-of-toronto/c245l1700273?ad=offering" # Main starting point
    id_xpath = '//*[@id="ViewItemPage"]/div[3]/div/ul/li[7]/a'
    #ad_xpath = '//*[@id="mainPageContent"]/div[3]/div[3]/div[3]/div[4]/div'
    images_xpath = '//*[@id="PageVIP"]/div[12]/div/div/div[2]/ul/li[1]/div/img'
    images_class_name = "image-376491912"
    images_ind = -10
    gallery_xpath = '//*[@id="mainHeroImage"]/div[2]'
    price_xpath = '//*[@id="ViewItemPage"]/div[5]/div[1]/div[1]/div/div/span/span[1]'
    html_class_name = "clearfix"
    folder = "/Users/nicholas/Documents/Experimentation/chairDetector/scanner/data"
    model_path = "/Users/nicholas/Documents/Experimentation/chairDetector/detector/model.pt"
    db = "chairs.db"
    price = 500
    driver_loc = '/Users/nicholas/chromedriver'
    thresh = 0.7

    web_dict = {
        "ads_loc": html_class_name,
        "id_loc": id_xpath,
        "price_loc": price_xpath,
        "gallery_loc": gallery_xpath,
        "image_loc": {"loc": images_ind, "path": images_xpath},
        "images_loc": images_class_name}
    web_loc = browserconn.BrowserConnection(**web_dict)
    scraper = KijijiScraper(db, model_path, price, folder, driver_loc, thresh)
    scraper.scrape_ads(url, web_loc)
