#!usr/bin/env python3
#-*- coding:utf-8 -*-
"""
@author: yanqiong
@file: futures_spot_spreads.py
@create_on: 2019/9/27
@description: 演示如何使用 Tqsdk 计算期货和现货价差，并使用 GUI 界面展示
    除了 Tqsdk 还需要提前安装的工具包 :
    PySimpleGUI (https://pysimplegui.readthedocs.io/en/latest/)
    matplotlib (https://matplotlib.org/)
    mplcursors (https://mplcursors.readthedocs.io/en/stable/index.html)
"""

import sys
import math
import asyncio
import numpy as np
import pandas as pd
import PySimpleGUI as sg
import webbrowser
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplcursors
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from tqsdk import TqApi

# 现货、期货合约对应列表
SymbolDict = {
    "al - 铝": ["SSWE.ALH", "KQ.m@SHFE.al", "orange"],
    "cu - 铜": ["SSWE.CUH", "KQ.m@SHFE.cu", "deepskyblue"],
    "ni - 镍": ["SSWE.NIH", "KQ.m@SHFE.ni", "red"],
    "pb - 铅": ["SSWE.PBH", "KQ.m@SHFE.pb", "lightseagreen"],
    "ru - 天然橡胶": ["SSWE.RUH", "KQ.m@SHFE.ru", "olive"],
    "sn - 锡": ["SSWE.SNH", "KQ.m@SHFE.sn", "burlywood"],
    "zn - 锌": ["SSWE.ZNH", "KQ.m@SHFE.zn", "deeppink"]
}
ProductList = list(SymbolDict.keys())
DataLength = 40 # 显示最近10日价差
IndexList = np.arange(DataLength)

# ------------------------------- TqSdk Helper Code -------------------------------
links = {
     "_LINK_":  "https://www.shinnytech.com/support-tianqin/",
     "_TITLE_": "https://www.shinnytech.com/tianqin/"
}

def open_link (url = 'https://www.shinnytech.com/tianqin/'):
    webbrowser.open_new(url)

def get_product_name (product_id):
    return product_id.split(' - ')[1]

# ------------------------------- Tqsdk 业务代码 -------------------------------
loop = asyncio.get_event_loop()
api = TqApi(loop=loop)

SelectedProductId = ProductList[0] # 默认选择的品种

klines_series = [[api.get_kline_serial(SymbolDict[i][0], 86400, DataLength), api.get_kline_serial(SymbolDict[i][1], 86400, DataLength)] for i in SymbolDict]
def prepare_data (product_id) :
    ind = ProductList.index(product_id)
    return pd.to_datetime(klines_series[ind][1]["datetime"] / 1e9, unit='s', origin=pd.Timestamp('1970-01-01')), klines_series[ind][0]["close"] - klines_series[ind][1]["close"]
dt_series, spread_series = prepare_data(SelectedProductId)

# ------------------------------- Matplotlib Code -------------------------------
fig, ax = plt.subplots()
fig.set_size_inches(6, 4)

def format_date(x, pos=None):
    if pos is None:
        return dt_series[int(x)].strftime("%Y%m%d")
    else:
        ind = np.clip(int(x + 0.5), 0, DataLength - 1) # 保证下标不越界
        return dt_series[ind].strftime("%Y%m%d")
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date)) # 格式化 X 轴显示

def prepare_plot():
    if dt_series[0] == dt_series[1]:
        return
    [spread_min, spread_max] = [np.min(spread_series), np.max(spread_series)]
    padding = (spread_max - spread_min) * 0.05
    ax.set_ylim(spread_min - padding, spread_max + padding)
    lines = ax.plot(IndexList, spread_series, "o-", color=SymbolDict[SelectedProductId][2])
    c2 = mplcursors.cursor(lines, hover=True)
    @c2.connect("add")
    def _(sel):
        ann = sel.annotation
        ann.get_bbox_patch().set(fc="#DBEDAC", alpha=.5)
        date_text = ann.get_text().replace('x=', 'date: ').split('\n')[0]
        ann.set_text("{}\n spread: {}".format(date_text, math.floor(sel.target[1])))
    ax.grid(True)
    fig.autofmt_xdate()

fig = plt.gcf()  # if using Pyplot then get the figure from the plot
figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds

# ------------------------------- Matplotlib helper code -----------------------
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def draw_toolbar(canvas, root):
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas._tkcanvas.pack(side='top', fill='both', expand=1)
    return

fig_canvas_agg = None

# ------------------------------- PySimpleGui Task Code  -----------------------
async def gui_task():
    global SelectedProductId, dt_series, spread_series, fig_canvas_agg
    product_list = list(SymbolDict.keys())
    # 界面布局
    fontStyle = 'Any 14'
    layout = [[sg.Text('现货期货价差 - 天勤量化', enable_events='true', font='Any 18', key='_TITLE_'),
               sg.Text('点击了解【天勤量化】和如何实现这个小工具', enable_events='true', font='Any 14', text_color='blue', key='_LINK_',
                       size=(80, 1), justification="right")],
              [
                  sg.Frame(
                  title='',
                  font='Any 12',
                  border_width=0,
                  size=(20, 12),
                  pad=(0, 2),
                  layout=[
                      [sg.Listbox(values=product_list, default_values=[product_list[0]], enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, size=(20, 7), pad=(0, 20), font='Any 14', key="_PRODUCT_")],
                      # [sg.Text(' ' * 60)], [sg.Text(' ' * 60)],
                      [sg.Text("行情最后更新时间", size=(20, 1), font=fontStyle), sg.Text("-------", size=(20, 1), font=fontStyle, key="datetime")],
                      [sg.Text(get_product_name(SelectedProductId) + " 现货最新价", size=(20, 1), font=fontStyle, key="spot.name"), sg.Text("仓单报价", font=fontStyle, key="spot.last")],
                      [sg.Text(get_product_name(SelectedProductId) + " 期货主连最新价", size=(20, 1), font=fontStyle, key="future.name"), sg.Text("期货报价", font=fontStyle, key="future.last"), sg.Text("期货涨跌幅", font=fontStyle, key="future.change")],
                      [sg.Text("期货现货价差", size=(20, 1), font=fontStyle), sg.Text("差价", size=(20, 1), font=fontStyle, key="spread")],
                      [sg.Text('_' * 60, text_color="grey")],
                      [sg.Text("价格信息来自【天勤量化】，仅供参考", font='Any 10', size=(50, 1), text_color="grey", justification="right")]
                  ],
                  relief=sg.RELIEF_SUNKEN,
                  tooltip='Use these to set flags'),
                  sg.Canvas(size=(figure_w, figure_h), key='canvas')
              ]
            ]
    window = sg.Window('现货期货价差 - 天勤量化', layout, finalize=True)
    # 在 canvas 处绘制图表
    prepare_plot()
    fig_canvas_agg = draw_figure(window['canvas'].TKCanvas, fig)
    # toolbar_canvas_agg = draw_toolbar(fig_canvas_agg, window.TKroot)
    # 获取合约引用
    quote_spot = api.get_quote(SymbolDict[SelectedProductId][0])
    quote_future = api.get_quote(SymbolDict[SelectedProductId][1])

    while True:
        event, values = window.Read(timeout=0)
        if event == "_PRODUCT_":
            if SelectedProductId != values[event][0]:
                SelectedProductId = values[event][0]
                dt_series, spread_series = prepare_data(SelectedProductId)
                if len(ax.lines) > 0: ax.lines.pop()
                prepare_plot()
                fig_canvas_agg.draw()
                window.Element('spot.name').Update(get_product_name(SelectedProductId) + " 现货最新价")
                window.Element('future.name').Update(get_product_name(SelectedProductId) + " 期货主连最新价")
                window.Element('future.change').Update("()")
                # 更新合约引用
                quote_spot = api.get_quote(SymbolDict[SelectedProductId][0])
                quote_future = api.get_quote(SymbolDict[SelectedProductId][1])
        elif event == "_LINK_" or event == "_TITLE_":
            open_link(links[event])
        if event is None or event == 'Exit':
            sys.exit(0)

        # 更新界面数据
        window.Element('datetime').Update(quote_future.datetime[:19])
        window.Element('spot.last').Update('nan' if math.isnan(quote_spot.last_price) else int(quote_spot.last_price))
        window.Element('future.last').Update('nan' if math.isnan(quote_future.last_price) else int(quote_future.last_price))

        future_change = (quote_future.last_price - quote_future.pre_settlement) / quote_future.pre_settlement * 100
        if math.isnan(future_change):
            window.Element('future.change').Update("(nan)", text_color = "black")
        else:
            window.Element('future.change').Update(
                "({}%)".format(round(future_change, 2)), text_color="red" if future_change >= 0 else "green")

        spread = quote_spot.last_price - quote_future.last_price
        window.Element('spread').Update('nan' if  math.isnan(spread) else int(spread))
        await asyncio.sleep(0.001)  # 注意, 这里必须使用 asyncio.sleep, 不能用time.sleep

loop.create_task(gui_task())

# ------------------------------- TqApi Task Code  -----------------------
while True:
    api.wait_update()
