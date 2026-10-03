# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 14:51:39 2024

@author: USER
"""
# from tools import get_chrome #,get_soup
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
#import pandas as pd
import time

def get_chrome(url,path=None,hide=False):
    #path為None時，由Selenium自動下載對應版本的chromedriver
    service=Service(path)
    options=webdriver.ChromeOptions()
    if hide:
        options.add_argument("--headless=new") #不顯示瀏覽器視窗
    try:
        chrome=webdriver.Chrome(service=service,options=options)
        chrome.get(url)
        return chrome
    except Exception as e:
        print(e)
    return None

# 最大頁數
def get_car_pages(url):
    chrome=get_chrome(url)
    time.sleep(1)
    pages=None
    if chrome is not None:        
        soup=BeautifulSoup(chrome.page_source,"lxml")
        items=soup.select("li.ant-pagination-item")
        pages=int(items[-1].text.strip()) if items else 1
        chrome.quit()
        
    return pages



# 取得每頁資料
def get_car_data(url,q):
    chrome=get_chrome(url,hide=True)
    
    datas=[]
    time.sleep(1)
    if chrome is not None:
        soup=BeautifulSoup(chrome.page_source,"lxml")
        cars=soup.select('a[class*="row-item"]')
        for car in cars:
            title=car.select_one('[class*="ib-info-title"]').text.strip()
            content=car.select_one('[class*="ib-info-oldtitle"]').text.strip()
            price=car.select_one('[class*="ib-price"]').text.strip()
            icons=car.select('[class*="ib-icon"]')
            year,km=icons[0].text.strip(),icons[1].text.strip()
            county=car.select_one('[class*="ib-ii-item"]').text.strip()
            car_url="https://auto.8891.com.tw"+car.get("href")
            img=car.select_one('[class*="ib-image"] img') #圖片為延遲載入，未載入時為空
            image_url=img.get("data-src") if img else ""
            #print(title,county,content,price,year,km,car_url,image_url,sep="\n")
            #順序對應GUI的欄位:標題,縣市,價格,里程,年份,圖片連結,超連結,內文
            datas.append([title,county,price,km,year,image_url,car_url,content])
            #print("-"*80)   
        chrome.quit()
    else:
        print("chrome啟動失敗")

    q.put(datas)
    return datas    



if __name__=="__main__":
    key="jimny"    
    url=f"https://auto.8891.com.tw/?key={key}"
    pages=get_car_pages(url)
    print(pages)
    datas=get_car_data(url)
    print(datas)
    
    
    
    
    
    
    
