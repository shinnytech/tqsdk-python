# Tqsdk 接入新版合约服务开发设计

## 目标效果

1. tqsdk 完全替换旧版合约服务

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

## 各模块修改方案

### TqApi

不需要合约信息

1. 需要能够处理 `aid = "ins_query"` 的请求包
2. 在 get_quote 中，先检查 quote 是否有请求合约的合约服务中的字段，如果没有的话发送 query 请求合约的全部字段, id 为 PYSDK_api_quote_xxxxx，等待到 quote 收到合约服务中的某个字段才返回。
3. recv_chan 中的数据包，需要过滤出 PYSDK_api_quote_xxxxx 的数据包，merge_diff 到 api._data.quotes。
4. 不会再下载合约文件作为第一个数据包。
5. 在用户使用 `api._data` 的时候，显示错误，并提供给用户推荐用法。加在 api._data.quotes. `__iter__()` 方法上提示用户。
    为了同时支持用户原来的用法，在 tqsdk 初始化的时候，先请求到全部合约代码（期货、期权、期货指数、期货主连和旧版合约代码相同），以及他们的完整字段，作为第一个初始的行情包发到 `md_recv_chan`。
    （会在 2.0.0 版本取消这种做法，并且不再支持原来给用户提供的用法）
6. 新增加几个接口提供给用户使用，能够完成 https://shinnytech.atlassian.net/browse/BE-247 https://shinnytech.atlassian.net/browse/BE-248
7. tqsdk 初始化的时候，先请求发送 query (id=PYSDK_api_all_quotes) 请求到全部合约代码，用于判断合约是否存在, 只记在 api 中备用，不会更新到 _data
 
```
# graphgl
def query_graphql(query_id: Option[str], query: str, variables: dict) => None (if api._loop.is_running())
                                                => dict (else) # { "query": 用户请求的query, "variables": 用户请求的参数, "result": 查询返回结果, "error": 可能的错误}:
    for symbol_query in api._data["symbols"]:
        if symbol_query["query"] == query and symbol_query["variables"] == variables:
            return symbol_query
    self.send_chan({
        "aid": "ins_query",
        "query_id": query_id if query_id else gen_uuid("PYSDK_api"),
        "query": query,
        "variables": variables
    })
    symbol_query = None
    deadline = time.time() + 30
    while not self._loop.is_running():
        for symbol_query in api._data["symbols"]:
            if symbol_query["query"] == query and symbol_query["variables"] == variables:
                return symbol_query
        if not self.wait_update(deadline=deadline):
            raise Exception("查询合约服务 %s 超时，请检查客户端及网络是否正常" % (symbol))
    return symbol_query

以下三个接口，先拼出来请求的 query 和 variables，然后调用 query_graphql。

# 全部 期货 期权 指数 主力连续 组合
def query_quotes(ins_class: str = None, exchange_id: str = None, product_id: str = None, expired: bool = None, has_night: bool = None) => if api._loop.is_running() None else list[str]:
# 主连对应的标的合约
def query_cont_quotes(exchange_id: str = None, product_id: str = None) => if api._loop.is_running() None else list[str]:
# 查询符合条件的期权
def query_options(underlying_symbol:str=None, option_class=None, option_month=None, strike_price=None, has_A=None) => if api._loop.is_running() None else list[str]:

```


## objs

quote 对象需要增加字段，underlying, 为其标的对象，默认值 None。

期权和主连，需要手动添加 `underlying_symbol` 字段，因为新版合约服务只有 `underlying` 字段。

### TqAccount

不需要合约信息，行情只需要正确转发 `aid = "ins_query"` 的请求包。 


### TqSim

需要合约信息
commisson margin trading_time ins_class price_tick option_class strike_price volume_multiple underling_symbol

1. 需要正确转发 `aid = "ins_query"` 的请求包。
2. tqsim 管理自己发送的 graphql
3. ensure_quote 需要先检查 quote 的 datetime，price_tick 等等字段，如果没有
    - 发送 id 是 PYSDK_sim_SHFE.au2001 的形式，query 请求为包括以上字段的请求的包
    - _register_update_chan(quote, quote_chan)，直到收到全部需要的数据才会继续执行后续的代码
4. 在 md_recv_chan 中收到 aid="rtn_data", symhols[PYSDK_sim_SHFE.au2001] 数据，收到之后，merge_diff 到 tqsim._data。
    - 这样对应 quote_handler 中的 quote_chan 就会收到对应的更新通知，并更新相应数据。

### TqBacktest

需要合约信息
price_tick

1. 需要正确转发 `aid = "ins_query"` 的请求包。
2. tqbacktest 管理自己发送的 graphql
3. 为每个合约在初始化 generator 的时候，请求一次合约信息，在 ensure_quote 先检查 quote 的 price_tick 字段，如果没有
    - 发送 id 是 PYSDK_backtest_SHFE.au2001 的形式，query 请求为包括以上字段的请求的包
    - 增加 `register_update_notify(quote)` 等到收到 quote["price_tick"] 再继续执行
4. 在 md_recv_chan 中收到 aid="rtn_data", 要单数处理 symhols 数据，id 为 PYSDK_backtest_SHFE.au2001 的需要 merge_diff 到 tqsim._data。


## utils

1. 需要函数生成 query 模板



相关文档：
+ [合约服务文档](https://shinnytech.atlassian.net/wiki/spaces/EFS/pages/29786314/GraphQL+Api)
