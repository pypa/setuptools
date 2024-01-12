import sys


if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    from setuptools.extern import tomli as tomllib
