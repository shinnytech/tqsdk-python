.. _tqsdk.channel:

tqsdk.TqChan - 协程通信通道
------------------------------------------------------------------

.. py:class:: tqsdk.TqChan
    :canonical: tqsdk.channel.TqChan

    用于协程间传递数据的通道。:py:meth:`~tqsdk.TqApi.register_update_notify` 返回此类型，
    可通过 ``async with`` 和 ``async for`` 接收更新通知。
    更新通知的完整用法见 :py:meth:`~tqsdk.TqApi.register_update_notify`，协程示例见 :ref:`multi_async_task`。

.. automethod:: tqsdk.TqChan.send

.. automethod:: tqsdk.TqChan.send_nowait

.. automethod:: tqsdk.TqChan.recv

.. automethod:: tqsdk.TqChan.recv_nowait

.. automethod:: tqsdk.TqChan.recv_latest

.. automethod:: tqsdk.TqChan.close
