import asyncio
import sys
import PySimpleGUI as sg
from tqsdk import TqApi

loop = asyncio.get_event_loop()
api = TqApi(loop=loop)
quote_a = api.get_quote("SHFE.rb1910")
quote_b = api.get_quote("SHFE.rb2001")


async def gui_task():
    layout = [[sg.Text('rb1910'), sg.Text("99999", key="rb1910.last")],
              [sg.Text('rb2001'), sg.Text("99999", key="rb2001.last")],
              [sg.Text('spread'), sg.Text("99999", key="spread")],
              ]

    window = sg.Window('价差显示', layout)

    while True:
        event, values = window.Read(timeout=0)
        if event is None or event == 'Exit':
            sys.exit(0)
        window.Element('rb1910.last').Update(quote_a.last_price)
        window.Element('rb2001.last').Update(quote_b.last_price)
        window.Element('spread').Update(quote_b.last_price - quote_a.last_price)
        await asyncio.sleep(1)  # 注意, 这里必须使用 asyncio.sleep, 不能用time.sleep


api.create_task(gui_task())

while True:
    api.wait_update()
