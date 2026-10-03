# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 15:16:29 2024

@author: USER
"""

from car_8891_thread import get_car_pages,get_car_data  
import pandas as pd
from threading import Thread
from queue import Queue

url="https://auto.8891.com.tw/?key={}&page={}"
q=Queue()
pages=0
cars=None


def search_car_thread():
    Thread(target=search_car).start()


def search_pages_thread():
    Thread(target=search_pages).start()
    
    
def search_pages():
    global pages,cars
    cars=entry.get()
    cars_url=url.format(cars,1)
    button.config(state=tk.DISABLED) #查找中關閉按鈕使用
    label3.config(text="查找頁數中...")
    pages=get_car_pages(cars_url)
    label2.config(text=f"共{pages}頁")
    label3.config(text="查找完畢")
    button.config(state=tk.NORMAL) #查找完開啟按鈕使用

    
    if pages>0:
        button1.config(state=tk.NORMAL) #開啟按鈕狀態
        
def search_car():
    button.config(state=tk.DISABLED)
    button1.config(state=tk.DISABLED)
    datas=[]
    threads=[]
    max_page=5
    
    for i in range(int(entry1.get()),int(entry2.get())+1):
        if i%max_page==0:
            label3.config(text=f"查找第{i-4}~{i}頁中...")
        else:
            label3.config(text=f"查找第{i+1-i%max_page}~{i}頁中...")
        
        #改成執行緒
        t=Thread(target=get_car_data,args=(url.format(cars,i),q))
        threads.append(t)
        
        if i%max_page==0:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
                
            threads=[]
    
    #剩下的頁數
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for i in range(q.qsize()):
        data=q.get()
        if len(data)>0:
            datas+=data
            
        # data=get_car_data(url.format(cars,i))
        # if len(data)>0:
        #     datas+=data

        
    df=pd.DataFrame(datas,columns=["標題","縣市","價格","里程","年份","圖片連結","超連結","內文"])
    df=df.set_index("標題")
    df.to_csv(f"8891_{cars}.csv",encoding="utf-8-sig")
    label3.config(text="檔案儲存完畢")
    button.config(state=tk.NORMAL)


import tkinter as tk

car=tk.Tk()

car.title("8891爬蟲app v0.1")
car.geometry("300x400")

label=tk.Label(car,text="8891爬蟲GUI",font=("標楷體",24),fg="blue")
label.pack(pady=12)

label1=tk.Label(car,text="關鍵字",font=("標楷體",16))
label1.pack()

entry=tk.Entry(car,font=("標楷體",14),justify="center")
entry.pack()

button=tk.Button(car,text="查找總頁數",font=("標楷體",16),command=search_pages_thread)
button.pack(pady=6)

label2=tk.Label(car,text="尚未查找",font=("標楷體",16))
label2.pack()

label3=tk.Label(car,text="",font=("標楷體",16),bg="#02F78E")
label3.pack(padx=9,pady=9,expand=1,fill="both")

button1=tk.Button(car,text="開始",font=("標楷體",16),command=search_car_thread,fg="red")
button1.pack(side="bottom",pady=6)

entry1=tk.Entry(car,font=("標楷體",14),width=5,justify="center")
entry1.pack(side="left",pady=3,padx=3,fill="x",expand=1)

entry2=tk.Entry(car,font=("標楷體",14),width=5,justify="center")
entry2.pack(side="right",pady=3,padx=3,fill="x",expand=1)



button1.config(state=tk.DISABLED)  #預設按鈕為關閉狀態




car.mainloop()