# Tqsdk 接入新版合约服务开发设计

## 目标效果

1. tqsdk 完全替换旧版合约服务
    注意：复盘服务器还是使用旧版的合约服务和行情服务，需要兼容复盘的情况

2. 用户使用体验不降级, 兼容支持之前官网提供的以下功能

```
目前可以使用以下代码来获取所有合约代码列表
ls = [k for k,v in api._data["quotes"].items()]

如果只要当前交易中的合约, 可以这样
ls = [k for k,v in api._data["quotes"].items() if v["expired"] == False]

如果要全部主连合约:
ls = [k for k,v in api._data["quotes"].items() if k.startswith("KQ.m")]

如果要全部主连合约对应的实际合约:
ls = [v["underlying_symbol"] for k,v in api._data["quotes"].items() if k.startswith("KQ.m")]
```

## 修改方案 - 版本2

* `tqsdk` 发送的 `ins_query` 包有两种情况：

1. 用户请求符合某种条件的合约列表，不知道会返回什么数据
    - 发送的 query_id 以 `PYSDK_api` 开始
2. 由 tqsdk 发出的请求某个指定合约的合约信息
    - 发送的 query_id 为 `"PYSDK_quote_" + url_base64_encode(symbol)`
        
### TqApi

* 在 setup_connection 里修改，初始化行情链接之后，新增 _md_handler_task 处理 ws_md_recv_chan
```python
    # 在复盘情况下，还需要初始化合约服务信息
    if isinstance(self._backtest, TqReplay):
        
    self.create_task(self._connect(self._md_url, ws_md_send_chan, ws_md_recv_chan))  # 启动行情websocket连接
    md_recv_handler_chan = TqChan(self)
    self.create_task(self._md_handler(ws_md_recv_chan, md_recv_handler_chan))
    ws_md_recv_chan = md_recv_handler_chan
```
```python
    # 将收到的 以 `PYSDK_quote` 开始的 query 请求的结果拼成 quotes，追加在 data 中发下去
    async def _md_handler(self, origin_recv_chan, recv_chan):
        async for pack in origin_recv_chan:
            if pack["aid"] == "rtn_data":
                # 过滤 symbols
                quotes = {}
                for d in pack["data"]:
                    if d.get("symbols", None) is None:
                        continue
                    for q_id, query_result in d.get("symbols").items():
                        if query_result.get("error", ""):
                            raise Exception(f"查询合约服务报错 {query_result}")
                        if q_id.startswith("PYSDK_quote"):
                            quotes.update(_symbols_to_quotes(query_result))
                pack["data"].append({"quotes": quotes})
            await recv_chan.send(pack)
```

* 新增加几个接口提供给用户使用，能够完成 https://shinnytech.atlassian.net/browse/BE-247 https://shinnytech.atlassian.net/browse/BE-248

```python
    # graphgl 这个方案里 query_graphql 也只给用户使用，tqsdk 代码不会用到这个函数
    def query_graphql(self, query: str, variables: str, query_id: Optional[str] = None):
        if isinstance(self._backtest, TqReplay):
            raise Exception("复盘服务器不支持当前接口")
        pack = {
            "query": query,
            "variables": variables
        }
        symbols = _get_obj(self._data, ["symbols"])
        for symbol_query in symbols.values():
            if symbol_query.items() >= pack.items():
                return symbol_query
    
        query_id = query_id if query_id else _generate_uuid("PYSDK_api")
        self._send_pack({
            "aid": "ins_query",
            "query_id": query_id
        }.update(pack))
        symbol_query = _get_obj(self._data, ["symbols", query_id])
        deadline = time.time() + 30
        if not self._loop.is_running():
            while symbol_query.items() >= pack.items():
                if not self.wait_update(deadline=deadline):
                    raise Exception("查询合约服务 %s 超时，请检查客户端及网络是否正常" % (query))
        return symbol_query
    
    # 以下三个接口，先拼出来请求的 query 和 variables，然后调用 query_graphql。
    # 只能在同步代码中使用，不能在协程中使用。如果要支持协程，需要再增加接口。
    
    # 全部 期货 期权 指数 主力连续 组合
    def query_quotes(ins_class: str = None, exchange_id: str = None, product_id: str = None, expired: bool = None, has_night: bool = None):
        if self._loop.is_running():
            raise Exception("协程不支持当前接口调用")
        pass
    # 主连对应的标的合约
    def query_cont_quotes(exchange_id: str = None, product_id: str = None) => if api._loop.is_running() None else list[str]:
    # 查询符合条件的期权
    def query_options(underlying_symbol:str=None, option_class=None, option_month=None, strike_price=None, has_A=None) => if api._loop.is_running() None else list[str]:
```

* 去掉之前临时添加的  _stock 参数

* 不会再下载合约文件作为第一个数据包

* 在用户使用 `api._data` 的时候，显示错误，并提供给用户推荐用法。加在 api._data.quotes. `__iter__()` 方法上提示用户。
    为了同时支持用户原来的用法，在 tqsdk 初始化的时候，先请求到全部合约代码（期货、期权、期货指数、期货主连和旧版合约代码相同），以及他们的完整字段，作为第一个初始的行情包发到 `md_recv_chan`。
    （会在 2.0.0 版本取消这种做法，并且不再支持原来给用户提供的用法）具体做法是：
    
```python
    # 在 api 初始化完成之后，发送一个请求全行情的 query
    def __init__(self):
        # ......
        # ......
        # todo: 兼容旧版 sdk 所做的修改
        if not isinstance(self._backtest, TqReplay):
            q, v = _query_for_class(["future", "index", "combine", "cont"])
            self.query_graphql(q, v, _generate_uuid("PYSDK_quote"))
```

* 检查合约是否存在，不能发送不存在的合约给服务器，get_quote get_tick_seriel get_kline_seriel get_position insert_order
    - 在同步代码中，先请求合约信息，再订阅合约、请求kline
    - 在协程中，使用 create_task, 保证发送请求的顺序依然是先请求合约信息，再订阅合约、请求kline

```python
    """
    以 get_quote 为例的处理流程，一共有八种情况：
    1. md--ioloop--symbol_in_quotes
    2. md--ioloop--symbol_not_in_quotes
    3. md--sync--symbol_in_quotes
    4. md--sync--symbol_not_in_quotes
    5. tqreplay--ioloop--symbol_in_quotes
    6. tqreplay--ioloop--symbol_not_in_quotes
    7. tqreplay--sync--symbol_in_quotes
    8. tqreplay--sync--symbol_not_in_quotes
    """

    def get_quote(symbol):
        if isinstance(self._backtest, TqReplay) and symbol not in self._data.get("quotes", {}):
            # 6. tqreplay--ioloop--symbol_not_in_quotes
            # 8. tqreplay--sync--symbol_not_in_quotes
            raise Exception("合约不存在")
        elif self._loop.is_running() and symbol not in self._data.get("quotes", {}):
            # 2. md--ioloop--symbol_not_in_quotes
            self.create_task(self._get_quote_async(symbol))  # 协程中需要等待合约信息，然后发送订阅请求
            return _get_obj(self._data, ["quotes", symbol], self._prototype["quotes"]["#"])
        else:
            # 1. md--ioloop--symbol_in_quotes
            # 3. md--sync--symbol_in_quotes
            # 4. md--sync--symbol_not_in_quotes
            # 5. tqreplay--ioloop--symbol_in_quotes
            # 7. tqreplay--sync--symbol_in_quotes
            self._ensure_symbol(symbol)  # 对于 1.3.5.7. 都是直接返回，对于 4. 会先请求合约信息
            quote = _get_obj(self._data, ["quotes", symbol], self._prototype["quotes"]["#"])
            if symbol not in self._requests["quotes"]:
                self._requests["quotes"].add(symbol)
                self._send_pack({
                    "aid": "subscribe_quote",
                    "ins_list": ",".join(self._requests["quotes"]),
                })
                deadline = time.time() + 30
                while not self._loop.is_running() and quote["datetime"] == "":
                    if not self.wait_update(deadline=deadline):
                        raise Exception(f"获取 {symbol} 的行情信息超时，请检查客户端及网络是否正常，且合约代码填写正确")
            return quote

    def _ensure_symbol(self, symbol):
        # 已经收到收到合约信息之后返回，同步
        if symbol not in self._data.get("quotes", {}):
            query_pack = _query_for_quote(symbol)
            self._send_pack(query_pack)
            deadline = time.time() + 30
            while query_pack["query_id"] not in self._data.get("symbols", {}):
                if not self.wait_update(deadline=deadline):
                    raise Exception(f"获取 {symbol} 的合约信息超时，请检查客户端及网络是否正常，且合约代码填写正确")

    async def _ensure_symbol_async(self, symbol):
        # 已经收到收到合约信息之后返回，异步
        if symbol not in self._data.get("quotes", {}):
            query_pack = _query_for_quote(symbol)
            self._send_pack(query_pack)
            async with self.register_update_notify() as update_chan:
                async for _ in update_chan:
                    if query_pack["query_id"] in self._data.get("symbols", {}):
                        break

    async def _get_quote_async(self, symbol):
        # 协程中, 在收到合约信息之后再发送订阅行情请求，来保证，不会发送订阅请求去订阅不存在的合约
        await self._ensure_symbol_async(symbol)
        if symbol not in self._requests["quotes"]:
            self._requests["quotes"].add(symbol)
            self._send_pack({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self._requests["quotes"]),
            })
```

```python
    """
    以 get_kline_serial 为例的处理流程，一共有八种情况：
    1. md--ioloop--symbol_in_quotes
    2. md--ioloop--symbol_not_in_quotes
    3. md--sync--symbol_in_quotes
    4. md--sync--symbol_not_in_quotes
    5. tqreplay--ioloop--symbol_in_quotes
    6. tqreplay--ioloop--symbol_not_in_quotes
    7. tqreplay--sync--symbol_in_quotes
    8. tqreplay--sync--symbol_not_in_quotes
    """

    def get_quote(symbol):
        # ... 检查参数
        
        if isinstance(self._backtest, TqReplay):
            # 5. tqreplay--ioloop--symbol_in_quotes
            # 7. tqreplay--sync--symbol_in_quotes
            for s in symbol:
                if s not in self._data.get("quotes", {}):
                    # 6. tqreplay--ioloop--symbol_not_in_quotes
                    # 8. tqreplay--sync--symbol_not_in_quotes
                    raise Exception(f"代码 {s} 不存在, 请检查合约代码是否填写正确")
        if self._loop.is_running() and not isinstance(self._backtest, TqReplay):
            # 1. md--ioloop--symbol_in_quotes
            # 2. md--ioloop--symbol_not_in_quotes
            self.create_task(self._get_kline_serial_async(symbol, chart_id, serial, pack.copy()))
        else:
            # 3. md--sync--symbol_in_quotes
            # 4. md--sync--symbol_not_in_quotes
            # 5. tqreplay--ioloop--symbol_in_quotes
            # 7. tqreplay--sync--symbol_in_quotes
            for s in symbol:
                self._ensure_symbol(s)
            if serial is None or chart_id is not None:  # 判断用户是否指定了 chart_id（参数）, 如果指定了，则一定会发送新的请求。
                self._send_pack(pack.copy())  
```

### TqAccount

不需要合约信息，行情只需要正确转发 `aid = "ins_query"` 的请求包。 


### TqSim

1. tqsim 会原样转发行情相关的请求包到 md，也会转发 ins_query, 不需要修改
2.  `ensure_quote` 只需修改为等待合约的 datetime 和 price_tick 字段都收到有效值，原因：
    + 对于 ensure_quote 来说，ensure_quote 只出现在 quote_handler_task 的第一步等待确认收到合约行情，
    + tqsim 只有在收到 insert_order 请求才会新建一个 quote_handler_task
    + api 在发送 `aid="insert_order"` 一定会请求合约信息，
    + 所以在执行到 `ensure_quote` 函数时，一定发送过请求合约信息的包，只需要等待 datetime 和 price_tick 都收到有效值即可


### TqBacktest

1. 需要正确转发 `aid = "ins_query"` 的请求包，并且等待收到回复 `query_id in self._data["symbols"]` 再继续执行
2. 在 ensure_quote 先检查 quote 的 price_tick 字段，如果没有
    - 发送 `query_id = PYSDK_quote_xxxxx` 的 query 包
    - 增加 `register_update_notify()` 等到收到 `query_id in self._data["symbols"]` 再继续执行，这里的主要是为了保证不发不存在的合约给行情服务器。
3. 在 md_recv_chan 中收到 aid="rtn_data", 要处理 symbols 和 quotes 数据，有 symbols 和 quotes 的数据包需要转发给下游
4. 不再发送合约信息截面，而是初始时放一个数据包在 diff 中，用于发送 `mdhis_more_data = false`, 原因：
    - sim 模块在收到 `mdhis_more_data = false` 数据包才会发送初始账户信息给客户端。
    - api 会在一开始就发送 peek_message，这时候 backtest 中的这第一个数据包就会消耗掉这个 peek_message，否则 backtest 没有任何等待发送的数据，就会认为回测结束。


### 其他需要注意的地方

* 全文搜索 ins_class ，所有用到的地方，旧版合约服务的 class 和新版合约服务 class 注意不同的点
    - FUTURE -> future
    - FUTURE_INDEX -> index
    - FUTURE_CONT -> cont
    - FUTURE_COMBINE  -> cont
    - FUTURE_OPTION -> option
    - INDEX (CSI.000300) -> index
    - OPTION (CFFEX.IO2003-C-3850) -> option
    
* 字段名称不一样的地方
    - option_class -> call_or_put
    - underlying_symbol -> underlying 需要调整

* 请求期权合约的合约信息，同时会请求标的的合约信息，utils 处理时需要展开标的数据

* 所有的测试用例都需要重新生成脚本


### utils

1. 需要函数生成 query 模板


## 单元测试

原来的测试用例脚本，全部都需要重新生成

增加测试用例：

* 测试新添加的几个接口


相关文档：
+ [合约服务文档](https://shinnytech.atlassian.net/wiki/spaces/EFS/pages/29786314/GraphQL+Api)
