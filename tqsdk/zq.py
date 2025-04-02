#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chenli'

import asyncio
import json
import sys
from pathlib import Path
import subprocess

from tqsdk.exceptions import TqContextManagerError


class ZqContext(object):
    def __init__(self, api):
        self._api = api
        self._zq_config_path = Path.home() / ".tqsdk" / "zq" / "config" / "zq.json"

    async def __aenter__(self):
        return self

    async def get_url(self, url_info):
        """无法启动时抛出 TqContextManagerError 例外"""
        try:
            with open(self._zq_config_path, 'r') as file:
                config = json.load(file)
                td_url = config["td_url"]
                interpreter = config["interpreter"]
                if sys.platform.startswith("win"):
                    zq_proc = subprocess.Popen([interpreter, "-m", "tqsdk_zq.cli", "start"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    returncode = await self._api._loop.run_in_executor(None, lambda: zq_proc.wait())
                else:
                    zq_proc = await asyncio.create_subprocess_exec(interpreter, "-m", "tqsdk_zq.cli", "start", stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    returncode = await zq_proc.wait()
                if returncode != 0:
                    raise TqContextManagerError(f"无法拉起 zq 进程, 返回码: {returncode}")
                return td_url
        except (OSError, KeyError, json.JSONDecodeError):
            raise Exception(f"加载配置文件失败: {self._zq_config_path}, 请尝试重新初始化: tqsdk-zq init") from None
        except:
            raise TqContextManagerError("获取交易服务地址失败")
    
    async def __aexit__(self, exc_type, exc, tb):
        pass
