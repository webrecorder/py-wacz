#!/usr/bin/env python3
# vim: set sw=4 et:
from setuptools import setup, find_packages

__version__ = "0.5.0"

def load_requirements(filename):
    with open(filename, "rt") as fh:
        return fh.read().rstrip().split("\n")

def long_description():
    with open("README.md") as f:
        return f.read()

setup(
    name="wacz",
    version=__version__,
    author="Ilya Kreymer, Emma Dickson",
    author_email="info@webrecorder.net",
    license="Apache 2.0",
    packages=find_packages(exclude=["test"]),
    url="https://github.com/webrecorder/py-wacz",
    description="WACZ Format Tools",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    install_requires=load_requirements("requirements.txt"),
    extras_require={"signing": ["authsign>=0.5.1", "requests"]},
    zip_safe=True,
    setup_requires=["pytest-runner"],
    entry_points="""
        [console_scripts]
        wacz = wacz.main:main
    """,
)
