#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import asyncio
import json
import os
import logging
import uuid
import sys
import subprocess
from pathlib import Path
from asyncio.subprocess import PIPE

from tqsdk_sm import get_sm_path


class SMContext(object):
    def __init__(self, logger, api, sm_type, sm_data, sm_user, sm_pwd):
        self._logger = logger
        self._api = api
        self._sm_type = sm_type
        self._sm_data = sm_data
        sm_path = get_sm_path()
        self._sm_exe = str(sm_path/sm_type)
        self._sm_env = os.environ.copy()
        self._sm_env["LD_LIBRARY_PATH"] = str(sm_path)
        data_path = Path.home()/".tqsdk"/self._sm_type/sm_user
        data_path.mkdir(parents=True, exist_ok=True)
        self._sm_init = {
            # smi
            "DeviceId": hex(uuid.getnode()),
            "CertLog": str(data_path/"smi_cert.log"),
            "SdkLog": str(data_path/"smi_sdk.log"),
            # smf
            "Debug": True,
            "LogPath": str(data_path),
            "Timeout": 10000000000,
            # sms
            "LogFile":str(data_path/"syd.log"),
        }
        self._sm_cfg = {
            "UserId": sm_user,
            "Password": sm_pwd,
            "DataPath": str(data_path),
        }
        self._sm_addr = ""

    _log_level_map = {
        "trace": logging.DEBUG,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "fatal": logging.FATAL,
        "panic": logging.CRITICAL,
    }

    def _process_log(self, line):
        # 仅处理完整的一行, 由于退出时先结束进程, 因此可能会输出半行日志
        if line and line[-1] == '\n' and line[:-1]:
            try:
                sm_log = json.loads(line[:-1])
            except json.JSONDecodeError:
                self._logger.error("sm error msg", error=line[:-1])
                return
            level = self._log_level_map[sm_log["level"]]
            self._logger.log(level, "sm log", pack=sm_log)
            if sm_log["msg"] == "NewConnection failed":
                err = sm_log["error"].split(":")[-1]
                if (self._sm_type in ["smi", "sms"] and err == "a000407") or (self._sm_type == "smf" and err == "-333700009"):
                    self._api._print(f"通知 {self._sm_cfg['UserId']}: 用户名或密码错误", level="ERROR")

    def _sync_err_logger(self, pipe):
        while True:
            line = pipe.readline()
            if not line:
                return
            # logging and _print is thread safe
            self._process_log(line.decode("utf-8"))

    async def _async_err_logger(self, reader):
        while not reader.at_eof():
            line = await reader.readline()
            self._process_log(line.decode("utf-8"))

    async def __aenter__(self):
        # Windows系统下不支持 connect_read_pipe 和 subprocess_exec
        if sys.platform.startswith("win"):
            self._sm_proc = subprocess.Popen([self._sm_exe, "-t", "dec"], stdin=PIPE, stdout=PIPE, stderr=PIPE, env=self._sm_env)
            self._logger_task = self._api._loop.run_in_executor(None, self._sync_err_logger, self._sm_proc.stderr)
            decrypt_coro = self._api._loop.run_in_executor(None, lambda: self._sm_proc.stdout.read())
            self._sm_proc.stdin.write(self._sm_data.encode("utf-8"))
            self._sm_proc.stdin.close()
            decrypt_out = await decrypt_coro
        else:
            rfd, wfd = os.pipe()
            # os.fdopen 返回的对象可以重复关闭, 而由于 fd 复用因此 os.pipe 返回的 fd 不能重复调用 os.close
            self._rf, self._wf = os.fdopen(rfd), os.fdopen(wfd)
            reader = asyncio.StreamReader()
            # 需要将 transport 保存下来, 在退出的时候关闭, 使得 _async_err_logger 退出
            self._rt, _ = await self._api._loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), self._rf)
            self._logger_task = self._api.create_task(self._async_err_logger(reader))
            self._sm_proc = await asyncio.create_subprocess_exec(self._sm_exe, "-t", "dec", stdin=PIPE, stdout=PIPE, stderr=self._wf, env=self._sm_env)
            decrypt_out, _ = await self._sm_proc.communicate(input=self._sm_data.encode("utf-8"))
        # ref:https://peps.python.org/pep-0448/
        # The keys in a dictionary remain in a right-to-left priority order, so {**{'a': 1}, 'a': 2, **{'a': 3}} evaluates to {'a': 3}.
        self._sm_cfg = {**json.loads(decrypt_out), **self._sm_cfg}
        return self

    async def get_addr(self):
        """无法启动时返回空字符串"""
        if sys.platform.startswith("win"):
            # subprocess.Popen 需要调用 poll 才会更新 returncode
            self._sm_proc.poll()
        # 初始由于执行了 -t dec 因此 returncode 不会为 None
        if self._sm_proc.returncode is not None:
            if sys.platform.startswith("win"):
                await self._logger_task
                self._sm_proc = subprocess.Popen([self._sm_exe, "-a", "localhost:0", "-t", self._sm_type], stdin=PIPE, stdout=PIPE, stderr=PIPE, env=self._sm_env)
                self._logger_task = self._api._loop.run_in_executor(None, self._sync_err_logger, self._sm_proc.stderr)
                addr_coro = self._api._loop.run_in_executor(None, lambda: self._sm_proc.stdout.readline())
                self._sm_proc.stdin.write(json.dumps(self._sm_init).encode("utf-8"))
                self._sm_proc.stdin.write(json.dumps(self._sm_cfg).encode("utf-8"))
                self._sm_proc.stdin.flush()
                self._sm_addr = (await addr_coro).decode("utf-8").strip()
            else:
                self._sm_proc = await asyncio.create_subprocess_exec(self._sm_exe, "-a", "localhost:0", "-t", self._sm_type, stdin=PIPE, stdout=PIPE, stderr=self._wf, env=self._sm_env)
                # 调用 write 但是不调用 drain, 避免死锁, 因为下面会 readline
                self._sm_proc.stdin.write(json.dumps(self._sm_init).encode("utf-8"))
                self._sm_proc.stdin.write(json.dumps(self._sm_cfg).encode("utf-8"))
                self._sm_addr = (await self._sm_proc.stdout.readline()).decode("utf-8").strip()
        return self._sm_addr

    async def __aexit__(self, exc_type, exc, tb):
        try:
            self._sm_proc.terminate()
        except ProcessLookupError:
            pass
        if sys.platform.startswith("win"):
            self._sm_proc.wait()
        else:
            await self._sm_proc.wait()
            # 会导致 _async_err_logger 遇到 eof
            self._rt.close()
            self._rf.close()
            self._wf.close()
        await self._logger_task


class NullContext(object):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
