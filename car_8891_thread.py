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

def get_chrome(url,path=r"C:\Users\user\Desktop\py2\解壓縮檔\chromedriver-win64\chromedriver.exe"):
    service=Service(path)
    try:
        chrome=webdriver.Chrome(service=service)
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
        pages=int(soup.find("div",class_="_pages_ivprf_7").find_all("button")[-1].text.strip())
        chrome.quit()
        
    return pages



# 取得每頁資料
def get_car_data(url,q):
    chrome=get_chrome(url,hide=True)
    
    datas=[]
    time.sleep(1)
    if chrome is not None:
        soup=BeautifulSoup(chrome.page_source,"lxml")
        cars=soup.find(id="search-result").find_all("a")        
        for car in cars:
            title=car.find("div",class_="ib-info-title").text.strip()            
            content=car.find("div",class_="ib-info-oldtitle").text.strip()
            infos=car.find("div",class_="ib-row ib-extra").text.strip().split()
            price,year,km=infos[0],infos[-2],infos[-1]
            county=car.find("span",class_="ib-ii-item").text.strip()
            car_url="https://auto.8891.com.tw/"+car.get("href")
            image_url=car.find("img").get("data-src")        
            #print(title,county,content,price,year,km,car_url,image_url,sep="\n")
            datas.append([title,county,content,price,year,km,car_url,image_url])
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
    
    
    
    
    
    
    
