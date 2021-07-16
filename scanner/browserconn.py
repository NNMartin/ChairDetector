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
    def __init__(self, driver_loc, timeout, headless=True):
        """
        Initializes BrowserConnection object.

        driver_loc - str: Path to webdriver.
        timeout - int: Maximum allotted time for Selenium methods before
            raising TimeoutException
        wait - int: Amount of time BrowserConnection waits between attempting
            to find elements.
        headless - bool: Whether the browser should be headless or not.
        driver - selenium.webdriver.WebDriver: The browser used to interact
            with Kijiji
        ignored_exceptions - tuple of Exceptions: Exceptions that are to be
            ignored when searching for a WebElement.
        by - dict: Dictionary of keys (str) that represent Selenium locator
            methods, and corresponding values (selenium.webdriver.common.by)
            that are the methods of location.
        ads_loc - str: pattern used by find_element_by_class_name to search
            for the WebElements containing the ads on the main results page to
            click on.
        id_loc - str: pattern used by find_element_by_xpath to search for a
            WebElement containing the ad id.
        price_loc - str: pattern used by find_element_by_xpath to search for a
            WebElement containing the ad price.
        gallery_loc: pattern used by find_element_by_xpath to search for a
            WebElement containing the ad gallery.
        gallery_loc: pattern used by find_element_by_css_selector to search for
            the WebElements containing the ad images.
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
            "class name": By.CLASS_NAME,
            "link text": By.LINK_TEXT,
            "css selector": By.CSS_SELECTOR
            }
        self.ads_loc = "clearfix"  # class name
        self.id_loc = '//*[@id="ViewItemPage"]/div[3]/div/ul/li[7]/a'
        self.price_loc = ('//*[@id="ViewItemPage"]/div[5]/div[1]/div[1]/div/'
                          'div/span/span[1]'
                          )
        self.gallery_loc = '//*[@id="mainHeroImage"]/div[2]'
        self.images_loc = '[alt="carousel thumbnail"]'  # css selector

    def go_back_n_pages(self, n=1):
        """
        Webdriver goes back <n> pages.

        n - int: The number of pages the browser goes back in history.
        returns None
        """
        assert isinstance(n, int) and n > 0, "n must be a positive integer"
        self.driver.execute_script("window.history.go(-{})".format(n))

    def get_current_url(self):
        """
        Returns the current url of the browser.

        returns str
        """
        return self.driver.current_url

    def get_url(self, url):
        """
        Selenium webdriver retrieves the <url> and implicitly waits for the
        page to load.

        url - str: website url for the browser to retrieve.
        returns None
        """
        self.driver.get(url)
        self.driver.implicitly_wait(self.timeout)

    def quit_conn(self):
        """
        Quits the browser connection and deletes all cookies.

        returns None
        """
        self.driver.delete_all_cookies()
        self.driver.quit()

    def get_ith_ad(self, num_ads, ind):
        """
        Waits for the webdriver to find at least <num_ads> ads and then
        returns the ad located at the index <ind>. At the time of writing
        this code Selenium doesn't offer a way to search for the ith
        occurrence of a locator and so an entire list of all elements matching
        the locator must be found on each call.

        num_ads - int (>0): Number of ads to scrape.
        ind - int (>0): Index of a particular ad to scrape.
        returns Selenium.webdriver.WebElement
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
        search if the price exists. If the price cannot be located or is not a
        number, returns None.

        returns None or float
        """
        try:
            price_element = self.wait_for_page(self.price_loc, "xpath")
        except TimeoutException:
            return None
        web_price = price_element.get_attribute("content")
        return None if web_price is None else float(web_price.replace("$", ""))

    def click_ad(self, ad_element):
        """
        Waits for browser until <ad_element> is enabled and then clicks on the
        element. Returns True if the <ad_element> is not a stale web element
        and False otherwise.

        ad_element - Selenium.webdriver.WebElement: Element to be clicked.
        returns - bool
        """
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
        """
        Clicks on the gallery of photos of a Kijiji ad webpage that the
        webdriver is on. The images in the gallery can then be scraped using
        additional functions.

        returns None
        """
        gallery = self.wait_for_page(self.gallery_loc, "xpath")
        gallery.click()

    def wait_for_page(self, loc, by, singular=True):
        """
        Returns the selenium.webdriver.WebElement found at the location <loc>
        using the key <by> associated to one of the methods found in
        selenium.webdriver.common.by. When searching for the WebElement, the
        function ignores exceptions found in <self.ignored_exceptions>.

        by - str: Must be one of the keys found in self.by. Denotes the
            Selenium method of location.
        loc - str: The pattern used by the locator to locate the WebElement of
            interest.
        returns Selenium.webdriver.WebElement
        """
        if singular:
            locator = ec.presence_of_element_located
        else:
            locator = ec.presence_of_all_elements_located
        return WebDriverWait(
            self.driver,
            self.timeout,
            ignored_exceptions=self.ignored_exceptions
            ).until(locator((self.by[by], loc)))

    def get_id(self):
        """
        Returns the ad id found by the pattern, self.id_loc, by an xpath
        search. If the id cannot be found in a duration of time less than
        self.timeout then returns None

        returns None or int
        """
        try:
            ad_id = self.wait_for_page(self.id_loc, "xpath")
            return int(ad_id.get_attribute("innerHTML"))
        except TimeoutException:
            return None

    def get_images(self):
        """
        Returns a generator of WebElements representing an ad's images. If
        an Exception is raised, the generator returned is empty.

        returns generator of WebElements
        """
        try:
            self.click_gallery()
            images = self.wait_for_page(
                self.images_loc, "css selector", singular=False
            )
            for image in images:
                yield image
        except (ElementNotInteractableException, TimeoutException):
            return None
