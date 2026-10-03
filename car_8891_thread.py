# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 14:51:39 2024

@author: USER

8891中古車爬蟲核心功能
"""
import re
from urllib.parse import quote

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SEARCH_URL = "https://auto.8891.com.tw/?key={}&page={}"
# CSV欄位名稱
COLUMNS = ["標題", "縣市", "價格", "里程", "年份", "圖片連結", "超連結", "內文"]
# 從網頁內嵌資料取出照片網址與車輛編號
IMAGE_PATTERN = re.compile(r'\\"image\\":\\"([^"\\]+)\\"[^{}]*?\\"itemId\\":(\d+)')


def build_url(keyword, page=1):
    # 組出搜尋網址(關鍵字轉為網址編碼)
    return SEARCH_URL.format(quote(keyword), page)


def get_chrome(url, hide=True, timeout=15):
    # 開啟Chrome並載入網頁
    options = webdriver.ChromeOptions()
    if hide:
        options.add_argument("--headless=new")  # 背景執行，不顯示視窗
    options.add_argument("--blink-settings=imagesEnabled=false")  # 不載入圖片
    options.add_argument("--log-level=3")
    chrome = webdriver.Chrome(options=options)
    try:
        chrome.get(url)
        # 等待車輛列表或頁碼載入
        WebDriverWait(chrome, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[class*="row-item"], li.ant-pagination-item')
            )
        )
    except Exception:
        pass  # 查無結果時不再等待
    return chrome


def get_page_source(url):
    chrome = get_chrome(url)
    try:
        return chrome.page_source
    finally:
        chrome.quit()  # 關閉瀏覽器


# 取得總頁數，查無資料回傳0
def get_car_pages(keyword):
    soup = BeautifulSoup(get_page_source(build_url(keyword)), "lxml")
    if not soup.select('a[class*="row-item"]'):
        return 0
    # 頁碼列表的最後一個數字為總頁數
    items = soup.select("li.ant-pagination-item")
    return int(items[-1].text.strip()) if items else 1


def text_of(tag, selector):
    found = tag.select_one(selector)
    return found.text.strip() if found else ""


# 取得單頁所有車輛資料
def get_car_data(keyword, page):
    html = get_page_source(build_url(keyword, page))
    soup = BeautifulSoup(html, "lxml")
    # 車輛編號對應照片網址
    images = {item_id: img for img, item_id in IMAGE_PATTERN.findall(html)}

    datas = []
    # 逐一解析每台車
    for car in soup.select('a[class*="row-item"]'):
        try:
            icons = car.select('[class*="ib-icon"]')
            item = car.select_one("[data-id]")
            item_id = item.get("data-id") if item else ""
            datas.append([
                text_of(car, '[class*="ib-info-title"]'),
                text_of(car, '[class*="ib-ii-item"]'),
                text_of(car, '[class*="ib-price"]'),
                icons[1].text.strip() if len(icons) > 1 else "",
                icons[0].text.strip() if icons else "",
                images.get(item_id, ""),
                # 車輛網址(去除追蹤參數)
                "https://auto.8891.com.tw" + car.get("href").split("?")[0],
                text_of(car, '[class*="ib-info-oldtitle"]'),
            ])
        except Exception as e:
            print("略過一筆資料:", e)  # 略過格式不符的車輛

    return datas


if __name__ == "__main__":
    key = "jimny"
    print("總頁數:", get_car_pages(key))
    for row in get_car_data(key, 1)[:3]:
        print(dict(zip(COLUMNS, row)))
