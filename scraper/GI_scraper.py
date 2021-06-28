from selenium import webdriver
import re
from urllib.request import urlopen
from time import sleep

def scroll_to_bottom(driver):
    scroll_down(driver)
    more_imgs_xpath = '//*[@id="islmp"]/div/div/div/div/div[3]/div[2]/input'
    driver.find_element_by_xpath(more_imgs_xpath).click()
    scroll_down(driver)

def scroll_down(driver):
    # get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    wait = 3
    while True:
        # scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(wait)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def create_img_name(driver, index, start_index):
    title_xpath = '//*[@id="islrg"]/div[1]/div[{}]/a[2]'.format(str(index))
    label_index = str(index+start_index)
    title = driver.find_element_by_xpath(
        title_xpath
        ).get_attribute("title")
    if bool(re.search(r'(?i)herman miller', title)):
        return "HM" + label_index
    else:
        return "NHM" + label_index

def download_img(driver, index, folder, filename):
    img_xpath = (
        '//*[@id="islrg"]/div[1]/'
        'div[{}]/a[1]/div[1]/img').format(str(index))
    img = driver.find_element_by_xpath(img_xpath)
    img_name = (
        "/Users/nicholas/Documents/Experimentation"
        "/chairDetector/new_data/{}/{}.png").format(folder, filename)
    src = img.get_attribute('src')
    conn = urlopen(src)
    with open(img_name, "wb") as download:
        download.write(conn.read())

def scrape_url(url, driver, n, folder, start_index = 0):
    """
    For loop must start at 1 for Google Images indexing.
    """
    driver.get(url)
    scroll_to_bottom(driver)
    total = 0
    for i in range(1, n+1):
        try:
            filename = create_img_name(driver, i, start_index)
            download_img(driver, i, folder, filename)
            total += 1
        except:
            pass
    return total

def scrape_data(n, url_folder_dict):
    driver = webdriver.Chrome('~/chromedriver')
    start_index = 0
    for url, folder in url_folder_dict.items():
        start_index += scrape_url(url, driver, n, folder, start_index)
    driver.close()

def rename_files(folder, suffix = 'x'):
    import os
    for filename in os.listdir(folder):
        curr_path = os.path.join(folder, filename)
        with open(curr_path):
            new_path = curr_path[:-4] + suffix + '.png'
            os.rename(curr_path, new_path)

if __name__ == '__main__':
    used_office_chair = (
        "https://www.google.ca/search?q=used+office+chair+-ergonomic+-herman+-"
        "miller&hl=en&tbm=isch&source=hp&biw=1438&bih=798&ei=rOrEYKDQNIW8tAa0mI"
        "DADg&oq=used+office+chair+-ergonomic+-herman+-miller&gs_lcp=CgNpbWcQAz"
        "oFCAAQsQM6AggAOgQIABAeOgYIABAIEB46BAgAEBhQlQpYgHlg56sBaAFwAHgBgAGHAogB"
        "6hqSAQY0Mi4yLjGYAQCgAQGqAQtnd3Mtd2l6LWltZw&sclient=img&ved=0ahUKEwig1v"
        "Cuy5LxAhUFHs0KHTQMAOgQ4dUDCAc&uact=5"
        )
    ergo = (
        "https://www.google.ca/search?q=ergonomic+office+chair+-used+-herman+-"
        "miller&tbm=isch&ved=2ahUKEwjXzsq5y5LxAhVNs6wKHeMJBaUQ2-cCegQIABAA&oq=e"
        "rgonomic+office+chair+-used+-herman+-miller&gs_lcp=CgNpbWcQA1CjvQhYzvg"
        "IYMqCCWgAcAB4AIABiAKIAdAKkgEFOC40LjGYAQCgAQGqAQtnd3Mtd2l6LWltZ8ABAQ&sc"
        "lient=img&ei=w-rEYJfhEs3msgXjk5SoCg&bih=798&biw=1438&hl=en"
        )
    hm = (
        "https://www.google.ca/search?q=Herman+Miller+office+chair+-Used&tbm=i"
        "sch&ved=2ahUKEwjSiunazJLxAhUPYK0KHc-fAPsQ2-cCegQIABAA&oq=Herman+Miller"
        "+office+chair+-Used&gs_lcp=CgNpbWcQAzoECAAQQzoCCAA6BAgAEB5Q5eoCWMaIA2D"
        "vjANoAHAAeACAAVaIAdsDkgEBN5gBAKABAaoBC2d3cy13aXotaW1nwAEB&sclient=img&"
        "ei=FezEYJKsG4_AtQXPv4LYDw&bih=798&biw=1438&hl=en"
        )
    hm_used = (
        "https://www.google.ca/search?q=Used+Herman+Miller&tbm=isch&ved=2ahUKEw"
        "iN8ffhzZLxAhUCL60KHRoDDb0Q2-cCegQIABAA&oq=Used+Herman+Miller&gs_lcp=Cg"
        "NpbWcQAzIECAAQQzICCAAyAggAMgQIABBDMgQIABBDMgIIADIGCAAQCBAeMgYIABAIEB4y"
        "BggAEAgQHjIGCAAQCBAeUIDkAVj85QFg6ucBaABwAHgAgAGsAogBhgSSAQUyLTEuMZgBAK"
        "ABAaoBC2d3cy13aXotaW1nwAEB&sclient=img&ei=MO3EYI2ZMYLetAWahrToCw&bih=7"
        "98&biw=1438&hl=en"
        )
    label_sample_size = 500
    url_folder_dict = {
        used_office_chair: "used_office_chair",
        hm: "hm",
        hm_used: "hm_used",
        ergo: "ergo"
        }
