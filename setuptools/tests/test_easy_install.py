"""Easy install Tests
"""
import sys
import os, shutil, tempfile, unittest
from setuptools.command.easy_install import easy_install, get_script_args, main
from setuptools.dist import Distribution

class FakeDist(object):
    def get_entry_map(self, group):
        if group != 'console_scripts':
            return {}
        return {'name': 'ep'}

    def as_requirement(self):
        return 'spec'

WANTED = """\
#!%s
# EASY-INSTALL-ENTRY-SCRIPT: 'spec','console_scripts','name'
__requires__ = 'spec'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('spec', 'console_scripts', 'name')()
    )
""" % sys.executable

SETUP_PY = """\
from setuptools import setup

setup(name='foo')
"""

class TestEasyInstallTest(unittest.TestCase):

    def test_install_site_py(self):
        dist = Distribution()
        cmd = easy_install(dist)
        cmd.sitepy_installed = False
        cmd.install_dir = tempfile.mkdtemp()
        try:
            cmd.install_site_py()
            sitepy = os.path.join(cmd.install_dir, 'site.py')
            self.assert_(os.path.exists(sitepy))
        finally:
            shutil.rmtree(cmd.install_dir)

    def test_get_script_args(self):
        dist = FakeDist()

        old_platform = sys.platform
        try:
            name, script = get_script_args(dist).next()
        finally:
            sys.platform = old_platform

        self.assertEquals(script, WANTED)

    def test_no_setup_cfg(self):
        # makes sure easy_install as a command (main)
        # doesn't use a setup.cfg file that is located
        # in the current working directory
        dir = tempfile.mkdtemp()
        setup_cfg = open(os.path.join(dir, 'setup.cfg'), 'w')
        setup_cfg.write('[easy_install]\nfind_links = http://example.com')
        setup_cfg.close()
        setup_py = open(os.path.join(dir, 'setup.py'), 'w')
        setup_py.write(SETUP_PY)
        setup_py.close()

        from setuptools.dist import Distribution

        def _parse_command_line(self):
            msg = 'Error: a local setup.cfg was used'
            opts = self.command_options
            if 'easy_install' in opts:
                assert 'find_links' not in opts['easy_install'], msg
            return self._old_parse_command_line

        Distribution._old_parse_command_line = Distribution.parse_command_line
        Distribution.parse_command_line = _parse_command_line

        old_wd = os.getcwd()
        try:
            os.chdir(dir)
            main([])
        finally:
            os.chdir(old_wd)
            shutil.rmtree(dir)

