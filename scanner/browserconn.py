from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import numpy as np


class BrowserConnection:
    def __init__(self, driver_loc, timeout, headless=False):
        if headless:
            options = Options()
            options.headless = True
        # self.driver = webdriver.Chrome(driver_loc, options = options)
        self.driver = webdriver.Chrome(driver_loc)
        self.ignored_exceptions = (StaleElementReferenceException,)
        self.timeout = timeout
        self.by = {
            "xpath": By.XPATH,
            "class_name": By.CLASS_NAME,
            "link text": By.LINK_TEXT
            }

    def go_back_n_pages(self, n=1):
        self.driver.execute_script("window.history.go(-{})".format(n))

    def quit_conn(self):
        self.driver.quit()

    def get_ads(self, ind):
        assert ind > 0, "index given must be greater than 0"
        ads = self.wait_for_page(
            self.driver, self.ads_loc, "class_name", singular=False
            )
        return len(ads), ads[ind]

    def get_price(self):
        try:
            price_element = self.wait_for_page(self.driver, self.price_loc, "xpath")
        except TimeoutException as e:
            return None
        web_price = price_element.get_attribute("content")
        return np.inf if web_price is None else float(web_price.replace("$", ""))

    def click_element(self, by, loc):
        cond = ec.element_to_be_clickable((self.by[by], loc))
        return WebDriverWait(self.driver, self.timeout).until(cond)

    def wait_for_page(self, loc, by, singular = True):
        if singular:
            locator = ec.presence_of_element_located
        else:
            locator = ec.presence_of_all_elements_located
        try:
            element = WebDriverWait(
                self.driver, self.timeout, ignored_exceptions=self.ignored_exceptions
                ).until(locator((self.by[by], loc)))
            return element
        except TimeoutException:
            print("The damn thing timed out again")

    def get_id(self):
        try:
            id = self.wait_for_page(self.driver, self.id_loc, "xpath")
            return int(id.get_attribute("innerHTML"))
        except TimeoutException:
            return None

    def get_images(self):
        try:
            gallery = self.wait_for_page(self.driver, self.gallery_loc, "xpath")
            gallery = self.click_element(self.driver, self.gallery_loc, "xpath")
            gallery.click()
        except ElementNotInteractableException as e:
            raise e
        images = self.wait_for_page(
            self.driver, self.images_loc, "class_name", singular=False
            )
        for image in images:
            yield image
