#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import random
import uuid


RD = random.Random()  # 初始化随机数引擎


def _generate_uuid(prefix=''):
    return f"{prefix + '_' if prefix else ''}{uuid.UUID(int=RD.getrandbits(128)).hex}"
