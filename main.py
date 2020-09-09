from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import requests
import time
import os

# 設定 chrome driver 參數
chrome_options = Options()
# chrome_options.add_argument('--headless') # 隱藏 driver
driver = webdriver.Chrome(chrome_options=chrome_options)

DOWNLOAD_DIRECTORY = r"directory path" # 下載的資料夾位置

prefix_url = "https://www.ruten.com.tw/user/" # 用來處理爬到的網址，部分網址沒有這部分

# 本來想說可以節省程式碼，但是似乎沒有省到多少，不要用好像還比較整潔...
def get_soup(url):
    """
    取得BeautifulSoup
    """
    driver.get(url)
    return BeautifulSoup(driver.page_source, "html.parser")

def get_directory(directory, *args):
    """
    取得目錄路徑，順便檢查是否存在，若不存在就建立目錄
    """
    directory = Path(directory).joinpath(*args)
    if not directory.exists():
        Path.mkdir(directory, parents=True)
    return directory

def download_img(path, ls): 
    """
    下載圖片
    :path str: 資料夾路徑
    :ls list: 圖片網址
    """
    for ele in ls:
        download_url = ele[0]
        file_name = ele[1]

        ir = requests.get(download_url)
        time.sleep(0.3)
        if ir.status_code == 200:
            open(f'{path}\\{file_name}', 'wb').write(ir.content)
            print(f"download '{path}\\{file_name}'")

if __name__ == '__main__':
    # 進入賣場首頁，爬取所有商品分類
    a_soup = get_soup("https://www.ruten.com.tw/user/index00.php?s=f2869397").select("div.sidebar-main.category-listing a")

    # a_soup[1:]撇除掉分類選項-全部商品
    # [(url, title), ...] classification_ls是串列，裡面的資料是tuple，分別代表分類頁面網址以及標題
    classification_ls = [(prefix_url + u["href"], u.text) for u in a_soup[1:]]

    # 從每個分類下去抓所有商品
    for classify in classification_ls:
        get_directory(DOWNLOAD_DIRECTORY, classify[1]) # 建立分類資料夾

        a_soup = get_soup(classify[0]).select("h3.item-name.isDefault-name a") # 取得所有商品網址
        merchandise_ls = [(ele["href"], ele.text) for ele in a_soup] # [(url, title), ...] 分別代表商品頁面網址以及標題

        # 從每個商品頁面下載圖片
        for merchandise in merchandise_ls:
            # 建立商品資料夾
            directory = get_directory(DOWNLOAD_DIRECTORY, classify[1], merchandise[1].rstrip())
            merchandise_soup = get_soup(merchandise[0])

            # 取得左邊小視窗的圖片
            side_img_soup = merchandise_soup.select("div.item-gallery img")
            side_img_ls = [(ele["src"], ele["src"].split("/")[-1]) for ele in side_img_soup]
            download_img(directory, side_img_ls)

            # 取得下方介紹的圖片
            below_img_ls = merchandise_soup.select("div.rt-tab-pane img")
            below_img_ls = [(ele["src"], ele["src"].split("/")[-1]) for ele in below_img_ls[1:-1]]
            download_img(directory, below_img_ls)
