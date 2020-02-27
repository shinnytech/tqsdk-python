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
from tqsdk import TqApi
from tqsdk.ta import MA


# 子进程要执行的代码
def run_tianqin_code(port):
    try:
        api = TqApi(web_gui="127.0.0.1:" + port)
        klines = api.get_kline_serial("SHFE.au1910", 24 * 60 * 60)
        ma = MA(klines, 30)  # 使用tqsdk自带指标函数计算均线
        while True:
            api.wait_update()
    except Exception as e:
        api.close()

class WebTestOnChrome(unittest.TestCase):
    def setUp(self):
        ctx = mp.get_context('spawn')
        self.port = "8084"
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


class WebTestOnFirefox(unittest.TestCase):
    def setUp(self):
        ctx = mp.get_context('spawn')
        self.port = "8083"
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
    account_info = driver.find_element_by_class_name("account-info")
    accounts = account_info.find_elements_by_tag_name("div")
    test.assertEqual(5, len(accounts))
    # 测试K线图是否显示
    chart_main_candle = driver.find_element_by_css_selector("svg.tqchart>g.root g.plot.main.candle")
    main_candle_paths = chart_main_candle.find_elements_by_tag_name("path")
    test.assertEqual(6, len(main_candle_paths))
    up_body = chart_main_candle.find_element_by_css_selector("path.candle.body.up")
    down_body = chart_main_candle.find_element_by_css_selector("path.candle.body.down")
    up_line = chart_main_candle.find_element_by_css_selector("path.candle.line.equal")
    down_line = chart_main_candle.find_element_by_css_selector("path.candle.line.equal")
    wait = WebDriverWait(driver, 30)
    wait.until(path_element_has_d(up_body))  # k线图显示
    wait.until(path_element_has_d(down_body))
    wait.until(path_element_has_d(up_line))
    wait.until(path_element_has_d(down_line))
    driver.close()

class path_element_has_d(object):
    """
    path  element 对象有内容
    """
    def __init__(self, element):
        self.element = element

    def __call__(self, driver):
        d = self.element.get_attribute("d")
        if not d:
            return False
        return d


if __name__ == "__main__":
    unittest.main()
