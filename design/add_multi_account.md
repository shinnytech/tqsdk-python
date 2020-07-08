# 单 TqApi 实例支持多账户

需求文档：https://shinnytech.atlassian.net/wiki/spaces/BACK/pages/154567536/tqsdk+api?focusedCommentId=158597233

单 `TqApi` 实例多账户支持是通过串行处理账户实例消息包的方式实现的，每个账户实例只处理当前账户的数据包；
否则，传递给下一个账户实例，直至发送至交易网关或行情网关。

## 数据流说明

调整后数据流结构如下图所示。

```buildoutcfg
        +-----------------+
        |                 |
        |                 |
        |       OMD       |
        |                 |
        +----+-------+----+
             ^       |
      md_send|       |md_recv
             |       v
        +----+-------+----+
        |                 |
        |                 |
        |      TqSim      |
        |                 |
        +----+-------+----+
             ^       |
api_send_chan|       |api_recv_chan
             |       v
        +----+-------+----+   td_send       +------------------+
        |                 +---------------->+                  |
        |                 |                 |                  |
        |     TqAccount   |                 |       OTG        |
        |                 +-----------------+                  |
        +----+-------+----+   td_recv       +------------------+
             ^       |
api_send_chan|       |api_recv_chan
             |       v
        +----+-------+----+   td_send       +------------------+
        |                 +---------------->+                  |
        |                 |                 |                  |
        |      TqKq       |                 |       OTG        |
        |                 +-----------------+                  |
        +----+-------+----+   td_recv       +------------------+
             ^       |
api_send_chan|       |api_recv_chan
             |       v
        +----+-------+----+
        |                 |
        |                 |
        |     TqApi       |
        |                 |
        +-----------------+


```
上行处理流程简要说明如下

1. 用户调用 `TqApi` 模块接口完成数据包的发送，如下单和撤单指令
2. 账户模块 `TqAccount/TqKq/TqSim` 从 `api_send_chan` 中取出数据包，根据 包类型 和 所属账户 进行处理：
若为行情包或非当前账户实例的交易指令包，直接将数据包放至下一个 `api_send_chan` 中供下一个账户实例进行处理；
否则，当数据包为当前账户实例的交易指令包时，将数据包通过 `td_send` 发送至交易服务器
3. 行情包经过多层传递发送至行情服务器

数据包下行处理流程为

1. Websocket client 从网络中接收行情网关发送的数据包，并将其放入 `md_recv`
2. 账户实例将 `md_recv` 中取出数据包，将数据包合并后放入 `api_recv_chan`
3. `TqApi` 从 `api_recv_chan` 中取出数据包，供各接口加工使用


## 业务信息截面结构调整

现有系统中单账户 `api` 实例，采用的是用户名 `account_id` 作为主键进行唯一标识。下面是交易的业务信息截面。
```buildoutcfg
{
  "trade": {
    "022000": {                             //账户唯一标识 account_key = user_id
      "user_id": "022000",                  //登录用户名
      "trading_day": "20200604",            //交易日
      "accounts": { ... },                  //资金账户
      "positions": { ... },                 //持仓
      "orders":  { ... },                   //委托
      "trades": { ... },                    //成交
      "banks": { ... },                     //签约银行
      "transfers": { ... }                  //银期流水
    }
  },
  "quotes":{},
  ...
}
```
为了在交易业务信息截面中兼容多账户，对账户主键 `acccount_key` 进行调整：实盘账户、模拟账户和快期账户
全部使用 `id(object)` 作为唯一标识 `account_key`，同时，该值也作为模拟账户的 `user_id` 使用。
 下面是调整后 2 个实盘账户、2 个模拟账户 和 1 个快期账户的业务截面示例。

```
{
  "trade": {
    "67629600": {                                                // 实盘账户 TqAccount1
      "user_id": "022000",                                       // 登录用户名为 资金账号
      ...
    },
    "67629601": { "user_id": "022001", ... },                    // 实盘账户 TqAccount2
    "67629602": {                                                // 模拟账户1
      "user_id": "67629602",                                     // 登录用户同 account_key
       ...
    },
    "67629603": {                                                // 模拟账户指定account_id时，使用 account_id
      "user_id": account_id,                                     // 登录用户名使用用户输入用户名
      ...
    }, 
    "67629604": {                                                // 快期账户 account_key = shinnyID
      "user_id": "4c5047c0-5f2b-42bb-a316-f86193f8ab4f",
      ...
    },
  },
  quotes:{}
  ...
}
```

## 关键代码调整

### 创建账户实例
用户代码
```
future_account = TqAccount("N南华期货","abc","123456")          
stock_account = TqAccount("N南华期货_股票", "cba", "123456", "httpsown-otg")
raw_sim_account = TqSim()
sim_account_withname = TqSim("simaccount1")
```
#### 账户实现调整 `TqAccount/TqSim/TqKq`

* 实盘账户 `TqAccount` 初始化时增加可选参数 `td_url`，用于指定账户连接的交易服务器地址，若参数为空，则由 `TqApi` 模块
根据期货公司选择不同的交易网关地址。
    ```
    TqAccount.__init__(self, broker_id: str, account_id: str ...  + td_url: Optional[str] = None ) -> None:
    ```


### 创建TqApi实例
用户代码：创建 TqApi 并传入账户实例列表

```
api = TqApi([future_account, stock_account])
```

#### `TqAPI` 实例化
```
TqApi. __init__(self, 
    account: Union[ + List[ Union[TqAccount, TqSim, TqKq] ], TqAccount, TqSim, None] = None, 
    auth: Optional[str] = None, 
    url: Optional[str] = None,             
    ...) -> None:
```
* 参数 `account`  增加多账户列表类型，列表支持实盘账户 `TqAccount `、模拟账户`TqSim` 和快期账号 `TqKq` 实例，
列表支持实例个数 0 ~ N。
* 行情服务器地址始终使用 `wss://openmd.shinnytech.com/t/md/front/mobile`；
交易服务器地址由 `TqApi` 根据期货公司从 ` https://files.shinnytech.com/broker-list.json`  配置中获取，
用户也可以在创建实盘账户实例时指定 `td_url`，见上一节。
* `TqApi`  多账户实例创建时，`TqApi.__Init__`  中 `url` 参数无效，单一实盘账户实例，可以通过设置 `url` 参数指定交易服务器地址
* 回测时，用户账户列表中包含实盘账户，直接告警退出

#### `~tqsdk.TqApi::_setup_connection`  多账户实例消息串行处理

```
for index in self._account_list:
    api_send_chan, api_recv_chan = _send_chan, _recv_chan
    self.create_task(self._connect(self._td_url[index], ws_td_send_chan[index], ws_td_recv_chan[index]))
    self.create_task(api._account[index]._run(
            self._api, api_send_chan, api_recv_chan, _send_chan, _recv_chan, ws_md_send_chan, \
ws_md_recv_chan, ws_td_send_chan, ws_td_recv_chan))
```
其中, TqAccount 实现调整如下：

```
TqAccount.__run(self, api, api_send_chan, api_recv_chan, \ 
    + api_send_next_chan, + api_recv_next_chan, \ # 增加 chan 向下一个账户实例传递消息
    ws_md_send_chan, ws_md_recv_chan, ws_td_send_chan, ws_td_recv_chan)  # 当账户为账户列表最后一个账户时，则将消息发送至交易服务器或行情服务器
                for pack in api_send_chan:
                    if pack = 行情包:
                        api_send_next_chan.send(pack)

                    elif pack = 交易包:
                        if pack["account_key"] == id(self):
                            ws_td_send_chans.send(pack)
                        elif:
                            api_send_next_chan.send(pack)

                for pack in ws_md_recv_chan:#行情包中有东西
                    api_recv_chan.send(pack)
```
* 增加参数 `api_send_next_chan, api_recv_next_chan` 用于存储发往下一个账户实例的消息
* 增加参数 `is_last_account` 用于标识该账户是否为账户列表中最后一个账户实例
* 账户对接收到的消息包进行判断处理：
    * 若为行情数据包
        * 该账户为账户列表中最后一个账户，直接将消息发送至行情网关
        * 若为行情数据包且账户后存在其他账户实例，将该数据包发送给下一个账户实例
    * 若数据包为交易数据包
        * 若为当前账户交易数据包，发送至交易服务器
        * 若不为当前账户交易数据包，发送至下一个账户实例
    * 若从行情服务器收到回包，直接发送给下行数据流中的 `api_recv_chan`

## 交易接口调整

`TqApi` 模块交易接口适配多账户进行以下调整

### 下单
```TqApi.insert_order(... +account: Optional[str] = None)```
* 参数增加账户列表，该参数为空时，为 `TqApi` 实例账户列表中第一个账户

### 获取用户账户资金信息
```
def get_account(self, + account: Optional[ List[ Union[TqAccount, TqSim, TqKq, str]  ] = None) -> List[ Account ]:
```

* 增加账户列表参数 `account`，列表支持查询 1 ~ N 个账户
* 多账户时
    * 账户列表参数，默认为空，此时返回 `List[:py:class:~tqsdk.objs.Account]`
    * 账户列表参数中账户数 大于1 时，返回 `List[:py:class:~tqsdk.objs.Account]`
    * 账户列表参数中账户数量 等于 1 时，返回账户对象 `:py:class:~tqsdk.objs.Account` 的引用 
*  单账户交易时，返回账户对象 `:py:class:~tqsdk.objs.Account` 的引用 

### 获取用户持仓信息

```
def get_position(self, + account)  -> Union[Position, Entity, dict] :
```
* 增加账户列表参数 `account`
* 单账户时，返回持仓对象的一个引用
* 多账户时，返回 `dict`，其中，`key`  为账户号 `user_id`，`value` 为持仓对象引用

### 获取用户委托单信息

```
def get_order(self, + account) -> Union[Order, Entity, dict] :

```
* 增加账户列表参数 `account`
* 单账户时，返回一个委托单对象引用
* 多账户时，返回 `dict`，其中，`key`  为账户号 `user_id`，`value` 为委托单对象引用

### 获取用户成交信息
```
def get_trade(self, ... , + account) -> Union[Trade, Entity, dict ]:
```
* 增加账户列表参数 `account`
* 单账户时，返回一个成交对象引用
* 多账户时，返回 `dict`，其中，`key`  为账户号 `user_id`，`value` 为成交对象引用

## 测试用例添加
* 原单账户测试案例的回归测试无影响
* 多账户场景下
    * `TqSim` × 2 
    * `TqSim` × 1 和 `TqAccount` × 1
    * `TqSim` × 1 和 `TqKq` × 1 
    * `TqAccount` × 2
    
  下单、撤单、获取资金、委托、成交和持仓正确

    
    