#!usr/bin/env python3
#-*- coding:utf-8 -*-
"""
@author: yanqiong
@file: test_web.py
@create_on: 2020/2/12
@description: "Users/yanqiong/Documents/geckodriver-v0.26.0-macos.tar.gz"
"""
import os
import sys
import time
import unittest
from multiprocessing import Process
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from tqsdk import TqApi, TqBacktest, TargetPosTask

# 子进程要执行的代码
def run_tianqin_code(port):
    try:
        api = TqApi(backtest=TqBacktest(start_dt=date(2018, 5, 5), end_dt=date(2018, 5, 10)), web_gui=":" + port)
        klines = api.get_kline_serial("DCE.m1901", 5 * 60, data_length=15)
        target_pos = TargetPosTask(api, "DCE.m1901")
        while True:
            api.wait_update()
            if api.is_changing(klines):
                ma = sum(klines.close.iloc[-15:]) / 15
                if klines.close.iloc[-1] > ma:
                    target_pos.set_target_volume(5)
                elif klines.close.iloc[-1] < ma:
                    target_pos.set_target_volume(0)

    except Exception as e:
        api.close()

class WebBacktestTest(unittest.TestCase):

    def setUp(self):
        self.port = "9878"
        self.tq_process = Process(target=run_tianqin_code, args=(self.port, ))
        self.tq_process.start()

    def tearDown(self):
        self.tq_process.terminate()

    def test_web_firefox(self):
        if sys.platform.startswith("win"):
            exe_path = os.path.join(os.getenv("GeckoWebDriver"), "geckodriver.exe")
            driver = webdriver.Firefox(executable_path=exe_path)
        elif sys.platform.startswith("linux"):
            exe_path = os.path.join(os.getcwd(), "geckodriver")
            opts = FirefoxOptions()
            opts.headless = True
            driver = webdriver.Firefox(executable_path=exe_path, options=opts)
        else:
            return
        run_for_driver(driver, self)

    def test_web_chrome(self):
        if sys.platform.startswith("win"):
            exe_path = os.path.join(os.getenv("ChromeWebDriver"), "chromedriver.exe")
            driver = webdriver.Chrome(executable_path=exe_path)
        elif sys.platform.startswith("linux"):
            exe_path = os.path.join(os.getcwd(), "chromedriver")
            opts = ChromeOptions()
            opts.headless = True
            driver = webdriver.Chrome(executable_path=exe_path, options=opts)
        elif sys.platform.startswith("darwin"):
            exe_path = os.path.join(os.getcwd(), "chromedriver")
            opts = ChromeOptions()
            opts.headless = True
            driver = webdriver.Chrome(executable_path=exe_path)
        else:
            return
        run_for_driver(driver, self)


def run_for_driver(driver, test):
    time.sleep(10)
    driver.implicitly_wait(30)
    driver.get("http://127.0.0.1:" + test.port)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.title_is("tqsdk-python-web"))  # k线图显示
    logo = driver.find_element_by_tag_name("img")
    test.assertEqual("Tianqin", logo.get_attribute("alt"))
    # K线是否有成交箭头
    chart_main_marks = driver.find_element_by_css_selector("svg.tqchart>g.root g.main.marks")
    trade_arrow_paths = chart_main_marks.find_element_by_css_selector("g.tradearrow")
    wait = WebDriverWait(driver, 10)
    wait.until(element_has_child(trade_arrow_paths, "path"))
    # 成交列表是否显示
    trades_table = driver.find_element_by_css_selector("div.reports.trades-table>table")
    wait = WebDriverWait(driver, 30)
    wait.until(element_has_child(trades_table, "tbody>tr"))
    driver.close()


class element_has_child(object):
    def __init__(self, element, css_selector):
        self.element = element
        self.css_selector = css_selector

    def __call__(self, driver):
        children = self.element.find_element_by_css_selector(self.css_selector)
        print("children", children)
        if not children:
            return False
        return True


if __name__ == "__main__":
    unittest.main()
