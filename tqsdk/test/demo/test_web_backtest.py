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
import multiprocessing as mp
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from tqsdk import TqApi, TqBacktest, TargetPosTask
from tqsdk.exceptions import BacktestFinished

# 子进程要执行的代码
def run_tianqin_code(port):
    try:
        api = TqApi(backtest=TqBacktest(start_dt=date(2018, 5, 5), end_dt=date(2018, 5, 10)), web_gui="127.0.0.1:" + port)
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
    except BacktestFinished as e:
        while True:
            api.wait_update()
    except Exception as e:
        api.close()



class WebBacktestTestOnChrome(unittest.TestCase):
    def setUp(self):
        ctx = mp.get_context('spawn')
        self.port = "8082"
        self.tq_process = ctx.Process(target=run_tianqin_code, args=(self.port,))
        self.tq_process.start()


    def tearDown(self):
        self.tq_process.terminate()


    @unittest.skipIf(not sys.platform.startswith("win"), "test on win")
    def test_on_win(self):
        chromedriver_path = os.path.join(os.getenv("ChromeWebDriver"), "chromedriver.exe")
        run_for_driver(webdriver.Chrome(executable_path=chromedriver_path), self)


    @unittest.skipIf(not sys.platform.startswith("linux"), "test on linux")
    def test_on_linux(self):
        exe_path = os.path.join(os.getenv("CHROMEWEBDRIVER"), "chromedriver")
        opts = ChromeOptions()
        opts.headless = True
        driver = webdriver.Chrome(executable_path=exe_path, options=opts)
        run_for_driver(driver, self)


    @unittest.skipIf(not sys.platform.startswith("darwin"), "test on macos")
    def test_on_macos(self):
        run_for_driver(webdriver.Chrome(), self)


class WebBacktestTestOnFirefox(unittest.TestCase):
    def setUp(self):
        ctx = mp.get_context('spawn')
        self.port = "8081"
        self.tq_process = ctx.Process(target=run_tianqin_code, args=(self.port,))
        self.tq_process.start()


    def tearDown(self):
        self.tq_process.terminate()


    @unittest.skipIf(not sys.platform.startswith("win"), "test on win")
    def test_on_win(self):
        geckodriver_path = os.path.join(os.getenv("GeckoWebDriver"), "geckodriver.exe")
        run_for_driver(webdriver.Firefox(executable_path=geckodriver_path), self)


    @unittest.skipIf(not sys.platform.startswith("linux"), "test on linux")
    def test_on_linux(self):
        exe_path = os.path.join(os.getenv("GECKOWEBDRIVER"), "geckodriver")
        opts = FirefoxOptions()
        opts.headless = True
        driver = webdriver.Firefox(executable_path=exe_path, options=opts)
        run_for_driver(driver, self)


    @unittest.skipIf(not sys.platform.startswith("darwin"), "test on macos")
    def test_on_macos(self):
        run_for_driver(webdriver.Firefox(), self)


def run_for_driver(driver, test):
    time.sleep(10)
    driver.implicitly_wait(30)
    driver.get("http://127.0.0.1:" + test.port)
    wait = WebDriverWait(driver, 30)
    wait.until(EC.title_is("tqsdk-python-web"))  # k线图显示
    logo = driver.find_element_by_tag_name("img")
    test.assertEqual("Tianqin", logo.get_attribute("alt"))
    # K线是否有成交箭头
    chart_main_marks = driver.find_element_by_css_selector("svg.tqchart>g.root g.main.marks")
    trade_arrow_paths = chart_main_marks.find_element_by_css_selector("g.tradearrow")
    wait = WebDriverWait(driver, 30)
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
