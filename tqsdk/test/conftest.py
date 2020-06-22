#!/usr/bin/env python
# -*- coding: utf-8 -*-
__time__ = '2020/6/20 11:45'
__author__ = 'Hong Yan'

import pytest
import logging
from _pytest.logging import LogCaptureHandler

@pytest.fixture(autouse=True)
def monkey_logging_emit():
    def mock_emit(self, record: logging.LogRecord) -> None:
        logging.StreamHandler.emit(self, record)
    LogCaptureHandler.emit = mock_emit