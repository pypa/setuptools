import distutils.command

__all__ = [
    'test', 'develop', 'bdist_egg', 'saveopts', 'setopt', 'rotate', 'alias'
]


# Make our commands available as though they were part of the distutils

distutils.command.__path__.extend(__path__)
distutils.command.__all__.extend(
    [cmd for cmd in __all__ if cmd not in distutils.command.__all__]
    )

from distutils.command.bdist import bdist

if 'egg' not in bdist.format_commands:
    bdist.format_command['egg'] = ('bdist_egg', "Python .egg file")
    bdist.format_commands.append('egg')

del bdist
