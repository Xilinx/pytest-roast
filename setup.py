#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from setuptools import setup
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


long_description = read("README.md")

setup(
    name="pytest-roast",
    version="1.1.2",
    description="pytest plugin for ROAST configuration override and fixtures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Xilinx/pytest-roast",
    author="Ching-Hwa Yu",
    author_email="chinghwa@xilinx.com",
    py_modules=["pytest_roast"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="roast",
    license="MIT",
    entry_points={"pytest11": ["roast = pytest_roast"]},
    install_requires=["pytest<6", "roast>=2.0.0"],
    extras_require={"dev": ["pytest-mock", "pytest-black", "pytest-cases"]},
    python_requires=">=3.6, <4",
)
