#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chenli'

import asyncio
import json
import os
import tempfile
import sys
import subprocess
from pathlib import Path
from asyncio.subprocess import DEVNULL, PIPE


class ZqOtgContext(object):
    def __init__(self, api):
        acc_types = ", ".join([type(acc).__name__ for acc in api._account._account_list if acc._account_auth.get("feature") == "tq_direct"])
        try:
            from tqsdk_zq_otg import __version__ as otg_version
            from tqsdk import __version__ as tqsdk_version
            from tqsdk_zq_otg import get_zq_otg_path
        except ImportError:
            raise Exception(f"使用 {acc_types} 账户需要安装 tqsdk_zq_otg 包: pip install -U tqsdk_zq_otg") from None
        if otg_version != tqsdk_version:
            raise Exception(f"使用 {acc_types} 账户需要更新 tqsdk_zq_otg 包到最新版本: pip install -U tqsdk_zq_otg")
        self._zq_otg_path = get_zq_otg_path()
        self._zq_otg_exe = str(Path(self._zq_otg_path) / "otg_adapter")
        self._zq_otg_env = os.environ.copy()
        self._zq_otg_env["LD_LIBRARY_PATH"] = str(self._zq_otg_path)
        self._zq_otg_proc = None

    async def __aenter__(self):
        self._zq_otg_data_dir = tempfile.TemporaryDirectory()
        self._zq_otg_data_path = Path(self._zq_otg_data_dir.name)
        return self

    async def get_addr(self):
        """无法启动时返回空字符串"""
        # port_file 是创建在 log_file_path 下的
        port_file = self._zq_otg_data_path / "port.json"

        parameters = json.dumps({
            "log_file_path": str(self._zq_otg_data_path),
            "user_file_path": str(self._zq_otg_data_path),
            "host": "127.0.0.1",
            "port": 0,
        })

        if self._zq_otg_proc is not None and sys.platform.startswith("win"):
            # subprocess.Popen 需要调用 poll 才会更新 returncode
            self._zq_otg_proc.poll()
        if self._zq_otg_proc is None or self._zq_otg_proc.returncode is not None:
            if sys.platform.startswith("win"):
                self._zq_otg_proc = subprocess.Popen([self._zq_otg_exe, f"--config={parameters}", "--mode=cmd"], stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL, env=self._zq_otg_env)
            else:
                self._zq_otg_proc = await asyncio.create_subprocess_exec(self._zq_otg_exe, f"--config={parameters}", "--mode=cmd", stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL, env=self._zq_otg_env)

            for i in range(30):
                if port_file.exists():
                    with open(port_file, 'r') as file:
                        port = json.load(file)["port"]
                        if port != 0:
                            return f"127.0.0.1:{port}"
                await asyncio.sleep(1)

        return ""

    async def __aexit__(self, exc_type, exc, tb):
        if self._zq_otg_proc is not None:
            self._zq_otg_proc.stdin.close()
            if sys.platform.startswith("win"):
                self._zq_otg_proc.wait()
            else:
                await self._zq_otg_proc.wait()
        self._zq_otg_data_dir.cleanup()
