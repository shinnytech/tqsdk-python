#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import copy

from tqsdk.entity import Entity


class TqDiff(object):

    @staticmethod
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
                    dv = result.pop(key, None)
                    TqDiff._notify_update(dv, True)
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
                target = TqDiff._get_obj(result, [key], default=default)
                TqDiff._merge_diff(target, diff[key], tpt, tpersist)
                if len(diff[key]) == 0:
                    del diff[key]
            elif key in result and (
                    result[key] == diff[key] or (diff[key] != diff[key] and result[key] != result[key])):
                # 判断 diff[key] != diff[key] and result[key] != result[key] 以处理 value 为 nan 的情况
                del diff[key]
            else:
                result[key] = diff[key]
        if len(diff) != 0:
            TqDiff._notify_update(result, False)

    @staticmethod
    def _notify_update(target, recursive):
        """同步通知业务数据更新"""
        if isinstance(target, dict) or isinstance(target, Entity):
            for q in target["_listener"]:
                q.send_nowait(True)
            if recursive:
                for v in target.values():
                    TqDiff._notify_update(v, recursive)

    @staticmethod
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

    @staticmethod
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

