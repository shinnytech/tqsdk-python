#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import copy
from typing import Set, Union, Dict, Tuple

from tqsdk.entity import Entity


def _merge_diff(result, diff, prototype, persist, reduce_diff=False, notify_update_diff=False):
    """
    更新业务数据,并同步发送更新通知，保证业务数据的更新和通知是原子操作
    :param result: 更新结果
    :param diff: diff pack
    :param persist: 是否保留 result 中所有字段，如果为 True，则 diff 里为 None 的对象在 result 中不会删除；如果是 False，则 result 结果中会删除 diff 里为 None 的对象
    :param reduce_diff: 表示是否修改 diff 对象本身，如果为 True 函数运行完成后，diff 会更新为与 result 真正的有区别的字段；如果为 False，diff 不会修改
        默认不会修改 diff，只有 api 中 is_changing 接口需要 diffs 为真正有变化的数据
    :param notify_update_diff: 为 True 表示发送更新通知的发送的是包含 diff 的完整数据包（方便 TqSim 中能每个合约的 task 可以单独维护自己的数据），反之只发送 True
    :return:
    """
    for key in list(diff.keys()):
        value_type = type(diff[key])
        if value_type is str and key in prototype and not type(prototype[key]) is str:
            diff[key] = prototype[key]
        if diff[key] is None:
            if (persist or "#" in prototype) and reduce_diff:
                del diff[key]
            else:
                if notify_update_diff:
                    dv = result.pop(key, None)
                    _notify_update(dv, True, _gen_diff_obj(None, result["_path"] + [key]))
                else:
                    dv = result.pop(key, None)
                    _notify_update(dv, True, True)
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
            _merge_diff(target, diff[key], tpt, persist=tpersist, reduce_diff=reduce_diff, notify_update_diff=notify_update_diff)
            if reduce_diff and len(diff[key]) == 0:
                del diff[key]
        elif reduce_diff and key in result and (
                result[key] == diff[key] or (diff[key] != diff[key] and result[key] != result[key])):
            # 判断 diff[key] != diff[key] and result[key] != result[key] 以处理 value 为 nan 的情况
            del diff[key]
        else:
            result[key] = diff[key]
    if len(diff) != 0:
        diff_obj = True
        if notify_update_diff:
            # 这里发的数据目前是不需要 copy (浅拷贝会有坑，深拷贝的话性能不知道有多大影响)
            # 因为这里现在会用到发送这个 diff 的只有 quote 对象，只有 sim 会收到使用，sim 收到之后是不会修改这个 diff
            # 所以这里就约定接收方不能改 diff 中的值
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
        for q in getattr(target, "_listener", {}):
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
