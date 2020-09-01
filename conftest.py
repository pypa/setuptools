import platform


collect_ignore = []


if platform.system() != 'Windows':
    collect_ignore.extend([
        'distutils/command/bdist_msi.py',
        'distutils/msvc9compiler.py',
    ])
