from datetime import datetime
import classify
import chair_sqlite
import browserconn


class KijijiAd(dict):
    def __init__(self, id, time, probs, price, names, *args, **kwargs):
        super(KijijiAd, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.id = id
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
            chair_sqlite.insert(db_conn, item_dict=item_dict, item_names=self.var_names)


class KijijiScraper:
    """
    Uses BrowserConnection object to interact with Kijiji website and scrape
    data.
    """
    def __init__(self, db, model_path, max_price, folder, thresh, num_ads):
        assert num_ads < 47, "Currently the number of ads is capped at 46."
        self.db = chair_sqlite.open_conn(db_name=db)  # tuple
        self.max_price = max_price
        self.model_path = model_path
        self.notifs = []
        self.num_ads = num_ads
        self.folder = folder
        self.thresh = thresh

    def _init_model(self):
        return classify.init_model(self.model_path)

    def init_browser_conn(self, driver_loc, timeout, wait):
        return browserconn.BrowserConnection(driver_loc, timeout, wait)

    def new_id(self, ad_id):
        """ check if ad_id is in the database"""
        return not chair_sqlite.is_in_db(self.db, ad_id, "id")

    def insert_into_db(self, ad):
        """ inserts ad into database
        """
        ad.insert_into_db(self.db)

    def _close_db(self):
        chair_sqlite.close_db(self.db)

    def _quit_browser(self, conn):
        conn.quit_conn()

    def scrape_images(self, conn, time, model):
        images = conn.get_images()
        if images is None:
            return None
        else:
            names, predictions = [], []
            for i, image in enumerate(images):
                name = "{}/{}_{}.png".format(self.folder, time, str(i))
                names.append(name)
                predictions.append(classify.hm_prob(image, name, model))
            return names, predictions

    def scrape_ad(self, conn, model):
        ad_dict = {"id": conn.get_id()}
        if ad_dict["id"] is None or not self.new_id(ad_dict["id"]):
            conn.go_back_n_pages()
            return None
        ad_dict["price"] = conn.get_price()
        if ad_dict["price"] is None:
            conn.go_back_n_pages()
            return None
        ad_dict["time"] = current_time()
        scraped_data = self.scrape_images(conn, ad_dict["time"], model)
        if scraped_data is not None:
            ad_dict["names"], ad_dict["probs"] = scraped_data
            ad = KijijiAd(**ad_dict)
            if ad.has_hm(self.thresh) and ad.price <= self.max_price:
                self.notifs.append((ad.id, ad.price))
            self.insert_into_db(ad)
        conn.go_back_n_pages()

    def scrape_ads(self, url, browser_dict):
        model = self._init_model()
        conn = self.init_browser_conn(**browser_dict)
        conn.get_url(url)
        for i in range(1, self.num_ads):
            if conn.click_ad(conn.get_ads(self.num_ads, i)):
                self.scrape_ad(conn, model)
            else:
                break
        self._quit_browser(conn)
        self._close_db()
        return self.notifs


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    url = "https://www.kijiji.ca/b-chair-recliner/city-of-toronto/c245l1700273?ad=offering"  # Main starting point
    id_xpath = '//*[@id="ViewItemPage"]/div[3]/div/ul/li[7]/a'
    images_class_name = "image-376491912"
    gallery_xpath = '//*[@id="mainHeroImage"]/div[2]'
    price_xpath = '//*[@id="ViewItemPage"]/div[5]/div[1]/div[1]/div/div/span/span[1]'
    html_class_name = "clearfix"
    folder = "/Users/nicholas/Documents/Experimentation/chairDetector/scanner/data"
    model_path = "/Users/nicholas/Documents/Experimentation/chairDetector/detector/model.pt"
    db = "chairs.db"
    num_ads = 10  # less than 47
    price = 500
    driver_loc = '/Users/nicholas/chromedriver'
    thresh = 0.7
    timeout = 30
    wait = 1

    # browser_dict = {
    #     "ads_loc": html_class_name,
    #     "id_loc": id_xpath,
    #     "price_loc": price_xpath,
    #     "gallery_loc": gallery_xpath,
    #     "images_loc": images_class_name}
    # = browserconn.BrowserConnection(**web_dict)
    browser_dict = {"driver_loc": driver_loc, "timeout": timeout, "wait": wait}
    scraper = KijijiScraper(db, model_path, price, folder, thresh, num_ads)
    scraper.scrape_ads(url, browser_dict)