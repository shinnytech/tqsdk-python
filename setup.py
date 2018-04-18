# -*- coding: utf-8 -*-
__author__ = 'yangyang'

from setuptools import setup, find_packages
# from tqsdk import __version__


setup(name='tqsdk',
      version="0.8.0",
      description='TianQin ',
      author='tq18.cn',
      author_email='tianqincn@gmail.com',
      url='http://www.tq18.cn/',
      packages=find_packages(exclude=["tqsdk.test"]),
      zip_safe=False,
      include_package_data=True,
      package_data={
      },
      install_requires=["tornado>=4.3",
                        "sortedcontainers>=1.5.7",
                        ],
      )

