__all__ = [
    'alias', 'bdist_egg', 'bdist_rpm', 'build_ext', 'build_py', 'develop',
    'easy_install', 'egg_info', 'install', 'install_lib', 'rotate', 'saveopts',
    'sdist', 'setopt', 'test', 'upload', 'install_egg_info',
]


from distutils.command.bdist import bdist

if 'egg' not in bdist.format_commands:
    bdist.format_command['egg'] = ('bdist_egg', "Python .egg file")
    bdist.format_commands.append('egg')

del bdist
