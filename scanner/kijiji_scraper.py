from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.request import urlopen
from datetime import datetime
import classify # might need to add parent directory
from PIL import Image

# make into dictionary
start_url = "https://www.kijiji.ca/b-chair-recliner/city-of-toronto/c245l1700273?ad=offering" # Main starting point
id_xpath = '//*[@id="ViewItemPage"]/div[3]/div/ul/li[7]'
ad_xpath = '//*[@id="mainPageContent"]/div[3]/div[3]/div[3]/div[4]/div'
images_xpath = '//*[@id="mainHeroImage"]'
price_xpath = '//*[@id="ViewItemPage"]/div[5]/div[1]/div[1]/div/div/span/span[1]'
html_class_name = "clearfix"
num_ads = 50

class KijijiAd:
    def __init__(self, names, probs, id, time, price):
        self.names = names # downloaded image names
        self.probs = probs
        self.id = id
        self.time = time # date and time of download
        self.price = price

    def has_hm(self, threshold = 0.7):
        return max(self.probs) >= threshold

def is_ad(html_element):
    html_classes = html_element.get_attribute("class")
    return len(html_classes) == 1

def get_all_ads(driver):
    potential_ads = driver.find_element_by_class_name(html_class_name)
    return (ad for ad in potential_ads if is_ad(ad))

def scrape_kijiji(url, max_price, folder, model_link):
    model = classify.init_model(model_link)
    driver = webdriver.Chrome('/Users/nicholas/chromedriver')
    driver.get(url)
    for html_ad in get_all_ads(driver):
        scrape_ad(driver, html_ad, folder, model)
    #for i in range(num_ads):
        # find ad by class = ""?, then iterate through list
        #xpath = '//*[@id="mainPageContent"]/div[3]/div[3]/div[3]/div[{}]/div'.format(i+4)
    #    potential_ad = driver.find_element_by_xpath(xpath)
    #    if is_ad(potential_ad):
    #


def current_time():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def scrape_ad(driver, html_ad, folder, model):
    ad = {}
    id = driver.find_element_by_xpath(id_xpath).getText()
    # check if id is in the database
    price = driver.find_element_by_xpath(price_xpath).get_attribute("content")
    driver.find_element_by_xpath(images_xpath).click()
    now = current_time()
    ad["id"] = id
    ad["time"] = now
    ad["price"] = price
    ad["probs"] = []
    ad["names"] = []
    i = 1
    while True:
        img_xpath = ('//*[@id="PageVIP"]/div[12]/div/div/div[2]/ul/li[{}]/div/i'
            'mg').format(i)
        try:
            img = driver.find_element_by_xpath(img_xpath)
        except:
            break
        img_name = "{}/{}_{}.png".format(folder, now, str(i))
        prob = hm_prob(img, img_name, model)
        ad["names"].append(img_name)
        ad["probs"].append(prob)
        i += 1

def hm_prob(image, image_name, model):
    src = image.get_attribute('src')
    conn = urlopen(src)
    with open(image_name, "wb") as download:
        download.write(conn.read())
    input = Image.open(image_name)
    prob = classify.get_prob(model, input)
    return prob

def get_label():
    pass
