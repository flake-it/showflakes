#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    license="MIT",
    version="0.1.0",
    name="showflakes",

    python_requires=">=3.5",
    install_requires=["pytest>=4.0"],

    author="Owain Parry",
    author_email="oparry1@sheffield.ac.uk",
    
    py_modules=["showflakes"],
    entry_points={"pytest11": ["showflakes=showflakes"]}
)
