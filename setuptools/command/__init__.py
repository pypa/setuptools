import distutils.command

__all__ = ['test', 'depends']


# Make our commands available as though they were part of the distutils

distutils.command.__path__.extend(__path__)
distutils.command.__all__.extend(
    [cmd for cmd in __all__ if cmd not in distutils.command.__all__]
)
