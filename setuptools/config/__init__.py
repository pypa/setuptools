# For backward compatibility, the following classes/functions are exposed
# from `config.setupcfg`
from setuptools.config.setupcfg import (
    parse_configuration,
    read_configuration,
)

__all__ = [
    'parse_configuration',
    'read_configuration'
]
