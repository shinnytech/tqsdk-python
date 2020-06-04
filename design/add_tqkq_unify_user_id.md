# 简介

此代码设计文档是为了完成使用统一账户登录快期模拟服务器而做。

相关需求：https://shinnytech.atlassian.net/browse/BE-257

**目标读者** tqsdk 开发及 code reviewer

# 约束目标

* 实现使用统一的快期账户登录。
* 原来的注册过的用户还能够继续使用原来的账户。
* 最好不改变现有用户的使用 TqAccount 的登录方式。

# todo:

## 增加 TqKuaiqi (extends TqAccount) 类，专门处理使用快期统一账户登录。

```
api setup_connection 需要修改的地方：

self._auth is None
    |
    |--> Yes - self._access_token = ""
    |        - self._account is TqKuaiqi
    |            |
    |            |--> Yes - raise Exception("需要快期账户认证")
    |            |
    |            |--> No
    |
    |--> No - request access_token with self._auth
               |
               |--> Success - self._access_token = response.access_token
               |            - logger.info("认证成功")
               |            - self._account is TqKuaiqi
               |               |
               |               |--> Yes - 解析 access_token, 得到的 'sub' 字段即为用户 ID, self._account._account_id = ID, self._account._password = ID
               |               |
               |               |--> No
               |
               |--> Fail - raise Exception("认证失败")
```

* api 在 setup_connection 中 TqWebHelper 初始化之后，运行以上逻辑

## TqWebHelper 增加处理相应环境变量参数的逻辑

```
TQ_HTTP_SERVER_ADDRESS [option] 设置 web_gui address
TQ_ACTION [option] 运行模式 (run, backtest, replay)
**TQ_AUTH** [option] 用户认证信息
TQ_INIT_BALANCE

TQ_BROKER_ID (TQ_ACTION=run) 
TQ_ACCOUNT_ID (TQ_ACTION=run) 
TQ_PASSWORD (TQ_ACTION=run) 

TQ_START_DT (TQ_ACTION=backtest) 
TQ_END_DT (TQ_ACTION=backtest)  
 
TQ_REPLAY_DT (TQ_ACTION=replay)                                
```

TqWebHelper 参数处理流程

```python
# 判断与构造 api 的 auth 参数是否冲突，如果有则抛错
api._auth = TQ_AUTH if TQ_AUTH else None

if TQ_ACTION == "run":
    api._backtest = None
    if TQ_BROKER_ID == "TQ_KQ":
        # 判断与构造 api 账户参数是否冲突，如果有则抛错
        api._account = TqKuaiqi()
    elif TQ_BROKER_ID and TQ_ACCOUNT_ID and TQ_PASSWORD:
        # 判断与构造 api 账户参数是否冲突，如果有则抛错
        api._account = TqAccount(TQ_BROKER_ID, TQ_ACCOUNT_ID, TQ_PASSWORD)
    else:
        api._account = TqSim(TQ_INIT_BALANCE if TQ_INIT_BALANCE else 10000000)

else:
    api._account = TqSim(TQ_INIT_BALANCE if TQ_INIT_BALANCE else 10000000)
    if TQ_ACTION == "backtest" and TQ_START_DT and TQ_END_DT:
        api._backtest = TqBacktest(TQ_START_DT, TQ_END_DT)
    elif TQ_ACTION == "replay" and TQ_REPLAY_DT:
        api._backtest = TqReplay(TQ_REPLAY_DT)
    else:
        api._backtest = None
```
* TQ_AUTH 一定有效，TQ_AUTH 与 api 构造参数中 auth 冲突时，抛错并提示用户
* TQ_BROKER_ID, TQ_ACCOUNT_ID, TQ_PASSWORD 只在 TQ_ACTION=="run" 有效，当与 api 构造函数中的账户信息冲突时，抛错并提示用户
* TQ_START_DT, TQ_END_DT 只在 TQ_ACTION=="backtest" 有效
* TQ_REPLAY_DT 只在 TQ_ACTION=="replay" 有效
* TQ_INIT_BALANCE 在判断账户类型为 TqSim 时有效

