"""Easy install Tests
"""
import sys
import os
import shutil
import tempfile
import unittest
import site
import contextlib
import textwrap

from setuptools.command.easy_install import easy_install, get_script_args, main
from setuptools.command.easy_install import  PthDistributions
from setuptools.command import easy_install as easy_install_pkg
from setuptools.dist import Distribution
from pkg_resources import Distribution as PRDistribution
import setuptools.tests.server

try:
    # import multiprocessing solely for the purpose of testing its existence
    __import__('multiprocessing')
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
        cmd.check_pth_processing = lambda: True
        cmd.no_find_links = True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        self.assertEquals(cmd.package_index.scanned_urls, {})

        # let's try without it (default behavior)
        cmd = easy_install(dist)
        cmd.check_pth_processing = lambda: True
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
        if sys.version >= "2.6":
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


class TestSetupRequires(unittest.TestCase):

    def test_setup_requires_honors_fetch_params(self):
        """
        When easy_install installs a source distribution which specifies
        setup_requires, it should honor the fetch parameters (such as
        allow-hosts, index-url, and find-links).
        """
        # set up a server which will simulate an alternate package index.
        p_index = setuptools.tests.server.MockServer()
        p_index.handle_request_in_thread()
        # create an sdist that has a build-time dependency.
        with TestSetupRequires.create_sdist() as dist_file:
            with tempdir_context() as temp_install_dir:
                with environment_context(PYTHONPATH=temp_install_dir):
                    ei_params = ['--index-url', p_index.url,
                        '--allow-hosts', 'localhost',
                        '--exclude-scripts', '--install-dir', temp_install_dir,
                        dist_file]
                    # attempt to install the dist. It will fail because
                    #  our fake server can't actually supply the dependency
                    try:
                        easy_install_pkg.main(ei_params)
                    except Exception:
                        pass
                #self.assertTrue(os.listdir(temp_install_dir))
        self.assertEqual(len(p_index.requests), 1)
        self.assertEqual(p_index.requests[0].path, 'x')

    @staticmethod
    @contextlib.contextmanager
    def create_sdist():
        """
        Return an sdist generated by self.generate_dist()

        We don't generate it dynamically, because we don't want the test suite
        to have to connect to the network for the setup_requires declaration
        just to build the sdist.
        """
        with tempdir_context() as d:
            dist_path = os.path.join(d, 'distribute-test-fetcher-1.0.tar.gz')
            with open(dist_path, 'wb') as dist:
                dist.write("""
                    H4sICLBagE8C/2Rpc3RcZGlzdHJpYnV0ZS10ZXN0LWZldGNoZXItMS4wLnRhcgDtmNtvmzAUh/Ns
                    Kf+DlZduUkmBYJAi5WHaXd2SqlG7h6pCNJwQa9xmm2j57+eQaqGpktKt0F3O9wI+XCJy/JmfCLlU
                    gt8UCgwFUhlzULMFCMPqmyedJ8LUeJ5XbjW723LfsjzHNBmzXV23HJuxDmWdFiikCgSlT/KQ1Yf7
                    SwgP9H97zF8f82+P9SGKDJ7Os5Om+m/brutg///4/oeQQxpCOlv5MU+/yr76rvb8Na7rHui/te0/
                    0/PEdvWgQ03sf+OQDvI/81v+n52+Nz6O301qqHHI/4HFdvwfePp09L8FPoMKwkAFxiUIybN0SHXn
                    u2QcJDCkeyZHl9w9eVokSSBWQ3oxPh1Pvoy75EOWgJEHEVRqrwq1yMS9ggFJwONK+ROfQSqrV74B
                    ORM8V+Uv/qyexYGaZyKplFDndv2fTi7OX7+d7nnt1/ffdHb8dxgboP9tIEEVeT9fkdqLPXnMtCC/
                    lCEfvkpluR/DEuKH5h7SoP81u/D4/M8cC/3H/I88q/81430tNWrn//L7HxswC/3H/I/5/zn932TD
                    2Txq2H/r3vd/13QZ+t8GVzrM+eswd90lKoj8m4LHIR3RzUivDKAH5mYkl6kvYMnX6m+qqNy/73++
                    avr9b3ne3fyv/Tdt9L8NeJJnQtGy1SrLYkm2u/1y9wWhmlQHglFvz2zpHZfnLDepYNTTk+e2VN5B
                    LxrfCi5A6kXj6mgRlTc/uj4mL3H5QBAEQRAEaZsfEynDsQAoAAA=
                    """.decode('base64'))
            yield dist_path

    @classmethod
    def generate_sdist(cls):
        """
        generate the sdist suitable for create_sdist
        """
        with tempdir_context(cd=os.chdir):
            with open('setup.py', 'wb') as setup_script:
                setup_script.write(textwrap.dedent("""
                    import setuptools
                    setuptools.setup(
                        name="distribute-test-fetcher",
                        version="1.0",
                        setup_requires = ['hgtools'],
                    )
                    """).lstrip())
            with argv_context(['setup.py', 'sdist', '-q', '--formats', 'gztar']):
                setuptools.setup(
                    name="distribute-test-fetcher",
                    version = "1.0",
                    setup_requires = ['hgtools'],
                )
            filename = 'distribute-test-fetcher-1.0.tar.gz'
            dist = os.path.join('dist', filename)
            assert os.path.isfile(dist)
            with open(dist, 'rb') as dist_f:
                print("=====================")
                print(dist_f.read().encode('base64'))

@contextlib.contextmanager
def argv_context(repl):
    old_argv = sys.argv[:]
    sys.argv[:] = repl
    yield
    sys.argv[:] = old_argv

@contextlib.contextmanager
def tempdir_context(cd=lambda dir:None):
    temp_dir = tempfile.mkdtemp()
    orig_dir = os.getcwd()
    try:
        cd(temp_dir)
        yield temp_dir
    finally:
        cd(orig_dir)
        shutil.rmtree(temp_dir)

@contextlib.contextmanager
def environment_context(**updates):
    old_env = os.environ.copy()
    os.environ.update(updates)
    try:
        yield
    finally:
        for key in updates:
            del os.environ[key]
        os.environ.update(old_env)
