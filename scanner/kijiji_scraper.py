from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from datetime import datetime
import classify
import numpy as np
import chair_sqlite

class KijijiAd(dict):
    def __init__(self, *args, **kwargs):
        super(KijijiAd, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.var_names = "(:id, :date, :prob, :price, :filename)"

    def has_hm(self, threshold = 0.7):
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

    def __str__(self):
        pass

class KijijiScraper:
    def __init__(self, db, model_path, price, folder, driver_loc, thresh,
        headless = False):
        if headless:
            options = Options()
            options.headless = True
        #self.driver = webdriver.Chrome(driver_loc, options = options)
        self.driver = webdriver.Chrome(driver_loc)
        self.db = chair_sqlite.open_conn(db_name = db) # tuple
        self.max_price = price
        self.model_path = model_path
        self.notifs = []
        self.folder = folder
        self.thresh = thresh

    def _init_model(self):
        return classify.init_model(self.model_path)

    def new_id(self, id):
        """ check if id is in the database"""
        return chair_sqlite.is_in_db(self.db, id, "id")

    def insert_into_db(self, ad):
        """ inserts ad into database
        """
        ad.insert_into_db(self.db)

    def scrape_images(self, web_loc, time, model):
        names = []
        probs = []
        try:
            for i, image in enumerate(web_loc.get_images(self.driver)):
                if image is None:
                    continue
                name = "{}/{}_{}.png".format(self.folder, time, str(i))
                names.append(name)
                probs.append(classify.hm_prob(image, name, model))
            return names, probs
        except ElementNotInteractableException:
            return None

    def go_back_n_pages(self, n=1):
        self.driver.execute_script("window.history.go(-{})".format(n))

    def scrape_ad(self, web_ad, web_loc, model):
        ad_title = web_ad.find_element_by_class_name("title")
        ad_link = ad_title.find_element_by_tag_name("a").get_attribute("href")
        web_loc.click_element(ad_title, "xpath", '../../..').click()
        #web_ad.click()
        id = web_loc.get_id(self.driver)
        if id is None or not self.new_id(id):
            self.go_back_n_pages()
            return None
        now = current_time()
        price = web_loc.get_price(self.driver)
        scraped_data = self.scrape_images(web_loc, now, model)
        if scraped_data is not None:
            names, probs = scraped_data
            ad = KijijiAd(
                **{"time": now, "price": price, "id": id, "names": names,
                "probs": probs}
                )
            if ad.has_hm(self.thresh) and ad.price <= self.max_price:
                self.notifs.append((id, price))
            ad.insert_into_db(self.db)
        self.go_back_n_pages()

    def scrape_ads(self, url, web_loc):
        model = self._init_model()
        self.driver.get(url)
        num_ads, _ = web_loc.get_ads(self.driver, 1)
        for i in range(1, num_ads):
            _, web_ad = web_loc.get_ads(self.driver, i)
            self.scrape_ad(web_ad, web_loc, model)
        self.driver.quit()
        self.db[1].close()
        return self.notifs

class WebPageIdentifiers(dict):
    def __init__(self, *args, **kwargs):
        super(WebPageIdentifiers, self).__init__(self, *args, **kwargs)
        self.__dict__ = self
        self.ignored_exceptions = (StaleElementReferenceException,)
        self.timeout = 30
        self.by = {
            "xpath": By.XPATH,
            "class_name": By.CLASS_NAME,
            "link text": By.LINK_TEXT
            }

    def get_ads(self, driver, ind):
        assert ind > 0, "The first element is not an ad"
        ads = self.wait_for_page(
            driver, self.ads_loc, "class_name", singular = False
            )
        return len(ads), ads[ind]

    def get_price(self, driver):
        try:
            price_element = self.wait_for_page(driver, self.price_loc, "xpath")
        except TimeoutException as e:
            return None
        web_price = price_element.get_attribute("content")
        return np.inf if web_price is None else float(web_price.replace("$", ""))

    def click_element(self, driver, by, loc):
        cond = ec.element_to_be_clickable((self.by[by], loc))
        return WebDriverWait(driver, self.timeout).until(cond)

    def wait_for_page(self, driver, loc, by, singular = True):
        if singular:
            locator = ec.presence_of_element_located
        else:
            locator = ec.presence_of_all_elements_located
        return WebDriverWait(
            driver, self.timeout, ignored_exceptions = self.ignored_exceptions
            ).until(locator((self.by[by], loc)))

    def get_id(self, driver):
        try:
            id = self.wait_for_page(driver, self.id_loc, "xpath")
            return int(id.get_attribute("innerHTML"))
        except TimeoutException:
            return None

    def get_images(self, driver):
        try:
            gallery = self.wait_for_page(driver, self.gallery_loc, "xpath")
            gallery.click()
        except ElementNotInteractableException as e:
            raise e
        images = self.wait_for_page(
            driver, self.images_loc, "class_name", singular = False
            )
        for image in images:
            yield image

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
    web_loc = WebPageIdentifiers(**web_dict)
    scraper = KijijiScraper(db, model_path, price, folder, driver_loc, thresh)
    scraper.scrape_ads(url, web_loc)
