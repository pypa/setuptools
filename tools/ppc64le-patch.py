"""
Except on bionic, Travis Linux base image for PPC64LE
platform lacks the proper
permissions to the directory ~/.cache/pip/wheels that allow
the user running travis build to install pip packages.
TODO: is someone tracking this issue? Maybe just move to bionic?
"""

import subprocess
import collections
import os


def patch():
    env = collections.defaultdict(str, os.environ)
    if env['TRAVIS_CPU_ARCH'] != 'ppc64le':
        return
    cmd = [
        'sudo',
        'chown',
        '-Rfv',
        '{USER}:{GROUP}'.format_map(env),
        os.path.expanduser('~/.cache/pip/wheels'),
    ]
    subprocess.Popen(cmd)


__name__ == '__main__' and patch()
