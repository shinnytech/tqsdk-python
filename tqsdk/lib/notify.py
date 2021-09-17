#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'


from tqsdk.api import TqApi
from tqsdk.diff import _get_obj


class TqNotify(object):
    """
    用于在同步代码中接受服务器通知
    """

    def __init__(self, api: TqApi) -> None:
        """
        创建 TqNotify 实例

        Args:
            api (tqsdk.api.TqApi): TqApi 实例

        Example::

            from tqsdk import TqApi, TqAuth, TqKq, TqNotify

            api = TqApi(account=TqKq(), auth=TqAuth("信易账户", "账户密码"))
            tqNotify = TqNotify(api)  # 构造实例类
            while True:
                api.wait_update()
                # 每次调用返回距离上一次调用 tqNotify.get_notifies() 之后产生的通知列表，没有的话返回 []
                notify_list = tqNotify.get_notifies()
                for notify in notify_list:
                    print(notify)  # 打印出通知内容
                    # send_message(notify['content'])  可以发送通知到其他工具

        """
        self._api = api
        self._notify = _get_obj(self._api._data, ["notify"])
        # 用户未读取过的通知，用 list 类型尽量保证用户读到通知的顺序和进程收到的顺序一致，但是不能完全保证
        self._unread_notifies_list = [k for k in self._notify if not k.startswith("_")]
        # 已经添加到 _unread_notifies 的通知
        self._processed_notifies_set = {k for k in self._notify if not k.startswith("_")}
        self._task = self._api.create_task(self._run())

    async def _run(self):
        async with self._api.register_update_notify(self._notify) as update_chan:
            async for _ in update_chan:
                all_notifies = {k for k in self._notify if not k.startswith("_")}
                notifies = all_notifies - self._processed_notifies_set  # 最近更新的通知
                self._processed_notifies_set = all_notifies
                self._unread_notifies_list.extend([k for k in notifies])

    def get_notifies(self):
        notifies = [self._notify[n] for n in self._unread_notifies_list]
        self._unread_notifies_list = []
        return notifies
