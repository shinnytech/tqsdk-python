#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


from pandas import DataFrame


class TqTimeTable(DataFrame):

    def __init__(self, account=None):
        self.__dict__["_account"] = account
        self.__dict__["_columns"] = ['interval', 'volume', 'price']
        super(TqTimeTable, self).__init__(data=[], columns=self.__dict__["_columns"])
