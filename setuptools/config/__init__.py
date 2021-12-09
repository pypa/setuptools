# For backward compatibility, the following classes/functions are exposed
# from `config.legacy_setupcfg`
from setuptools.config.legacy_setupcfg import parse_configuration

__all__ = [
    'parse_configuration',  # still required by setuptools.dist
]
