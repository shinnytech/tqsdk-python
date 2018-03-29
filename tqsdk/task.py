# encoding: UTF-8

"""
Task 单线程多任务框架
========================================

多任务问题
----------------------------------------
对于用户而言, 一个任务中通常包含了若干操作和等待, 以一个简单的套利下单需求为例:

+ 发出一个买入开仓报单指令和一个卖出开仓报单指令
+ 等待两个报单完全成交, 在此过程中, 如果发现市场价格有变, 则:
  - 撤销已经发出的委托单
  - 撤销完成后, 重新按照剩余手数和价格发出报单
+ 重复第二步直至完成

在这个例子中, 等待发出的开仓指令成交, 和等待价格变动, 都需要等待一段较长的时间, 在这段时间内, 我们可能还有别的代码需要运行, 因此需要某种多任务机制, 来使多个任务同时执行. 常见的多任务方案有三种


异步回调+状态机模型
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CTP API 使用的即是此方式. 每当一个事件发生时, 触发特定的回调函数. 用户在回调函数中编写自己的业务代码对事件进行响应.

Pros:

* 语法简单, 绝大多数编程语言都直接支持此类模型, 性能较高

Cons:

* 用户的业务代码被分成两个(或更多)部分, 一部分代码在主线程中执行, 另一部分代码放在回调函数中, 代码结构与需求结构不一致, 导致编码困难
* 当业务逻辑较复杂时, 需要用户自行构建状态机和管理状态变量
* 主线程和回调函数线程中的代码如果常常需要访问共同变量, 因此需用户实现转线程或线程锁机制


多线程阻塞模型
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
每个任务建立一个线程, 在线程中可以方便的执行阻塞和等待.

Pros:

* 代码结构与需求结构较为接近, 编码较简单
* 所有业务代码可以组织到一个函数中, 避免状态机和全局变量

Cons:

* 多线程都对共同数据集执行读写操作, 需要小心的使用锁机制
* 线程开销较大, 创建大量线程后性能明显下降


基于generator机制的单线程多任务模型
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
为了克服上面两种机制的困难, 现代编程语言中通常都支持某种形式的 单线程多任务 机制, 例如 golang 中的 coroutines, javascript 和 python 中的 generator 等.

Pros:

* 代码结构与线程函数相似, 所有业务代码可以组织到一个函数中, 避免状态机和全局变量
* 代码中明确插入等待事件的代码, 任务管理器只会在这个位置执行任务切换
* 多任务访问共同变量无需加锁
* 没有线程开销

Cons:

* 较老的编程语言对此机制缺乏支持

我们推荐使用这种模型, 并在 TqSdk 中对这种方式给予了专门支持


任务概念
----------------------------------------
我们将一个任务称为一个 Task. 在实现上, 每个 Task 是一个 `Python Generator <https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/Generator>`_.

.. code-block:: python
    :caption: 一个Task的例子 (tqsdk.tools.make_order_until_all_matched)

    # 订阅指定合约的行情, 以便跟随市场价下单
    quote = api.get_quote(symbol)
    volume_left = volume
    while volume_left > 0:
        limit_price = quote["bid_price1"] if direction == "SELL" else quote["ask_price1"]
        # 发出报单
        order = api.insert_order(symbol=symbol, direction=direction, offset=offset, volume=volume_left, limit_price=limit_price)
        # 等待委托单完全成交, 或者行情有变
        wait_result = yield{
            "ORDER_FINISH": lambda: order["status"] == "FINISHED",
            "PRICE_CHANGED": lambda: limit_price != (quote["bid_price1"] if direction == "SELL" else quote["ask_price1"])
        }
        # 如果委托单状态为已完成
        if wait_result["ORDER_FINISHED"]:
            if order["exchange_order_id"] == "":
                # 没有交易所单号, 判定为错单
                raise Exception("error order")
            else:
                return
        # 如果价格有变
        if wait_result["PRICE_CHANGED"]:
            # 发出撤单指令
            api.cancel_order(order)
        # 等待撤单指令生效, 或者委托单全部成交
        yield {
            "ORDER_CANCELED": lambda: order["status"] == 'FINISHED'
        }
        # 这时委托单已经FINISHED, 拿到未成交手数作为下轮追单使用
        volume_left = order["volume_left"]


在一个任务函数中, 我们在需要阻塞等待的地方插入 yield 语句, 例如::

    wait_result = yield{
        "ORDER_FINISH": lambda: order["status"] == "FINISHED",
        "PRICE_CHANGED": lambda: limit_price != (quote["bid_price1"] if direction == "SELL" else quote["ask_price1"])
    }


代码运行到 yield 这行时, 便将控制权交回给任务管理器(TaskManager), 本函数自身被"挂起", 不再执行后面的代码.

yield 后跟一个dict, 其中的每个item都是一个function, 用来表示一个唤醒本任务的条件.
TaskManager在收到新数据包或定时器触发时, 检查所有挂起 task 的唤醒条件是否满足.
如果发现某个task的至少一个唤醒条件满足(function 返回 True), 就会将控制权交回给任务, 继续执行后续代码, 直到遇到下一个 yield 或 return 为止
任务函数可以通过yield的返回值得知哪些条件已满足.


超时处理
----------------------------------------
TaskManager支持在每个阻塞等待的位置加入超时设置, 如下例:

    # 下单
    order = api.insert_order(symbol="SHFE.cu1801", ...)
    # 如果10秒内没有完全成交则撤单
    wait_result = yield {
        "TIMEOUT": 10,    # 设置10秒超时
        "ORDER_FINISHED": lambda: order["status"] == "FINISHED"     # 如果委托单已经完全成交也OK
    }
    # 代码运行到这里, 就表示上面两个条件至少有一个满足了
    if wait_result["TIMEOUT"]:
        api.cancel_order(order)

在每个 yield 中可以用 "TIMEOUT" 设置超时, 单位为秒. 可以使用浮点数.


异常处理
----------------------------------------
task函数中遇到异常时, 可以抛出 Exception. 任何task抛出Exception后, 都会停止执行. 可以通过 TaskManager.get_error 获得异常信息

"""

import uuid
import time
import logging
import traceback


class TaskManager:
    """
    协程任务管理调度器.

    通常情况下, 一个进程中有一个TaskManager的实例, 它负责维护所有运行中的协程, 并根据条件调度运行
    """
    def __init__(self):
        self.tasks = {}
        self.error_tasks = {}

    def start_task(self, task_generator):
        """
        启动一个任务

        Args:
            task_generator (generator): 一个python generator (即带yield的函数)

        Returns:
            str: 返回一个 task_id (全局唯一字符串), 用于唯一标示此任务
        """
        task_id = uuid.uuid4().hex
        try:
            self.tasks[task_id] = [task_generator, None]
            self._set_task_condition(task_id, task_generator.send(None))
        except Exception as e:
            logging.log(logging.WARNING, "exception when start_task: " + str(e) + traceback.format_exc())
            self.error_tasks[task_id] = e
        return task_id

    def stop_task(self, task_id):
        """
        停止一个任务

        Args:
           task_id (str): 用于标示任务的任务ID, 即 start_task 的返回值
        """
        if task_id not in self.tasks:
            return
        self.tasks[task_id][0].close()
        del self.tasks[task_id]

    def is_active(self, task_id):
        """
        判定一个任务是否在 active 状态 (此任务以后还可能得到运行机会)

        Args:
           task_id (str): 用于标示任务的任务ID, 即 start_task 的返回值

        Returns:
           bool: 如果任务还在active状态, 返回 True, 否则返回 False
        """
        return task_id in self.tasks

    def is_finish(self, task_id):
        """
        判定一个任务是否已正常结束

        Args:
           task_id (str): 用于标示任务的任务ID, 即 start_task 的返回值

        Returns:
           bool: 如果任务已正常完成, 返回 True, 否则返回 False
        """
        return not task_id in self.tasks and not task_id in self.error_tasks

    def get_error(self, task_id):
        """
        获取任务运行中抛出的错误信息

        Args:
           task_id (str): 用于标示任务的任务ID, 即 start_task 的返回值

        Returns:
           Exception: 如果任务没有抛出任何 Exception, 返回 None, 否则返回任务代码抛出的 Exception
        """
        return self.error_tasks.get(task_id, None)

    def trigger(self):
        """
        指令任务管理器检查所有任务等待条件, 尝试运行任务

        通常将此函数作为 data_update_hook 传给 TqApi.run(), 以便在api接口收到数据后调度各task
        """
        finished_task = set()
        for task_id in list(self.tasks.keys()):
            need_trigger = False
            wait_result = {}
            for cond_name, cond_expr in self.tasks[task_id][1].items():
                if cond_name == "TIMEOUT":
                    v = time.time() > cond_expr
                else:
                    v = cond_expr()
                wait_result[cond_name] = v
                if v:
                    need_trigger = True
            if need_trigger:
                try:
                    wait_condition = self.tasks[task_id][0].send(wait_result)
                    self._set_task_condition(task_id, wait_condition)
                except StopIteration:
                    finished_task.add(task_id)
                except Exception as e:
                    logging.log(logging.WARNING, "exception when run_task: " + str(e) + traceback.format_exc())
                    self.error_tasks[task_id] = e
        for task_id in finished_task:
            self.tasks.pop(task_id)

    def _set_task_condition(self, task_id, wait_condition):
        time_out = wait_condition.get("TIMEOUT", 0)
        if time_out:
            wait_condition["TIMEOUT"] = time.time() + time_out
        self.tasks[task_id][1] = wait_condition
