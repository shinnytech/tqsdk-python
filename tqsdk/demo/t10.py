#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi

api = TqApi("SIM")
quote = api.get_quote("SHFE.cu1812")

while api.peek_message():
    print(quote)