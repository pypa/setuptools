"""
Wrap the pip command to:

- Avoid the default 'python -m pip' invocation, which causes the current
  working directory to be added to the path, which causes problems.
- Ensure pip meets a requisite version.
"""


import sys
import subprocess


def ensure_pip_version(pip_bin, ver):
    """
    Ensure the pip version meets the specified version.

    Use python -m pip to upgrade/downgrade, because for this operation,
    on Windows, pip.exe must not be locked.
    """
    cmd = [sys.executable, '-m', 'pip', 'install', 'pip ' + ver]
    subprocess.check_call(cmd)


def main():
    pip_bin = sys.argv[1]
    # workaround for #1644
    ensure_pip_version(pip_bin, '<19')
    cmd = sys.argv[1:]
    subprocess.check_call(cmd)


__name__ == '__main__' and main()
