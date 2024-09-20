# -*- coding: utf-8 -*-
__author__ = 'yangyang'

import setuptools

with open("README.md", mode="r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='tqsdk',
    version="3.7.3",
    description='TianQin SDK',
    author='TianQin',
    author_email='tianqincn@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://www.shinnytech.com/tqsdk',
    packages=setuptools.find_packages(exclude=["tqsdk.test", "tqsdk.test.*"]),
    python_requires='>=3.6.4',
    install_requires=["websockets>=8.1", "requests", "numpy", "pandas>=1.1.0", "scipy", "simplejson", "aiohttp",
                      "certifi", "pyjwt", "psutil", "shinny_structlog", "sgqlc", "filelock", "tqsdk_ctpse", "tqsdk_sm"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True
)
