# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 15:16:29 2024

@author: USER
"""

from car_8891_thread import COLUMNS,get_car_data,get_car_pages
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox,ttk
from concurrent.futures import ThreadPoolExecutor,as_completed
from threading import Thread
import pandas as pd

MAX_WORKERS=5 #同時爬取的頁數上限
SAVE_DIR=os.path.join(os.path.expanduser("~"),"Downloads") #CSV存檔資料夾(下載)
if not os.path.isdir(SAVE_DIR):
    SAVE_DIR=os.path.expanduser("~") #沒有下載資料夾時存到使用者資料夾
FONT="微軟正黑體"

cars=""
save_path=""


#在主執行緒更新畫面
def ui(func,*args,**kwargs):
    car.after(0,lambda:func(*args,**kwargs))


def set_status(text,color="#333333"):
    ui(status_label.config,text=text,foreground=color)


def set_busy(busy):
    def apply():
        state=tk.DISABLED if busy else tk.NORMAL
        search_button.config(state=state)
        keyword_entry.config(state=state)
        #有頁數時才能按開始
        can_start=not busy and pages_var.get()>0
        start_button.config(state=tk.NORMAL if can_start else tk.DISABLED)
    ui(apply)


# 步驟1：查詢頁數
def search_pages_thread(event=None):
    keyword=keyword_entry.get().strip()
    if not keyword:
        messagebox.showwarning("提醒","請先輸入要搜尋的車款關鍵字，例如：jimny")
        return
    Thread(target=search_pages,args=(keyword,),daemon=True).start()


def search_pages(keyword):
    global cars
    cars=keyword
    ui(pages_var.set,0)
    set_busy(True)
    ui(progress.config,mode="indeterminate",maximum=100)
    ui(progress.start,10)
    set_status(f"正在查詢「{cars}」的總頁數，請稍候...")

    try:
        pages=get_car_pages(cars)
    except Exception as e:
        pages=-1
        print("查詢失敗:",e)

    ui(progress.stop)
    ui(progress.config,mode="determinate",value=0)
    if pages>0:
        ui(pages_var.set,pages)
        ui(pages_label.config,text=f"共 {pages} 頁（每頁約 40 筆）",foreground="#1E7E34")
        #頁數範圍預設為全部頁數
        ui(start_spin.config,to=pages)
        ui(end_spin.config,to=pages)
        ui(start_var.set,1)
        ui(end_var.set,pages)
        set_status("查詢完成，請確認頁數範圍後按「開始爬取」","#1E7E34")
    elif pages==0:
        ui(pages_label.config,text="查無資料",foreground="#C0392B")
        set_status("找不到符合的車輛，請換個關鍵字試試","#C0392B")
    else:
        ui(pages_label.config,text="查詢失敗",foreground="#C0392B")
        set_status("Chrome 啟動失敗，請確認電腦已安裝 Google Chrome","#C0392B")
    set_busy(False)


# 步驟2：爬取資料
def search_car_thread():
    try:
        start,end=int(start_var.get()),int(end_var.get())
    except ValueError:
        messagebox.showwarning("提醒","頁數請輸入數字")
        return
    total=pages_var.get()
    if not 1<=start<=end<=total:
        messagebox.showwarning("提醒",f"頁數範圍需介於 1 ~ {total}，且起始頁不能大於結束頁")
        return
    Thread(target=search_car,args=(start,end),daemon=True).start()


def search_car(start,end):
    global save_path
    set_busy(True)
    ui(open_button.config,state=tk.DISABLED)
    page_count=end-start+1
    ui(progress.config,maximum=page_count,value=0)
    set_status(f"正在爬取第 {start} ~ {end} 頁（0/{page_count}）...")

    datas=[]
    done=0
    #多執行緒爬取各頁資料
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures=[pool.submit(get_car_data,cars,i) for i in range(start,end+1)]
        for future in as_completed(futures):
            done+=1
            try:
                datas+=future.result()
            except Exception as e:
                print("爬取失敗:",e)
            ui(progress.config,value=done)
            set_status(f"正在爬取第 {start} ~ {end} 頁（{done}/{page_count}），已取得 {len(datas)} 筆")

    if not datas:
        set_status("沒有抓到任何資料，請換個關鍵字或稍後再試","#C0392B")
        set_busy(False)
        return

    df=pd.DataFrame(datas,columns=COLUMNS)
    #去除重複車輛
    df=df.drop_duplicates(subset="超連結").set_index("標題")
    save_path=os.path.join(SAVE_DIR,f"8891_{cars}.csv")
    try:
        df.to_csv(save_path,encoding="utf-8-sig")
    except PermissionError:
        set_status("存檔失敗：CSV 檔案正被 Excel 開啟，請關閉後再試一次","#C0392B")
        set_busy(False)
        return

    set_status(f"完成！共 {len(df)} 筆，已存到：\n{save_path}","#1E7E34")
    ui(open_button.config,state=tk.NORMAL)
    set_busy(False)


def open_file():
    if not (save_path and os.path.exists(save_path)):
        return
    #用系統預設程式開啟CSV
    if sys.platform=="win32":
        os.startfile(save_path)
    elif sys.platform=="darwin":
        subprocess.run(["open",save_path])
    else:
        subprocess.run(["xdg-open",save_path])


# 介面
car=tk.Tk()
car.title("8891中古車爬蟲 v0.2")
car.geometry("440x500")
car.resizable(False,False)

style=ttk.Style()
style.configure("TLabel",font=(FONT,11))
style.configure("TButton",font=(FONT,11),padding=4)
style.configure("TLabelframe.Label",font=(FONT,11,"bold"))
style.configure("Accent.TButton",font=(FONT,12,"bold"),padding=6)

pages_var=tk.IntVar(value=0)
start_var=tk.StringVar(value="1")
end_var=tk.StringVar(value="1")

tk.Label(car,text="8891 中古車爬蟲",font=(FONT,20,"bold"),fg="#1F5FAD").pack(pady=(14,0))
ttk.Label(car,text="輸入車款 → 查詢頁數 → 選擇範圍 → 開始爬取，結果會存成 CSV",
          foreground="#666666",font=(FONT,9)).pack(pady=(2,10))

#步驟1
step1=ttk.LabelFrame(car,text=" 步驟 1：輸入車款關鍵字 ",padding=10)
step1.pack(fill="x",padx=16,pady=4)
keyword_entry=ttk.Entry(step1,font=(FONT,12))
keyword_entry.pack(side="left",fill="x",expand=True,padx=(0,8))
keyword_entry.bind("<Return>",search_pages_thread) #按Enter查詢頁數
keyword_entry.focus()
search_button=ttk.Button(step1,text="查詢頁數",command=search_pages_thread)
search_button.pack(side="right")

pages_label=ttk.Label(car,text="尚未查詢",foreground="#888888")
pages_label.pack(pady=4)

#步驟2
step2=ttk.LabelFrame(car,text=" 步驟 2：選擇要爬取的頁數範圍 ",padding=10)
step2.pack(fill="x",padx=16,pady=4)
range_row=ttk.Frame(step2)
range_row.pack()
ttk.Label(range_row,text="從第").pack(side="left")
start_spin=ttk.Spinbox(range_row,from_=1,to=1,width=5,textvariable=start_var,
                       justify="center",font=(FONT,11))
start_spin.pack(side="left",padx=4)
ttk.Label(range_row,text="頁　到第").pack(side="left")
end_spin=ttk.Spinbox(range_row,from_=1,to=1,width=5,textvariable=end_var,
                     justify="center",font=(FONT,11))
end_spin.pack(side="left",padx=4)
ttk.Label(range_row,text="頁").pack(side="left")

#步驟3
step3=ttk.LabelFrame(car,text=" 步驟 3：開始爬取 ",padding=10)
step3.pack(fill="x",padx=16,pady=4)
start_button=ttk.Button(step3,text="開始爬取",style="Accent.TButton",
                        command=search_car_thread,state=tk.DISABLED)
start_button.pack(fill="x")
progress=ttk.Progressbar(step3,mode="determinate")
progress.pack(fill="x",pady=(10,0))

status_label=ttk.Label(car,text="請先輸入關鍵字並查詢頁數",wraplength=400,justify="center")
status_label.pack(pady=10)

open_button=ttk.Button(car,text="開啟 CSV 檔案",command=open_file,state=tk.DISABLED)
open_button.pack()

car.mainloop()
