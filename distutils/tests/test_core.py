"""Tests for distutils.core."""

import io
import distutils.core
import os
import shutil
import sys
from test.support import captured_stdout

import pytest

from . import py38compat as os_helper
import unittest
from distutils import log
from distutils.dist import Distribution

# setup script that uses __file__
setup_using___file__ = """\

__file__

from distutils.core import setup
setup()
"""

setup_prints_cwd = """\

import os
print(os.getcwd())

from distutils.core import setup
setup()
"""

setup_does_nothing = """\
from distutils.core import setup
setup()
"""


setup_defines_subclass = """\
from distutils.core import setup
from distutils.command.install import install as _install

class install(_install):
    sub_commands = _install.sub_commands + ['cmd']

setup(cmdclass={'install': install})
"""

setup_within_if_main = """\
from distutils.core import setup

def main():
    return setup(name="setup_within_if_main")

if __name__ == "__main__":
    main()
"""


@pytest.mark.usefixtures('save_env')
@pytest.mark.usefixtures('save_argv')
class CoreTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.old_stdout = sys.stdout
        self.cleanup_testfn()
        self.addCleanup(log.set_threshold, log._global_log.threshold)

    def tearDown(self):
        sys.stdout = self.old_stdout
        self.cleanup_testfn()
        super().tearDown()

    def cleanup_testfn(self):
        path = os_helper.TESTFN
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def write_setup(self, text, path=os_helper.TESTFN):
        f = open(path, "w")
        try:
            f.write(text)
        finally:
            f.close()
        return path

    def test_run_setup_provides_file(self):
        # Make sure the script can use __file__; if that's missing, the test
        # setup.py script will raise NameError.
        distutils.core.run_setup(self.write_setup(setup_using___file__))

    def test_run_setup_preserves_sys_argv(self):
        # Make sure run_setup does not clobber sys.argv
        argv_copy = sys.argv.copy()
        distutils.core.run_setup(self.write_setup(setup_does_nothing))
        assert sys.argv == argv_copy

    def test_run_setup_defines_subclass(self):
        # Make sure the script can use __file__; if that's missing, the test
        # setup.py script will raise NameError.
        dist = distutils.core.run_setup(self.write_setup(setup_defines_subclass))
        install = dist.get_command_obj('install')
        assert 'cmd' in install.sub_commands

    def test_run_setup_uses_current_dir(self):
        # This tests that the setup script is run with the current directory
        # as its own current directory; this was temporarily broken by a
        # previous patch when TESTFN did not use the current directory.
        sys.stdout = io.StringIO()
        cwd = os.getcwd()

        # Create a directory and write the setup.py file there:
        os.mkdir(os_helper.TESTFN)
        setup_py = os.path.join(os_helper.TESTFN, "setup.py")
        distutils.core.run_setup(self.write_setup(setup_prints_cwd, path=setup_py))

        output = sys.stdout.getvalue()
        if output.endswith("\n"):
            output = output[:-1]
        assert cwd == output

    def test_run_setup_within_if_main(self):
        dist = distutils.core.run_setup(
            self.write_setup(setup_within_if_main), stop_after="config"
        )
        assert isinstance(dist, Distribution)
        assert dist.get_name() == "setup_within_if_main"

    def test_run_commands(self):
        sys.argv = ['setup.py', 'build']
        dist = distutils.core.run_setup(
            self.write_setup(setup_within_if_main), stop_after="commandline"
        )
        assert 'build' not in dist.have_run
        distutils.core.run_commands(dist)
        assert 'build' in dist.have_run

    def test_debug_mode(self):
        # this covers the code called when DEBUG is set
        sys.argv = ['setup.py', '--name']
        with captured_stdout() as stdout:
            distutils.core.setup(name='bar')
        stdout.seek(0)
        assert stdout.read() == 'bar\n'

        distutils.core.DEBUG = True
        try:
            with captured_stdout() as stdout:
                distutils.core.setup(name='bar')
        finally:
            distutils.core.DEBUG = False
        stdout.seek(0)
        wanted = "options (after parsing config files):\n"
        assert stdout.readlines()[0] == wanted
