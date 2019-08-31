import asyncio
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
        event, values = window.Read(timeout=1)
        if event is None or event == 'Exit':
            break
        window.Element('rb1910.last').Update(quote_a.last_price)
        window.Element('rb2001.last').Update(quote_b.last_price)
        window.Element('spread').Update(quote_b.last_price - quote_a.last_price)

loop.create_task(gui_task())

while True:
    api.wait_update()

