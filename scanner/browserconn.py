from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import time


class BrowserConnection:
    def __init__(self, driver_loc, timeout, wait, headless=False):
        if headless:
            options = Options()
            options.headless = True
        # self.driver = webdriver.Chrome(driver_loc, options = options)
        self.driver = webdriver.Chrome(driver_loc)
        self.ignored_exceptions = (StaleElementReferenceException,)
        self.timeout = timeout
        self.wait = wait
        self.by = {
            "xpath": By.XPATH,
            "class_name": By.CLASS_NAME,
            "link text": By.LINK_TEXT
            }
        self.ads_loc = "clearfix"  # class name
        self.id_loc = '//*[@id="ViewItemPage"]/div[3]/div/ul/li[7]/a'
        self.price_loc = '//*[@id="ViewItemPage"]/div[5]/div[1]/div[1]/div/div/span/span[1]'
        self.gallery_loc = '//*[@id="mainHeroImage"]/div[2]'
        self.images_loc = "image-376491912"  # class name

    def go_back_n_pages(self, n=1):
        self.driver.execute_script("window.history.go(-{})".format(n))
        self.driver.implicitly_wait(self.timeout)

    def get_url(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(self.timeout)

    def quit_conn(self):
        self.driver.quit()

    def get_ads(self, num_ads, ind):
        total = 0
        ads = self.driver.find_elements_by_class_name(self.ads_loc)
        while len(ads) < num_ads:
            time.sleep(self.wait)
            total += self.wait
            if total > self.timeout:
                raise TimeoutException
            ads = self.driver.find_elements_by_class_name(self.ads_loc)
        return ads[ind]
        # ads = self.wait_for_page(self.ads_loc, "class_name", singular=False)
        # return len(ads), ads[ind]

    def get_price(self):
        try:
            price_element = self.wait_for_page(self.price_loc, "xpath")
        except TimeoutException:
            return None
        web_price = price_element.get_attribute("content")
        return None if web_price is None else float(web_price.replace("$", ""))

    def wait_until_clickable(self, by, loc):
        cond = ec.element_to_be_clickable((self.by[by], loc))
        return WebDriverWait(
            self.driver, self.timeout, ignored_exceptions=self.ignored_exceptions
            ).until(cond)

    def click_ad(self, ad_element):
        total = 0
        while not ad_element.is_enabled():
            time.sleep(self.wait)
            total += self.wait
            if total > self.timeout:
                raise TimeoutException
        ad_element.click()
        # ad_title = ad_element.find_element_by_class_name("title")
        # ad_link = ad_title.find_element_by_tag_name("a").get_attribute("href")
        # self.wait_for_page(ad_link, "link text")  # wait until page loads
        # clickable_ad = self.wait_until_clickable("link text", ad_link)
        # clickable_ad.click()

    def click_gallery(self):
        gallery = self.wait_for_page(self.gallery_loc, "xpath")
        gallery.click()

    def wait_for_page(self, loc, by, singular=True):
        if singular:
            locator = ec.presence_of_element_located
        else:
            locator = ec.presence_of_all_elements_located
        element = WebDriverWait(
            self.driver, self.timeout, ignored_exceptions=self.ignored_exceptions
        ).until(locator((self.by[by], loc)))
        return element

    def get_id(self):
        try:
            ad_id = self.wait_for_page(self.id_loc, "xpath")
            return int(ad_id.get_attribute("innerHTML"))
        except TimeoutException:
            return None

    def get_images(self):
        try:
            self.click_gallery()
        except (ElementNotInteractableException, TimeoutException):
            return None
        try:
            images = self.wait_for_page(
                self.images_loc, "class_name", singular=False
                )
        except TimeoutException:
            return None
        for image in images:
            yield image
