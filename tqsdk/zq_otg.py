#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chenli'

import asyncio
import datetime
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from asyncio.subprocess import DEVNULL, PIPE

from tqsdk.exceptions import TqContextManagerError


class ZqOtgContext(object):
    _otg_logs_dir = Path.home() / ".tqsdk" / "otg_logs"
    _otg_config_dir = Path.home() / ".tqsdk" / "otg_config"
    _otg_log_dir_prefix_len = 20
    _otg_log_protect_days = 3

    @staticmethod
    def _get_otg_log_max_dirs():
        return int(os.getenv("TQ_OTG_MAX_LOG_DIRS", 30))

    def __init__(self, api):
        acc_types = ", ".join([type(acc).__name__ for acc in api._account._account_list if acc._account_auth.get("feature") == "tq_direct"])
        try:
            from tqsdk_zq_otg import __version__ as otg_version
            from tqsdk_zq_otg import get_zq_otg_path
        except ImportError:
            raise Exception(f"使用 {acc_types} 账户需要安装 tqsdk_zq_otg 包: pip install -U tqsdk_zq_otg") from None
        if otg_version < "3.9.8":
            raise Exception(f"使用 {acc_types} 账户需要更新 tqsdk_zq_otg 包到最新版本: pip install -U tqsdk_zq_otg")
        self._zq_otg_path = get_zq_otg_path()
        self._zq_otg_exe = str(Path(self._zq_otg_path) / "otg_adapter")
        self._zq_otg_env = os.environ.copy()
        self._zq_otg_env["LD_LIBRARY_PATH"] = str(self._zq_otg_path)
        self._zq_otg_proc = None

    @staticmethod
    def _parse_otg_log_dir_dt(path):
        try:
            return datetime.datetime.strptime(path.name[:ZqOtgContext._otg_log_dir_prefix_len], "%Y%m%d%H%M%S%f")
        except Exception:
            return None

    @staticmethod
    def _clear_otg_logs():
        ZqOtgContext._otg_logs_dir.mkdir(parents=True, exist_ok=True)
        all_dirs = [path for path in ZqOtgContext._otg_logs_dir.iterdir() if path.is_dir()]
        max_dirs = ZqOtgContext._get_otg_log_max_dirs()
        if len(all_dirs) <= max_dirs:
            return
        protect_dt = datetime.datetime.now() - datetime.timedelta(days=ZqOtgContext._otg_log_protect_days)
        parsed_dirs = []
        for path in all_dirs:
            created_at = ZqOtgContext._parse_otg_log_dir_dt(path)
            if created_at is None or created_at >= protect_dt:
                continue
            parsed_dirs.append((created_at, path.name, path))
        parsed_dirs.sort()
        total_dirs = len(all_dirs)
        for _, _, path in parsed_dirs:
            if total_dirs <= max_dirs:
                break
            try:
                shutil.rmtree(path)
                total_dirs -= 1
            except Exception:
                pass

    @staticmethod
    def _create_otg_data_path():
        ZqOtgContext._clear_otg_logs()
        while True:
            dirname = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex}"
            path = ZqOtgContext._otg_logs_dir / dirname
            try:
                path.mkdir(exist_ok=False)
                return path
            except FileExistsError:
                continue

    @staticmethod
    def _get_otg_config_path():
        ZqOtgContext._otg_config_dir.mkdir(parents=True, exist_ok=True)
        return ZqOtgContext._otg_config_dir

    async def __aenter__(self):
        self._zq_otg_data_path = self._create_otg_data_path()
        self._zq_otg_config_path = self._get_otg_config_path()
        return self

    async def get_url(self, url_info):
        """无法启动时抛出 TqContextManagerError 例外"""
        # port_file 是创建在 log_file_path 下的
        port_file = self._zq_otg_data_path / "port.json"

        parameters = json.dumps({
            "log_file_path": str(self._zq_otg_data_path),
            "user_file_path": str(self._zq_otg_config_path),
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
                            return url_info._replace(scheme="ws", netloc=f"127.0.0.1:{port}").geturl()
                await asyncio.sleep(1)
        raise TqContextManagerError("获取交易服务地址失败")

    async def __aexit__(self, exc_type, exc, tb):
        if self._zq_otg_proc is not None:
            self._zq_otg_proc.stdin.close()
            if sys.platform.startswith("win"):
                self._zq_otg_proc.wait()
            else:
                await self._zq_otg_proc.wait()
