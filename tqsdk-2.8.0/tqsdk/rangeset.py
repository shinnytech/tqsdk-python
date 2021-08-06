#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yanqiong'

from typing import Tuple, List

"""
Range 用来表示一个数据段，包含 start, end 之间的 int64 类型连续整数集合，包含 end - start - 1 个数据点 (左闭右开区间)
一个 Range 用元组来表示，例如: (0, 100), (8000, 10000)

RangeSet 是一组有序的递增的 Range
"""
Range = Tuple[int, int]
RangeSet = List[Range]


def _range_intersection(range1: Range, range2: Range) -> RangeSet:
    # 两个 range 的交集
    s1, e1 = range1
    s2, e2 = range2
    if s2 >= e1:
        return []
    elif s2 >= s1:
        return [(s2, min(e1, e2))]
    elif e2 <= s1:
        return []
    else:
        return [(s1, min(e1, e2))]


def _range_union(range1: Range, range2: Range) -> RangeSet:
    # 两个 range 的并集
    s1, e1 = range1
    s2, e2 = range2
    if s2 > e1:
        return [(s1, e1), (s2, e2)]
    elif s2 >= s1:
        return [(s1, max(e1, e2))]
    elif e2 < s1:
        return [(s2, e2), (s1, e1)]
    else:
        return [(s2, max(e1, e2))]


def _range_subtraction(range1: Range, range2: Range) -> RangeSet:
    # 两个 range 的差集，在 range1 中但是不在 range2 中
    s1, e1 = range1
    s2, e2 = range2
    if s2 >= e1:
        return [(s1, e1)]
    elif s2 > s1:
        if e2 < e1:
            return [(s1, s2), (e2, e1)]
        else:
            return [(s1, s2)]
    elif e2 <= s1:
        return [(s1, e1)]
    elif e2 < e1:
        return [(e2, e1)]
    else:
        return []


def _rangeset_length(rangeset: RangeSet) -> int:
    """返回 rangeset 长度"""
    l = 0
    for s, e in rangeset:
        l += e - s
    return l


def _rangeset_head(rangeSet: RangeSet, n: int) -> RangeSet:
    """
    求出在集合 rangeSet 中, 头部 n 个元素
    :return: RangeSet
    """
    r = []
    for s, e in rangeSet:
        if n <= 0:
            break
        if e - s <= n:
            r.append((s, e))
            n -= (e - s)
        else:
            r.append((s, s + n))
            break
    return r


def _rangeset_slice(rangeset: RangeSet, start: int, end: int = None) -> RangeSet:
    """
    求出集合 rangeset 中, start ~ end 构成的 rangeset
    ## 等价于 _rangeset_intersection(rangeset, [(start, end)])
    rangeset 是一个列表，里面包含的元素格式为 [S1,E1] 表示一个数据段，其中每段包括S~E-1数据点(左闭右开区间)
    任意两个数据段都不重叠且不连续
    数据段总是从小到大排序
    :param rangeset start: 时间1
    :param rangeset end: 时间2，不填表示到 rangeset 的结尾
    :return: rangeset，两个集合的交集
    """
    r = []
    for s, e in rangeset:
        if start >= e:
            continue
        if end and end <= s:
            break
        r.append((max(s, start), e if end is None else min(e, end)))
    return r


def _rangeset_intersection(rangeset_a: RangeSet, rangeset_b: RangeSet) -> RangeSet:
    """
    求既在集合 rangeset_a 中又在集合 rangeset_b 中的元素组成的 rangeset
    rangeset_a - rangeset_b
    :param rangeset rangeset_a:
    :param rangeset rangeset_b:
    :return: rangeset，两个集合的交集
    """
    if len(rangeset_a) == 0 or len(rangeset_b) == 0:
        return []
    r = []
    index_a, index_b = 0, 0
    while index_a < len(rangeset_a) and index_b < len(rangeset_b):
        r_a = rangeset_a[index_a]
        r_b = rangeset_b[index_b]
        intersection = _range_intersection(r_a, r_b)
        if intersection:
            r += intersection
        if r_a[1] <= r_b[1]:
            index_a += 1
        else:
            index_b += 1
    return r


def _rangeset_difference(rangeset_a: RangeSet, rangeset_b: RangeSet) -> RangeSet:
    """
    求出在集合 rangeset_a 中但是不在集合 rangeset_b 中的元素组成的 rangeset
    rangeset_a - rangeset_b
    :param rangeset rangeset_a:
    :param rangeset rangeset_b:
    :return: rangeset，两个集合的差集
    """
    if len(rangeset_a) == 0 or len(rangeset_b) == 0:
        return rangeset_a
    intersetction = _rangeset_intersection(rangeset_a, rangeset_b)  # rangeset_a 和 rangeset_b 的交集
    # rangeset_a - intersetction 等价于 rangeset_a - rangeset_b，此时 intersetction 一定是 rangeset_a 的子集
    if len(intersetction) == 0:
        return rangeset_a
    r = []
    index_a, index_b = 0, 0
    rangeset_a = rangeset_a.copy()
    rangeset_b = intersetction  # 此时 rangeset_b 一定是 rangeset_a 的子集
    while index_a < len(rangeset_a):
        r_a = rangeset_a[index_a]
        r_b = rangeset_b[index_b] if index_b < len(rangeset_b) else rangeset_b[-1]
        inter = _range_intersection(r_a, r_b)
        if inter:
            sub = _range_subtraction(r_a, r_b)
            if len(sub) == 0:
                index_a += 1
            elif len(sub) == 1:
                if sub[0][1] == inter[0][0]:
                    r.append(sub[0])
                    index_a += 1
                else:
                    rangeset_a[index_a] = (inter[0][1], r_a[1])
            else:
                r.append(sub[0])
                rangeset_a[index_a] = (inter[0][1], r_a[1])
            index_b += 1
        else:
            r.append(r_a)
            index_a += 1
    return r


def _rangeset_range_union(rangeset: RangeSet, other_range: Range) -> RangeSet:
    # 将 other_range 并入 rangeset, 求交集
    start_index = None
    for i in range(len(rangeset)):
        r = rangeset[i]
        if other_range[0] <= r[1]:
            start_index = i
            break
    if start_index is None:
        return rangeset + [other_range]
    union = rangeset[:start_index]
    end = None
    for i in range(start_index, len(rangeset)):
        r = rangeset[i]
        if other_range[1] < r[0]:
            end = other_range[1]
            break
        elif r[0] <= other_range[1] <= r[1]:
            end = r[1]
            i += 1
            break
    start = min(other_range[0], rangeset[start_index][0])
    if end:
        union.append((start, end))
        union += rangeset[i:]
    else:
        union.append((start, other_range[1]))
    return union


def _rangeset_union(rangeset_a: RangeSet, rangeset_b: RangeSet) -> RangeSet:
    """
    求既在集合 rangeset_a 中或者在集合 rangeset_b 中的元素组成的 rangeset
    rangeset_a + rangeset_b
    :param rangeset rangeset_a:
    :param rangeset rangeset_b:
    :return: rangeset，两个集合的并集
    """
    if len(rangeset_a) == 0:
        return rangeset_b
    if len(rangeset_b) == 0:
        return rangeset_a
    if rangeset_a == rangeset_b:
        return rangeset_a
    rangeset_union = rangeset_a.copy()
    for r_b in rangeset_b:  # 将 r 并入 rangeset_union
        rangeset_union = _rangeset_range_union(rangeset_union, r_b)
    return rangeset_union
