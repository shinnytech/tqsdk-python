#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))

# 全部主连合约对应的标的合约
ls = api.query_cont_quotes()
print(ls)

# 大商所主连合约对应的标的合约
ls = api.query_cont_quotes(exchange_id="DCE")
print(ls)

# jd 品种主连合约对应的标的合约
ls = api.query_cont_quotes(product_id="jd")
print(ls)

# 关闭api,释放相应资源
api.close()

# 预期输出如下
# ['SHFE.cu2503', 'SHFE.ni2503', 'CFFEX.TS2503', 'SHFE.br2503', 'CZCE.OI505', 'DCE.c2505', 'GFEX.lc2505', 'INE.bc2503', 'CZCE.CJ505', 'CFFEX.TF2503', 'SHFE.hc2505', 'SHFE.ru2505', 'DCE.lg2507', 'DCE.a2505', 'DCE.b2505', 'GFEX.ps2506', 'SHFE.ss2505', 'CZCE.CF505', 'DCE.m2505', 'CFFEX.T2503', 'DCE.pg2503', 'CZCE.SR505', 'CZCE.PF504', 'SHFE.pb2503', 'CZCE.UR505', 'CZCE.MA505', 'CZCE.PX505', 'SHFE.sn2503', 'GFEX.si2505', 'CZCE.FG505', 'CFFEX.IM2503', 'CZCE.ZC505', 'CFFEX.IC2503', 'INE.nr2504', 'INE.lu2505', 'DCE.fb2505', 'CZCE.RM505', 'CFFEX.TL2503', 'CZCE.SA505', 'CZCE.AP505', 'CZCE.PK505', 'CZCE.SF505', 'SHFE.ao2505', 'CZCE.TA505', 'SHFE.bu2504', 'SHFE.zn2503', 'DCE.jm2505', 'DCE.jd2505', 'INE.sc2504', 'INE.ec2504', 'CZCE.PM505', 'DCE.lh2505', 'CZCE.WH505', 'CZCE.RI505', 'DCE.l2505', 'CZCE.PR503', 'CZCE.CY505', 'DCE.eg2505', 'DCE.pp2505', 'SHFE.fu2505', 'DCE.v2505', 'DCE.p2505', 'SHFE.rb2505', 'CZCE.JR505', 'SHFE.sp2505', 'CZCE.SM505', 'CFFEX.IF2503', 'DCE.rr2503', 'SHFE.au2504', 'DCE.bb2509', 'SHFE.ag2504', 'SHFE.al2504', 'DCE.j2505', 'CZCE.RS507', 'DCE.y2505', 'DCE.i2505', 'CZCE.SH505', 'CZCE.LR505', 'DCE.cs2503', 'SHFE.wr2505', 'CFFEX.IH2503', 'DCE.eb2503']
# ['DCE.c2505', 'DCE.lg2507', 'DCE.a2505', 'DCE.b2505', 'DCE.m2505', 'DCE.pg2503', 'DCE.fb2505', 'DCE.jm2505', 'DCE.jd2505', 'DCE.lh2505', 'DCE.l2505', 'DCE.eg2505', 'DCE.pp2505', 'DCE.v2505', 'DCE.p2505', 'DCE.rr2503', 'DCE.bb2509', 'DCE.j2505', 'DCE.y2505', 'DCE.i2505', 'DCE.cs2503', 'DCE.eb2503']
# ['DCE.jd2505']
