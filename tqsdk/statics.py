#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import copy

@staticmethod
def get_obj(root, path, default=None):
	"""获取业务数据"""
	# todo: support nested dict for default value
	d=root
	for i in range(len(path)):
		if path[i] not in d:
			dv={} if i!=len(path)-1 or default is None else copy.copy(default)
			if isinstance(dv, dict):
				dv["_path"]=d["_path"]+[path[i]]
				dv["_listener"]=set()
			d[path[i]]=dv
		d=d[path[i]]
	return d

@staticmethod
def is_key_exist(diff, path, key):
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

@staticmethod
def notify_update(target, recursive):
	"""同步通知业务数据更新"""
	if isinstance(target, dict):
		target["_listener"]={q for q in target["_listener"] if not q.closed}
		for q in target["_listener"]:
			q.send_nowait(True)
		if recursive:
			for v in target.values():
				notify_update.__func__(v, recursive)