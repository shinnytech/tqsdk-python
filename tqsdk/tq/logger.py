#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import logging
import asyncio

class WidgetLogger(logging.Handler):
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.widget = widget

    def emit(self, record):
        self.widget.append(self.format(record))

def log_task_exception(logger, name, task):
    try:
        exception = task.exception()
        if exception:
            logger.error("%s 遇到错误", name, exc_info=exception)
    except asyncio.CancelledError:
        pass
