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
    for key in tuple(diff):
        val = diff[key]
        value_type = _type(val)
        if value_type is str and key in prototype and _type(prototype[key]) is not str:
            val = prototype[key]
            diff[key] = val
        if val is None:
            if (persist or "#" in prototype) and reduce_diff:
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
            target = _get_obj_single(result, key, default)
            _merge_diff(target, val, tpt, persist=tpersist, reduce_diff=reduce_diff, notify_update_diff=notify_update_diff)
            if reduce_diff and len(val) == 0:
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
    for i in range(len(path)):
        diff_obj = {path[len(path)-i-1]: diff_obj}
    return diff_obj


def _notify_update(target, recursive, content):
    """同步通知业务数据更新"""
    if type(target) is dict or hasattr(target, '_data'):
        for q in getattr(target, "_listener", {}):
            q.send_nowait(content)
        if recursive:
            for v in target.values():
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
        if not isinstance(diff, dict) or p not in diff:
            return False
        diff = diff[p]
    if not isinstance(diff, dict):
        return False
    for k in key:
        if k in diff:
            return True
    return len(key) == 0


def _simple_merge_diff(result, diff):
    """
    更新业务数据
    :param result: 更新结果
    :param diff: diff pack
    :return:
    """
    for key in list(diff.keys()):
        if diff[key] is None:
            result.pop(key, None)
        elif isinstance(diff[key], dict):
            target = result.setdefault(key, {})
            _simple_merge_diff(target, diff[key])
        else:
            result[key] = diff[key]


def _simple_merge_diff_and_collect_paths(result, diff, path: Tuple, diff_paths: Set, prototype: Union[Dict, None]):
    """
    更新业务数据并收集指定节点的路径
    默认行为 reduce_diff=False，表示函数运行过程中不会修改 diff 本身
    :param result: 更新结果
    :param diff: diff pack
    :param path: 当前迭代 merge_diff 的节点路径
    :param diff_paths: 收集指定节点的路径
    :param prototype: 数据原型, 为 None 的节点路径会被记录在 diff_paths 集合中
    :return:
    """
    for key in list(diff.keys()):
        if diff[key] is None:
            result.pop(key, None)
            if prototype and ('*' in prototype or key in prototype) and prototype['*' if '*' in prototype else key] is None:
                diff_paths.add(path + (key, ))
        elif isinstance(diff[key], dict):
            target = result.setdefault(key, {})
            sub_path = path + (key, )
            sub_prototype = None
            if prototype and ('*' in prototype or key in prototype):
                sub_prototype = prototype['*' if '*' in prototype else key]
                if sub_prototype is None:
                    diff_paths.add(sub_path)
            _simple_merge_diff_and_collect_paths(target, diff[key], path=sub_path, prototype=sub_prototype, diff_paths=diff_paths)
        elif key in result and result[key] == diff[key]:
            pass
        else:
            result[key] = diff[key]
            # 只有确实有变更的字段，会出现在 diff_paths 里
            if prototype and ('*' in prototype or key in prototype) and prototype['*' if '*' in prototype else key] is None:
                diff_paths.add(path + (key, ))
