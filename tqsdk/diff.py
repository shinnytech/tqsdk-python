#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import copy
from typing import Set, Union, Dict, Tuple

from tqsdk.entity import Entity


def _merge_diff(result, diff, prototype, persist, reduce_diff=False, notify_update_diff=False):
    """
    更新业务数据,并同步发送更新通知，保证业务数据的更新和通知是原子操作
    """
    _type = type
    _Entity = Entity
    _dict = dict
    result_data = result._data
    # Access prototype._data directly to bypass Entity method dispatch
    try:
        _pd = prototype._data
    except AttributeError:
        _pd = prototype
    for key in tuple(diff):
        val = diff[key]
        value_type = _type(val)
        if value_type is str and key in _pd and _type(_pd[key]) is not str:
            val = _pd[key]
            diff[key] = val
        if val is None:
            if (persist or "#" in _pd) and reduce_diff:
                del diff[key]
            else:
                dv = result_data.pop(key, None)
                if dv is not None:
                    if notify_update_diff:
                        _notify_update(dv, True, _gen_diff_obj(None, result._path + [key]))
                    else:
                        _notify_update(dv, True, True)
        elif value_type is _dict or value_type is _Entity:
            default = None
            tpersist = persist
            if key in _pd:
                tpt = _pd[key]
            elif "*" in _pd:
                tpt = _pd["*"]
            elif "@" in _pd:
                tpt = _pd["@"]
                default = tpt
            elif "#" in _pd:
                tpt = _pd["#"]
                default = tpt
                tpersist = True
            else:
                tpt = {}
            try:
                target = result_data[key]
            except KeyError:
                if default is None:
                    target = _Entity()
                else:
                    target = copy.copy(default)
                target._instance_entity(result._path + [key])
                result_data[key] = target
            _merge_diff(target, val, tpt, tpersist, reduce_diff, notify_update_diff)
            if reduce_diff and not val:
                del diff[key]
        elif reduce_diff and key in result_data:
            rval = result_data[key]
            if rval == val or (val != val and rval != rval):
                del diff[key]
            else:
                result_data[key] = val
        else:
            result_data[key] = val
    if diff:
        diff_obj = True
        if notify_update_diff:
            diff_obj = _gen_diff_obj(diff, result._path)
        _notify_update(result, False, diff_obj)


def _gen_diff_obj(diff, path):
    """将 diff 根据 path 拼成一个完整的 diff 包"""
    diff_obj = diff
    for p in reversed(path):
        diff_obj = {p: diff_obj}
    return diff_obj


def _notify_update(target, recursive, content):
    """同步通知业务数据更新"""
    target_type = type(target)
    if target_type is dict:
        if recursive:
            for v in target.values():
                _notify_update(v, recursive, content)
        return
    try:
        listener = object.__getattribute__(target, '_listener')
    except AttributeError:
        return
    if listener:
        for q in listener:
            q.send_nowait(content)
    if recursive:
        for v in target._data.values():
            _notify_update(v, recursive, content)


def _get_obj_single(root, key, default=None):
    """获取业务数据 - optimized for single key lookup (most common case)"""
    root_data = root._data
    try:
        return root_data[key]
    except KeyError:
        if default is None:
            dv = Entity()
        else:
            dv = copy.copy(default)
        dv._instance_entity(root._path + [key])
        root_data[key] = dv
        return dv


def _get_obj(root, path, default=None):
    """获取业务数据"""
    d = root
    for i in range(len(path)):
        if path[i] not in d:
            if i != len(path) - 1 or default is None:
                dv = Entity()
            else:
                dv = copy.copy(default)
            dv._instance_entity(d._path + [path[i]])
            d[path[i]] = dv
        d = d[path[i]]
    return d


def _register_update_chan(objs, chan):
    if not isinstance(objs, list):
        objs = [objs]
    for o in objs:
        o._listener.add(chan)
    return chan


def _is_key_exist(diff, path, key):
    """判断指定数据是否存在"""
    for p in path:
        if type(diff) is not dict or p not in diff:
            return False
        diff = diff[p]
    if type(diff) is not dict:
        return False
    for k in key:
        if k in diff:
            return True
    return not key


def _simple_merge_diff(result, diff):
    """
    更新业务数据
    """
    for key in diff:
        val = diff[key]
        if val is None:
            result.pop(key, None)
        elif type(val) is dict:
            target = result.setdefault(key, {})
            _simple_merge_diff(target, val)
        else:
            result[key] = val


def _simple_merge_diff_and_collect_paths(result, diff, path: Tuple, diff_paths: Set, prototype: Union[Dict, None]):
    """
    更新业务数据并收集指定节点的路径
    """
    for key in diff:
        val = diff[key]
        if val is None:
            result.pop(key, None)
            if prototype:
                pkey = '*' if '*' in prototype else key
                if pkey in prototype and prototype[pkey] is None:
                    diff_paths.add(path + (key, ))
        elif type(val) is dict:
            target = result.setdefault(key, {})
            sub_path = path + (key, )
            sub_prototype = None
            if prototype:
                pkey = '*' if '*' in prototype else key
                if pkey in prototype:
                    sub_prototype = prototype[pkey]
                    if sub_prototype is None:
                        diff_paths.add(sub_path)
            _simple_merge_diff_and_collect_paths(target, val, path=sub_path, prototype=sub_prototype, diff_paths=diff_paths)
        elif key in result and result[key] == val:
            pass
        else:
            result[key] = val
            if prototype:
                pkey = '*' if '*' in prototype else key
                if pkey in prototype and prototype[pkey] is None:
                    diff_paths.add(path + (key, ))
