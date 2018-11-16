# -*- coding: utf-8 -*-
__author__ = 'yangyang'

import setuptools

with open("README.rst", mode="r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='tqsdk',
    version="0.8.7",
    description='TianQin SDK',
    author='TianQin',
    author_email='tianqincn@gmail.com',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url='http://www.shinnytech.com/tianqin',
    packages=setuptools.find_packages(exclude=["tqsdk.test"]),
    zip_safe=False,
    python_requires='>=3.6',
    install_requires=["websockets>=6.0"],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
)
