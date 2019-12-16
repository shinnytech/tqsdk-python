#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import sys


class BacktestFinished(Exception):
    """回测结束会抛出此例外"""

    _orig_excepthook = None

    def __init__(self, api):
        message = "回测结束"
        self._logger = api._logger.getChild("BacktestFinished")
        super().__init__(message)
        if BacktestFinished._orig_excepthook is None:
            BacktestFinished._orig_excepthook = sys.excepthook

            def _except_catcher(type, value, traceback):
                if type is BacktestFinished:
                    if api._web_gui:
                        try:
                            self._logger.warning("----------- Backtest finished, press [Ctrl + C] to exit. -----------")
                            while True:
                                api.wait_update()
                        except KeyboardInterrupt:
                            pass

                    if not api._loop.is_closed():
                        api.close()
                    sys.exit()
                BacktestFinished._orig_excepthook(type, value, traceback)

            sys.excepthook = _except_catcher
