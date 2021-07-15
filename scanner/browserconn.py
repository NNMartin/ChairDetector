from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import time


class BrowserConnection:
    """
    Object that interacts with web browser using Selenium.
    """
    def __init__(self, driver_loc, timeout, headless=False):
        """
        Initializes BrowserConnection object.

        driver_loc: str. Path to webdriver.
        timeout: int. Maximum allotted time for Selenium methods before raising
            TimeoutException
        wait: int. Amount of time BrowserConnection waits between attempting to find elements.
        headless: bool. Whether the browser should be headless or not.
        """
        if headless:
            options = Options()
            options.headless = True
        else:
            options = None
        self.driver = webdriver.Chrome(driver_loc, options=options)
        self.ignored_exceptions = (StaleElementReferenceException,)
        self.timeout = timeout
        self.wait = 1
        self.by = {
            "xpath": By.XPATH,
            "class_name": By.CLASS_NAME,
            "link text": By.LINK_TEXT,
            }
        self.ads_loc = "clearfix"  # class name
        self.id_loc = '//*[@id="ViewItemPage"]/div[3]/div/ul/li[7]/a'
        self.price_loc = '//*[@id="ViewItemPage"]/div[5]/div[1]/div[1]/div/div/span/span[1]'
        self.gallery_loc = '//*[@id="mainHeroImage"]/div[2]'
        self.images_loc = "image-376491912"  # class name

    def go_back_n_pages(self, n=1):
        """
        Webdriver goes back <n> pages.

        n: int
        returns: None
        """
        assert isinstance(n, int) and n > 0, "n must be a positive integer"
        self.driver.execute_script("window.history.go(-{})".format(n))

    def get_current_url(self):
        return self.driver.current_url

    def get_url(self, url):
        """
        Selenium webdriver retrieves the <url> and implicitly waits for the
        page to load.

        url: str
        returns: None
        """
        self.driver.get(url)
        self.driver.implicitly_wait(self.timeout)

    def quit_conn(self):
        """
        Quits the browser connection

        returns: None
        """
        self.driver.delete_all_cookies()
        self.driver.quit()

    def get_ads(self, num_ads, ind):
        """
        Waits for the webdriver to find at least <num_ads> ads and then
        returns the ad located at the index <ind>.

        num_ads: int
        returns: Selenium.webdriver.WebElement
        """
        total = 0
        ads = self.driver.find_elements_by_class_name(self.ads_loc)
        while len(ads) < num_ads:
            time.sleep(self.wait)
            total += self.wait
            if total > self.timeout:
                raise TimeoutException
            ads = self.driver.find_elements_by_class_name(self.ads_loc)
        return ads[ind]

    def get_price(self):
        """
        Returns the ad price found in the location, self.price_loc, by an xpath
        search if the price exists. If the price cannot be located, returns
        None.

        returns: None or float
        """
        try:
            price_element = self.wait_for_page(self.price_loc, "xpath")
        except TimeoutException:
            return None
        web_price = price_element.get_attribute("content")
        return None if web_price is None else float(web_price.replace("$", ""))

    def wait_until_clickable(self, by, loc):
        cond = ec.element_to_be_clickable((self.by[by], loc))
        return WebDriverWait(
            self.driver,
            self.timeout,
            ignored_exceptions=self.ignored_exceptions
            ).until(cond)

    def click_ad(self, ad_element):
        total = 0
        try:
            while not ad_element.is_enabled():
                time.sleep(self.wait)
                total += self.wait
                if total > self.timeout:
                    raise TimeoutException
            ad_element.click()
            return True
        except StaleElementReferenceException:
            return False

    def click_gallery(self):
        gallery = self.wait_for_page(self.gallery_loc, "xpath")
        gallery.click()

    def wait_for_page(self, loc, by, singular=True):
        """
        Returns the selenium.webdriver.WebElement found at the location <loc>
        using the key <by> associated to one of the methods found in
        selenium.webdriver.common.by. When searching for the WebElement, waits
        for the element to not be stale.

        by: str
        loc: str
        returns: Selenium.webdriver.WebElement
        """
        if singular:
            locator = ec.presence_of_element_located
        else:
            locator = ec.presence_of_all_elements_located
        element = WebDriverWait(
            self.driver,
            self.timeout,
            ignored_exceptions=self.ignored_exceptions
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
            return self.wait_for_page(
                self.images_loc, "class_name", singular=False
            )
        except (ElementNotInteractableException, TimeoutException):
            return None
