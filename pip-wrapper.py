"""
Wrap the pip command to:

- Avoid the default 'python -m pip' invocation, which causes the current
  working directory to be added to the path, which causes problems.
"""


import sys
import subprocess


def main():
    cmd = sys.argv[1:]
    subprocess.check_call(cmd)


__name__ == '__main__' and main()
