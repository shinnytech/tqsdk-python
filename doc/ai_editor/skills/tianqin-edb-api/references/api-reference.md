# API 参考（摘要）

本参考为“天勤 EDB 数据服务”常用接口的快速摘要，便于在扣子（Coze）Skill 内编写脚本调用。

## 1) 行情历史服务（CSV）

- Base：`https://edb.shinnytech.com/md`
- GET `/kline`

常用参数：

- `period`：`60`（1 分钟）或 `86400`（日线，按交易日）
- `symbol`：如 `SHFE.rb2401`、`KQ.m@CFFEX.IF`
- `start_time` / `end_time`：`YYYY-MM-DD HH:MM:SS`
- `col`：逗号分隔列名（可选）：`open,high,low,close,volume,open_oi,close_oi`
- `token`：可通过 query 传入（不推荐）或用 Header 传入（推荐）

鉴权（专业版）：

- `Authorization: Bearer <token>`

## 2) Token 服务（JSON）

- Base：`https://edb.shinnytech.com`
- POST `/token`

请求体（JSON）：

```json
{"username":"<user>","password":"<password>"}
```

响应（JSON）：

```json
{"token":"<access_token>"}
```

## 3) EDB 指标服务（JSON，专业版）

- Base：`https://edb.shinnytech.com/data`

接口：

- POST `/index_table`：查询指标目录（支持 `ids` 或 `search`）
- POST `/index_data`：查询指标数值（`ids` + `start/end`）

鉴权：

- `Authorization: Bearer <token>`

