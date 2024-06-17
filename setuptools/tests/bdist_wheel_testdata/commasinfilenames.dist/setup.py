from __future__ import annotations

from setuptools import setup

setup(
    name="testrepo",
    version="0.1",
    packages=["mypackage"],
    description="A test package with commas in file names",
    include_package_data=True,
    package_data={"mypackage.data": ["*"]},
)
