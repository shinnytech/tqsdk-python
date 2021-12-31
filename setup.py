# -*- coding: utf-8 -*-
__author__ = 'yangyang'

import setuptools

# from py-spy/setup.py
try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel, get_platform

    class bdist_wheel(_bdist_wheel):

        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package (we have platform specific ctpse lib)
            if self.plat_name != "any":
                self.root_is_pure = False
                plat_name = (self.plat_name or get_platform()).replace('-', '_').replace('.', '_')
                if plat_name == "linux_x86_64" or plat_name == "manylinux1_x86_64":
                    self.distribution.package_data[""] = ["ctpse/LinuxDataCollect64.so"]
                elif plat_name == "win32":
                    self.distribution.package_data[""] = ["ctpse/WinDataCollect32.dll"]
                elif plat_name == "win_amd64":
                    self.distribution.package_data[""] = ["ctpse/WinDataCollect64.dll"]

        def get_tag(self):
            # this set's us up to build generic wheels.
            python, abi, plat = _bdist_wheel.get_tag(self)
            # We don't contain any python source
            python, abi = 'py3', 'none'
            return python, abi, plat
except ImportError:
    bdist_wheel = None

with open("README.md", mode="r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='tqsdk',
    version="3.2.0",
    description='TianQin SDK',
    author='TianQin',
    author_email='tianqincn@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://www.shinnytech.com/tqsdk',
    packages=setuptools.find_packages(),
    zip_safe=False,
    python_requires='>=3.6.4',
    install_requires=["websockets>=8.1", "requests", "numpy", "pandas>=1.1.0", "scipy", "simplejson", "aiohttp",
                      "certifi", "pyjwt", "psutil", "shinny_structlog", "sgqlc"],
    cmdclass={'bdist_wheel': bdist_wheel},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True
)
