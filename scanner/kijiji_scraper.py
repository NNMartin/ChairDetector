from datetime import datetime
import classify
import chair_sqlite
from browserconn import BrowserConnection
import sqlite3


class KijijiAd:
    """
    Object that represents a Kijiji Ad.

    id - int: Unique integer identifier of the ad that distinguishes it from
            other Kijiji ads. This id is created by Kijiji.
    time - str: The date (Y/M/D and H/M/S) the ad was identified and added to a
            local database.
    probs - list[float]: Each ad has a gallery of images showcasing the product
            for sale. This attribute represents the probabilities of each image
            containing a particular item, which depends on the model used for
            classification.
    names - list[str]: List of the downloaded global paths of each image in the
            ad gallery.
    price - float: The price in CAD of an ad.
    var_names - str: String of variable names used in the database containing
            downloaded ads. This string is formatted to make insertion into the
            database convenient.
    """
    def __init__(self, id: int, time: str, probs: list[float], price: float,
                 names: list[str], *args, **kwargs):
        super(KijijiAd, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.id = id
        self.time = time
        self.probs = probs
        self.names = names
        self.price = price
        self.var_names = "(:id, :date, :prob, :price, :filename)"

    def has_hm(self, threshold=0.7):
        """
        Returns True if the ad contains an image whose probability of being a
        a particular item are greater than or equal to <threshold>.
        Returns False otherwise.

        :param threshold: Probability threshold to
                classify an image as a particular item.
        :return: bool
        """
        return max(self.probs) >= threshold

    def get_ith_value_dict(self, i: int):
        """
        Given an index <i>, returns a dictionary of ad attributes corresponding
        to the <i>th image.

        :param i: Index of image in image gallery of ad.
        :return: dict
        """
        return {
            "id": self.id,
            "date": self.time,
            "prob": self.probs[i],
            "price": self.price,
            "filename": self.names[i]
            }

    def insert_into_db(self, db_conn: tuple[sqlite3.Cursor, sqlite3.Connection]):
        """
        Inserts ad into the database associated to the (cursor, connection)
        object <db_conn>.

        :param db_conn: Database object
        :return: None
        """
        for i in range(len(self.names)):
            item_dict = self.get_ith_value_dict(i)
            chair_sqlite.insert(
                db_conn, item_dict=item_dict, item_names=self.var_names
                )


class KijijiScraper:
    """
    Uses BrowserConnection object to interact with Kijiji website and scrape
    ad data.

    db - (sqlite3.Cursor, sqlite3.Connection): Database cursor and connection
    max_price - float: The maximum price that will be considered when
            notifying a user about a potential ad.
    model - torch.Module: PyTorch Neural Net used for ad image classification.
    notifs - list[tuple(int, float)]: List of ads whose price is less than or
            equal to max_price. Each element contains ad id and ad price.
            Originally empty, this list is filled by calling scrape_ads.
    num_ads - int (>0): The maximum number of ads to scrape.
    folder - str: Global path of folder to store downloaded images.
    thresh - float (0 < threshold < 1): Probability threshold to
            classify an image as a particular item.
    """
    def __init__(self, db_name: str, model_path: str, max_price: float,
                 folder: str, thresh: float, num_ads: int):
        """
        :param db_name: Local path of database used to store scraped ad data.
        :param model_path: Global path of model used to classify ads.
        :param max_price: The maximum price that will be considered when
                notifying a user about a potential ad.
        :param folder: Global path of folder to store downloaded images.
        :param thresh: Probability threshold to
                classify an image as a particular item.
        :param num_ads: The maximum number of ads to scrape.
        """
        assert num_ads < 47, "Currently the number of ads is capped at 46."
        self.db = chair_sqlite.open_conn(db_name=db_name)
        self.max_price = max_price
        self.model = classify.init_model(model_path)
        self.notifs = []
        self.num_ads = num_ads
        self.folder = folder
        self.thresh = thresh

    @staticmethod
    def init_browser_conn(driver_loc: str, timeout: int):
        """
        Initializes BrowserConnection object with the webdriver location.

        :param driver_loc: Path to webdriver.
        :param timeout: Maximum allotted time for Selenium methods before
                raising TimeoutException.
        :return: BrowserConnection
        """
        return BrowserConnection(driver_loc, timeout)

    def new_id(self, ad_id: int):
        """
        Returns True if <ad_id> is not in the database under the variable
        "id", and False otherwise.

        :param ad_id: Unique numeric identifier of an ad.
        :return: bool
        """
        return not chair_sqlite.is_in_db(self.db, ad_id, "id")

    def insert_into_db(self, ad: KijijiAd):
        """
        Inserts <ad> into database.

        :param ad: Ad to be inserted into database.
        :return: None
        """
        ad.insert_into_db(self.db)

    def _close_db(self):
        """
        Closes the database connection.

        :return: None
        """
        chair_sqlite.close_conn(self.db)

    @staticmethod
    def _quit_browser(conn: BrowserConnection):
        """
        Quits the browser connection.

        :param conn: Web browser object that interacts with Kijiji
                website using Selenium.
        :return: None
        """
        conn.quit_conn()

    def scrape_images(self, conn: BrowserConnection, time: str):
        """
        Given a BrowserConnection <conn> located at an ad image gallery,
        download the images; including the <time> of download in their filename.
        Return the names of downloaded images and their classification
        probabilities.

        :param conn: Web browser object that interacts with Kijiji
                website using Selenium.
        :param time: The date (Y/M/D and H/M/S) the ad was identified and added
                to a local database.
        :return: tuple[list[str], list[float]]
        """
        images = conn.get_images()
        names, predictions = [], []
        for i, image in enumerate(images):
            name = "{}/{}_{}.png".format(self.folder, time, str(i))
            names.append(name)
            predictions.append(classify.hm_prob(image, name, self.model))
        return names, predictions

    def scrape_ad(self, conn: BrowserConnection):
        """
        Scrapes the data of a particular ad corresponding to the web browser
        <conn> and stores in a database, self.db.
        Ad data stored includes:
            - id
            - price
            - images of product
            - date and time of download
            - names of images downloaded
            - probabilities of images being a particular item
        Ads that contain an image whose probability is greater than or equal to
        self.thresh and price is less than or equal to self.max_price are
        appended to self.notifs. Afterwards, the web browser goes back to the
        previous page containing all ads.

        :param conn: Web browser object that interacts with Kijiji
                website using Selenium.
        :return: None
        """
        ad_dict = {"id": conn.get_id()}
        if ad_dict["id"] is None or not self.new_id(ad_dict["id"]):
            conn.go_back_n_pages()
            return None
        ad_dict["price"] = conn.get_price()
        if ad_dict["price"] is None:
            conn.go_back_n_pages()
            return None
        ad_dict["time"] = KijijiScraper.current_time()
        names, probs = self.scrape_images(conn, ad_dict["time"])
        if len(names) > 0:
            ad_dict["names"], ad_dict["probs"] = names, probs
            ad = KijijiAd(**ad_dict)
            if ad.has_hm(self.thresh) and ad.price <= self.max_price:
                self.notifs.append((ad.id, ad.price))
            self.insert_into_db(ad)
        conn.go_back_n_pages()

    def scrape_ads(self, url: str, browser_dict: dict):
        """
        Given a <url> link and a dictionary of paramaters, <browser_dict>,
        needed to initialize a BrowserConnection, return a list of ads whose
        prices are below or equal to self.max_price and have a probability
        greater than or equal to self.thresh of containing a particular item.

        :param url: Url link to a Kijiji website page of ads to scrape.
        :param browser_dict: Dictionary of keys and values needed to initialize
                a BrowserConnection.
        :return: List[tuple[int, float]]
        """
        conn = KijijiScraper.init_browser_conn(**browser_dict)
        conn.get_url(url)
        for i in range(1, self.num_ads):
            if conn.click_ad(conn.get_ith_ad(self.num_ads, i)):
                self.scrape_ad(conn)
            else:
                break
        KijijiScraper._quit_browser(conn)
        self._close_db()
        return self.notifs

    @staticmethod
    def current_time():
        """
        Returns current date and time.

        :return: str
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
