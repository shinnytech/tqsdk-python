# TqSim 支持 FAK / FOK 开发计划


## 开发任务

1. 在 api 提供接口时，已经对不符合交易所规则的交易指令组合，进行抛错的处理。所以认为到 sim 收到的 insert_order 包，应该都是允许下单的。
2. 对于 TqSim，insert_order 指令包有 3 个属性和以前不同需要处理：
    + price_type (BEST / FIVELEVEL / ANY / LIMIT) - BSET / FIVELEVEL / ANY 都是按照对手一档价成交，全成或全撤；LIMIT 是按照限价成交。和现在处理一致。
    + volume_condition (ANY / ALL) - TqSim 很难找出合适的逻辑，支持部分成交，所以 TqSim 对于这个指令条件的处理都是 ALL。
    + time_condition (GFD / IOC) - 当日有效 / 不成即撤
    
总的来说，与当前 TqSim 处理撮合成交的逻辑相比，需要增加的部分是：

限价单的 FAK / FOK，即 price_type == "LIMIT" and time_condition == "IOC"

需要在 _match_order() 增加判断这种情况。

## 测试任务

| 品种        | limit_price | advance  | expect       |
|------------|-------------|----------|-----------------|
| DCE.m2009 | 5050        |    None  | 当日有效          |   
| DCE.m2009 | 5050        |    FAK   | 不成即撤，以不能成交的价格下单，看是否立即撤单 |   
| DCE.m2009 | 5050        |    FOK   | 不成即撤，以不能成交的价格下单，看是否立即撤单 |   
| DCE.m2009 | 5050        |    FAK   | 不成即撤，以可以成交的价格下单，看是否有正确的委托和成交回报 |   
| DCE.m2009 | 5050        |    FOK   | 不成即撤，以可以成交的价格下单，看是否有正确的委托和成交回报 |   
| DCE.m2009 | None        |    None  | 市价全部成交，看是否有正确的委托和成交回报 |
| DCE.m2009 | None        |    FAK   | 市价全部成交，看是否有正确的委托和成交回报 |
| DCE.m2009 | None        |    FOK   | 市价全部成交，看是否有正确的委托和成交回报 |
| DCE.m2009 | BEST        |    None  | expectedFailure |  
| DCE.m2009 | BEST        |    FAK   | expectedFailure |  
| DCE.m2009 | BEST        |    FOK   | expectedFailure |  
| DCE.m2009 | FIVELEVEL   |    None  | expectedFailure |  
| DCE.m2009 | FIVELEVEL   |    FAK   | expectedFailure |  
| DCE.m2009 | FIVELEVEL   |    FOK   | expectedFailure |  
| SHFE.cu2007 | None        |    None  | expectedFailure |  
| SHFE.cu2007 | None        |    FAK   | expectedFailure |  
| SHFE.cu2007 | None        |    FOK   | expectedFailure |   

 * 预期结果就是要么正常下单，比较成交记录和委托单记录；要么抛错
