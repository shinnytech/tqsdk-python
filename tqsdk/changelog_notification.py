# !usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'chenli'

import sys
from packaging import version

import requests

from tqsdk.__version__ import __version__

try:
    res = requests.get("https://shinny-tqsdk.oss-cn-shanghai.aliyuncs.com/tqsdk_metadata.json", timeout=10)
    tq_metadata = res.json()
    current_version = version.parse(__version__)
    change_version = version.parse(tq_metadata.get('tqsdk_version', '0.0.0'))
    if tq_metadata.get('tqsdk_changelog') and current_version < change_version:
        print(tq_metadata['tqsdk_changelog'], file=sys.stderr)
    if tq_metadata.get('tqsdk_notify'):
        print(tq_metadata['tqsdk_notify'], file=sys.stderr)
except:
    pass
