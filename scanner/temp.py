from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.request import urlopen

#options = Options()
#options.headless = True
# add additional options to speed up automation
url = "https://www.kijiji.ca/v-chair-recliner/mississauga-peel-region/high-end-pre-owned-office-chair-in-excellent-condition-call-now/1547561429"
driver = webdriver.Chrome('/Users/nicholas/chromedriver')
driver.get(url)
xpath = '//*[@id="mainHeroImage"]'
driver.find_element_by_xpath(xpath).click()
for i in range(1, 4):
    img_xpath = '//*[@id="PageVIP"]/div[12]/div/div/div[2]/ul/li[{}]/div/img'.format(i)
    img = driver.find_element_by_xpath(img_xpath)
    img_name = (
        "/Users/nicholas/Documents/Experimentation"
        "/chairDetector/scanner/{}.png").format(i)
    src = img.get_attribute('src')
    conn = urlopen(src)
    with open(img_name, "wb") as download:
        download.write(conn.read())
