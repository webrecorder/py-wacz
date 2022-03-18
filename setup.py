#!/usr/bin/env python3
# vim: set sw=4 et:
from setuptools import setup, find_packages

__version__ = "0.4.4"


def load_requirements(filename):
    with open(filename, "rt") as fh:
        return fh.read().rstrip().split("\n")


setup(
    name="wacz",
    version=__version__,
    author="Ilya Kreymer, Emma Dickson",
    author_email="info@webrecorder.net",
    license="Apache 2.0",
    packages=find_packages(exclude=["test"]),
    url="https://github.com/webrecorder/wacz-format",
    description="WACZ Format Tools",
    long_description="Create and validate web archive data packaged using WACZ",
    install_requires=load_requirements("requirements.txt"),
    extras_require={"signing": ["authsign>=0.3.1", "requests"]},
    zip_safe=True,
    setup_requires=["pytest-runner"],
    entry_points="""
        [console_scripts]
        wacz = wacz.main:main
    """,
)
