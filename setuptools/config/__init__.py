# For backward compatibility, the following classes/functions are exposed
# from `config.setupcfg`
from setuptools.config.setupcfg import (
    ConfigHandler,
    parse_configuration,
    read_configuration,
)

__all__ = [
    'ConfigHandler',
    'parse_configuration',
    'read_configuration'
]
