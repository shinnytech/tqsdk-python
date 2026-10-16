.. _tqsdk.objs:

tqsdk.objs - 业务对象
------------------------------------------------------------------

正文中的 :py:class:`quote <tqsdk.objs.Quote>`、:py:class:`account <tqsdk.objs.Account>`、
:py:class:`position <tqsdk.objs.Position>`、:py:class:`order <tqsdk.objs.Order>` 和
:py:class:`trade <tqsdk.objs.Trade>` 通常是示例变量名。点击这些名称可以查看对应对象类型，点击字段名可以查看字段定义。

.. automodule:: tqsdk.objs
    :members:
    :exclude-members: iopv

对象集合与查询结果
==================================================================

.. currentmodule:: None

以下类型出现在 API 的返回值中，由对应接口创建。列表和表格的具体内容及更新方式以接口说明为准。

.. py:class:: tqsdk.entity.Entity

    业务数据及其集合使用的映射对象，支持按字段名或键访问。
    :py:meth:`~tqsdk.TqApi.get_position`、:py:meth:`~tqsdk.TqApi.get_order` 和
    :py:meth:`~tqsdk.TqApi.get_trade` 在不指定具体合约或编号时返回对象集合。
    业务数据引用通过 :py:meth:`~tqsdk.TqApi.wait_update` 接收更新。

.. py:class:: tqsdk.objs_not_entity.QuoteList

    :py:meth:`~tqsdk.TqApi.get_quote_list` 返回的行情列表，每项是 :py:class:`~tqsdk.objs.Quote`。

.. py:class:: tqsdk.objs_not_entity.SymbolList

    :py:meth:`~tqsdk.TqApi.query_quotes`、:py:meth:`~tqsdk.TqApi.query_options` 等查询接口返回的合约代码列表。

.. py:class:: tqsdk.objs_not_entity.TqSymbolDataFrame

    :py:meth:`~tqsdk.TqApi.query_symbol_info` 返回的合约信息表，继承 :py:class:`pandas.DataFrame`。

.. py:class:: tqsdk.objs_not_entity.TqMdSettlementDataFrame

    :py:meth:`~tqsdk.TqApi.query_symbol_settlement` 返回的每日结算价表，继承 :py:class:`pandas.DataFrame`。

.. py:class:: tqsdk.objs_not_entity.TqSymbolRankingDataFrame

    :py:meth:`~tqsdk.TqApi.query_symbol_ranking` 返回的合约排名表，继承 :py:class:`pandas.DataFrame`。

.. py:class:: tqsdk.objs_not_entity.TqOptionGreeksDataFrame

    :py:meth:`~tqsdk.TqApi.query_option_greeks` 返回的期权希腊值数据表，继承 :py:class:`pandas.DataFrame`。

.. py:class:: tqsdk.objs_not_entity.TqEdbIndexDataFrame

    :py:meth:`~tqsdk.TqApi.query_edb_data` 返回的经济数据库指标表，继承 :py:class:`pandas.DataFrame`。

