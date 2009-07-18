##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Bootstrap a buildout-based project

Simply run this script in a directory containing a buildout.cfg.
The script accepts buildout command-line options, so you can
use the -c option to specify an alternate configuration file.

$Id: bootstrap.py 101222 2009-06-22 14:05:44Z jim $
"""

import os, shutil, sys, tempfile, urllib2

tmpeggs = tempfile.mkdtemp()

is_jython = sys.platform.startswith('java')

try:
    import pkg_resources
except ImportError:
    ez = {}
    # CHANGED: The following was adjusted to use the distribute ez_setup.py
    # instead of the regular setuptools one.
    #
    # exec urllib2.urlopen('http://peak.telecommunity.com/dist/ez_setup.py'
    #                      ).read() in ez
    exec urllib2.urlopen(
        'http://cdn.bitbucket.org/tarek/distribute/downloads/ez_setup.py'
    ).read() in ez
    ez['use_setuptools'](to_dir=tmpeggs, download_delay=0)

    import pkg_resources

if sys.platform == 'win32':
    def quote(c):
        if ' ' in c:
            return '"%s"' % c # work around spawn lamosity on windows
        else:
            return c
else:
    def quote (c):
        return c

cmd = 'from setuptools.command.easy_install import main; main()'
ws  = pkg_resources.working_set

if len(sys.argv) > 2 and sys.argv[1] == '--version':
    VERSION = '==%s' % sys.argv[2]
    args = sys.argv[3:] + ['bootstrap']
else:
    VERSION = ''
    args = sys.argv[1:] + ['bootstrap']

if is_jython:
    import subprocess

    assert subprocess.Popen([sys.executable] + ['-c', quote(cmd), '-mqNxd',
           quote(tmpeggs), 'zc.buildout' + VERSION],
           env=dict(os.environ,
               PYTHONPATH=
               ws.find(pkg_resources.Requirement.parse('setuptools')).location
               ),
           ).wait() == 0

else:
    assert os.spawnle(
        os.P_WAIT, sys.executable, quote (sys.executable),
        '-c', quote (cmd), '-mqNxd', quote (tmpeggs), 'zc.buildout' + VERSION,
        dict(os.environ,
            PYTHONPATH=
            ws.find(pkg_resources.Requirement.parse('setuptools')).location
            ),
        ) == 0

ws.add_entry(tmpeggs)
ws.require('zc.buildout' + VERSION)
import zc.buildout.buildout
zc.buildout.buildout.main(args)
shutil.rmtree(tmpeggs)
