"""Easy install Tests
"""
import sys
import os, shutil, tempfile, unittest
import site
from StringIO import StringIO
from setuptools.command.easy_install import easy_install, get_script_args, main
from setuptools.command.easy_install import  PthDistributions
from setuptools.command import easy_install as easy_install_pkg
from setuptools.dist import Distribution
from pkg_resources import Distribution as PRDistribution

try:
    import multiprocessing
    import logging
    _LOG = logging.getLogger('test_easy_install')
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    _MULTIPROC = True
except ImportError:
    _MULTIPROC = False
    _LOG = None

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
            name, script = [i for i in get_script_args(dist).next()][0:2]
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

    def test_no_find_links(self):
        # new option '--no-find-links', that blocks find-links added at
        # the project level
        dist = Distribution()
        cmd = easy_install(dist)
        cmd.check_pth_processing = lambda : True
        cmd.no_find_links = True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        self.assertEquals(cmd.package_index.scanned_urls, {})

        # let's try without it (default behavior)
        cmd = easy_install(dist)
        cmd.check_pth_processing = lambda : True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        keys = cmd.package_index.scanned_urls.keys()
        keys.sort()
        self.assertEquals(keys, ['link1', 'link2'])


class TestPTHFileWriter(unittest.TestCase):
    def test_add_from_cwd_site_sets_dirty(self):
        '''a pth file manager should set dirty
        if a distribution is in site but also the cwd
        '''
        pth = PthDistributions('does-not_exist', [os.getcwd()])
        self.assert_(not pth.dirty)
        pth.add(PRDistribution(os.getcwd()))
        self.assert_(pth.dirty)

    def test_add_from_site_is_ignored(self):
        if os.name != 'nt':
            location = '/test/location/does-not-have-to-exist'
        else:
            location = 'c:\\does_not_exist'
        pth = PthDistributions('does-not_exist', [location, ])
        self.assert_(not pth.dirty)
        pth.add(PRDistribution(location))
        self.assert_(not pth.dirty)


class TestUserInstallTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        setup = os.path.join(self.dir, 'setup.py')
        f = open(setup, 'w')
        f.write(SETUP_PY)
        f.close()
        self.old_cwd = os.getcwd()
        os.chdir(self.dir)
        if sys.version >= "2.6":
            self.old_has_site = easy_install_pkg.HAS_USER_SITE
            self.old_file = easy_install_pkg.__file__
            self.old_base = site.USER_BASE
            site.USER_BASE = tempfile.mkdtemp()
            self.old_site = site.USER_SITE
            site.USER_SITE = tempfile.mkdtemp()
            easy_install_pkg.__file__ = site.USER_SITE

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.dir)
        if sys.version >=  "2.6":
            shutil.rmtree(site.USER_BASE)
            shutil.rmtree(site.USER_SITE)
            site.USER_BASE = self.old_base
            site.USER_SITE = self.old_site
            easy_install_pkg.HAS_USER_SITE = self.old_has_site
            easy_install_pkg.__file__ = self.old_file

    def test_user_install_implied(self):
        easy_install_pkg.HAS_USER_SITE = True # disabled sometimes
        #XXX: replace with something meaningfull
        if sys.version < "2.6":
            return #SKIP
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = easy_install(dist)
        cmd.args = ['py']
        cmd.ensure_finalized()
        self.assertTrue(cmd.user, 'user should be implied')

    def test_multiproc_atexit(self):
        if not _MULTIPROC:
            return
        _LOG.info('this should not break')

    def test_user_install_not_implied_without_usersite_enabled(self):
        easy_install_pkg.HAS_USER_SITE = False # usually enabled
        #XXX: replace with something meaningfull
        if sys.version < "2.6":
            return #SKIP
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = easy_install(dist)
        cmd.args = ['py']
        cmd.initialize_options()
        self.assertFalse(cmd.user, 'NOT user should be implied')

    def test_local_index(self):
        # make sure the local index is used
        # when easy_install looks for installed
        # packages
        new_location = tempfile.mkdtemp()
        target = tempfile.mkdtemp()
        egg_file = os.path.join(new_location, 'foo-1.0.egg-info')
        f = open(egg_file, 'w')
        try:
            f.write('Name: foo\n')
        except:
            f.close()

        sys.path.append(target)
        old_ppath = os.environ.get('PYTHONPATH')
        os.environ['PYTHONPATH'] = os.path.pathsep.join(sys.path)
        try:
            dist = Distribution()
            dist.script_name = 'setup.py'
            cmd = easy_install(dist)
            cmd.install_dir = target
            cmd.args = ['foo']
            cmd.ensure_finalized()
            cmd.local_index.scan([new_location])
            res = cmd.easy_install('foo')
            self.assertEquals(res.location, new_location)
        finally:
            sys.path.remove(target)
            for basedir in [new_location, target, ]:
                if not os.path.exists(basedir) or not os.path.isdir(basedir):
                    continue
                try:
                    shutil.rmtree(basedir)
                except:
                    pass
            if old_ppath is not None:
                os.environ['PYTHONPATH'] = old_ppath
            else:
                del os.environ['PYTHONPATH']

