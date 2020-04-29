#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import copy

from tqsdk.entity import Entity


def _merge_diff(result, diff, prototype, persist):
    """更新业务数据,并同步发送更新通知，保证业务数据的更新和通知是原子操作"""
    for key in list(diff.keys()):
        value_type = type(diff[key])
        if value_type is str and key in prototype and not type(prototype[key]) is str:
            diff[key] = prototype[key]
        if diff[key] is None:
            if persist or "#" in prototype:
                del diff[key]
            else:
                path = result["_path"].copy()
                dv = result.pop(key, None)
                path.append(key)
                _notify_update(dv, True, _gen_diff_obj(None, path))
        elif value_type is dict or value_type is Entity:
            default = None
            tpersist = persist
            if key in prototype:
                tpt = prototype[key]
            elif "*" in prototype:
                tpt = prototype["*"]
            elif "@" in prototype:
                tpt = prototype["@"]
                default = tpt
            elif "#" in prototype:
                tpt = prototype["#"]
                default = tpt
                tpersist = True
            else:
                tpt = {}
            target = _get_obj(result, [key], default=default)
            _merge_diff(target, diff[key], tpt, tpersist)
            if len(diff[key]) == 0:
                del diff[key]
        elif key in result and (
                result[key] == diff[key] or (diff[key] != diff[key] and result[key] != result[key])):
            # 判断 diff[key] != diff[key] and result[key] != result[key] 以处理 value 为 nan 的情况
            del diff[key]
        else:
            result[key] = diff[key]
    if len(diff) != 0:
        diff_obj = _gen_diff_obj(diff, result["_path"])
        _notify_update(result, False, diff_obj)


def _gen_diff_obj(diff, path):
    """将 diff 根据 path 拼成一个完整的 diff 包"""
    diff_obj = diff
    for i in range(len(path)):
        diff_obj = {path[len(path)-i-1]: diff_obj}
    return diff_obj


def _notify_update(target, recursive, content):
    """同步通知业务数据更新"""
    if isinstance(target, dict) or isinstance(target, Entity):
        for q in target["_listener"]:
            q.send_nowait(content)
        if recursive:
            for v in target.values():
                _notify_update(v, recursive, content)


def _get_obj(root, path, default=None):
    """获取业务数据"""
    d = root
    for i in range(len(path)):
        if path[i] not in d:
            if i != len(path) - 1 or default is None:
                dv = Entity()
            else:
                dv = copy.copy(default)
            dv._instance_entity(d["_path"] + [path[i]])
            d[path[i]] = dv
        d = d[path[i]]
    return d


def _register_update_chan(objs, chan):
    if not isinstance(objs, list):
        objs = [objs]
    for o in objs:
        o["_listener"].add(chan)
    return chan


def _is_key_exist(diff, path, key):
    """判断指定数据是否存在"""
    for p in path:
        if not isinstance(diff, dict) or p not in diff:
            return False
        diff = diff[p]
    if not isinstance(diff, dict):
        return False
    for k in key:
        if k in diff:
            return True
    return len(key) == 0


def _simple_merge_diff(result, diff, reduce_diff=True, persist=False):
    """
    更新业务数据
    :param result: 更新结果
    :param diff: diff pack
    :param reduce_diff: 表示是否修改 diff 对象本身，因为如果 merge_diff 的 result 是 conn_chan 内部的 last_diff，那么 diff 会在循环中多次使用，这时候一定不能修改 diff 本身
            如果为True 函数运行完成后，diff 会更新为与 result 真正的有区别的字段；如果为 False，diff 不会修改
    :param persist: 是否一定存储当前 diff 涉及的字段，如果为 True，则 result 为 None 的对象不会删除；如果是 False，则 result 为 None 的对象会被删除
    :return:
    """
    for key in list(diff.keys()):
        if diff[key] is None:
            if persist and reduce_diff:
                del diff[key]
            if not persist:
                result.pop(key, None)
        elif isinstance(diff[key], dict):
            target = result.setdefault(key, {})
            _simple_merge_diff(target, diff[key], reduce_diff=reduce_diff)
            if len(diff[key]) == 0:
                del diff[key]
        elif reduce_diff and key in result and result[key] == diff[key]:
            del diff[key]
        else:
            result[key] = diff[key]
