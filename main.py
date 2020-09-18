from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from user_agent import generate_user_agent
from bs4 import BeautifulSoup
from pathlib import Path
import requests
import time
import json
import os

def get_soup(driver, tags, saler_url=""):
    if saler_url:
        driver.get(saler_url)
        time.sleep(3)

    return BeautifulSoup(driver.page_source).select(tags)

def get_directory(directory, *args):
    """
    取得目錄路徑，順便檢查是否存在，若不存在就建立目錄
    """
    directory = Path(directory).joinpath(*args)
    if not directory.exists():
        Path.mkdir(directory, parents=True)
    return directory

def outpu_json(file, data):
    filename = file if ".json" in file else f"{file}.json"

    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file)

def load_json(file):
    with open(file, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data

def get_classification(driver, saler_url):
    classification_soup = get_soup(driver, "div.sidebar-main.category-listing a", saler_url)[1:] # 排除第一個分類-全部商品
    classification_name_ls = [c.text.replace("\n", "").strip() for c in classification_soup]
    classification_link_ls = []

    for i, btn in enumerate(driver.find_elements_by_class_name("category-listing-item")[1:]):
        btn.click()
        time.sleep(2)
        driver.execute_script("window.scroll(0, 0);") # 拉到頂部，因為btn似乎是記錄點擊位置，點擊進入下個頁面時位置不一定是在頂部

        get_directory(DOWNLOAD_DIRECTORY, classification_name_ls[i]) # 建立資料夾
        classification_link_ls.append(driver.current_url) # 之後輸出記錄使用
        
    dc = dict(zip(classification_name_ls, classification_link_ls))

    outpu_json("classification.json", dc)

def get_product(driver):
    classification_dc = load_json("classification.json")

    product_dc = {} # 記錄資料使用

    for key, url in classification_dc.items():
        driver.get(url)
        time.sleep(3)
        soup = get_soup(driver, "div.item-info > h3.item-name.defaultStyle-name > span > a") # 取得所有商品資料

        dc = {}
        for i, ele in enumerate(soup):
            dc[i] = {
                "title": ele.text,
                "link": ele["href"]
            }

            get_directory(DOWNLOAD_DIRECTORY, key, ele.text) # 建立資料夾

        product_dc[key] = dc

    outpu_json("product.json", product_dc)

def go_to_down(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(0.5)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def download_img(path, img_url, s):
    headers = {
        "user-agent": generate_user_agent()
    }

    file_name = img_url.split("/")[-1] 

    if not (".jpg" in file_name.lower() or ".png" in file_name.lower()): # 以防爬到不是圖片的網址
        return

    ir = s.get(img_url, headers=headers)
    time.sleep(0.5)

    if ir.status_code == 200:
        open(f'{path}\\{file_name}', 'wb').write(ir.content)
        print(f"download '{path}\\{file_name}'")

def get_img(driver, s):
    product_dc = load_json("product.json")

    flag = False # 用來判斷是否要爬圖片

    for key, item in product_dc.items(): 
        if key == "排氣管 (20)": # 被擋IP時，可以設定最後的分類項目，從這邊繼續爬
            flag = True

        if not flag:
            continue 

        for id in item:            
            title = item[id]["title"]
            link = item[id]["link"]
            
            driver.get(link)
            go_to_down(driver)

            img_soup = get_soup(driver, "div.rt-tab-pane img") # 取得商品說明內的圖片

            src = get_soup(driver, "iframe#embedded_goods_comments")[0]["src"] # 賣家輸入的文字區塊是iframe，所以要取得該網址
            driver.switch_to.frame(driver.find_element_by_id("embedded_goods_comments")) # 讀取iframe的html
            iframe_soup = get_soup(driver, "img") # 取得所有img區塊，有些人會用內嵌的方式放圖片

            img_url_ls = [ ele["src"] for ele in img_soup[1:-1]] # 排除掉第一個店家商標跟最後的安全的圖示
            img_url_ls.extend([ ele["src"] for ele in iframe_soup])

            directory = get_directory(DOWNLOAD_DIRECTORY, key, title)
            [download_img(directory, img_url, s) for img_url in img_url_ls]

if __name__ == "__main__":
    # ========== 設定 chrome driver 參數 ==========
    chrome_options = Options()
    # chrome_options.add_argument('--headless') # 隱藏式窗
    driver = webdriver.Chrome(chrome_options=chrome_options)

    # ========== 一些變數 ==========
    DOWNLOAD_DIRECTORY = r"download" # 下載的資料夾位置

    saler_url = "https://www.ruten.com.tw/user/index00.php?s=f2869397"
    prefix_url = "https://www.ruten.com.tw/user/"

    s = requests.session()
    
    # ========== 取得分類項目的名稱跟網址，之後輸出成json，以防爬到一半出錯時還可以用 ==========
    # get_classification(driver, saler_url)

    # ========== 取得分類項目下的商品網址，之後輸出成json，以防爬到一半出錯時還可以用 ==========
    # get_product(driver)

    # ========== 取得商品圖片 ==========
    # get_img(driver, s)
