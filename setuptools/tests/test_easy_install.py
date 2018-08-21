# -*- coding: utf-8 -*-
"""Easy install Tests
"""
from __future__ import absolute_import, unicode_literals

import sys
import os
import tempfile
import site
import contextlib
import tarfile
import logging
import itertools
import distutils.errors
import io
import zipfile
import mock

import time
from setuptools.extern import six
from setuptools.extern.six.moves import urllib

import pytest

from setuptools import sandbox
from setuptools.sandbox import run_setup
import setuptools.command.easy_install as ei
from setuptools.command.easy_install import PthDistributions
from setuptools.command import easy_install as easy_install_pkg
from setuptools.dist import Distribution
from pkg_resources import normalize_path, working_set
from pkg_resources import Distribution as PRDistribution
import setuptools.tests.server
from setuptools.tests import fail_on_ascii
import pkg_resources

from . import contexts
from .textwrap import DALS

__metaclass__ = type


class FakeDist:
    def get_entry_map(self, group):
        if group != 'console_scripts':
            return {}
        return {str('name'): 'ep'}

    def as_requirement(self):
        return 'spec'


SETUP_PY = DALS("""
    from setuptools import setup

    setup(name='foo')
    """)


class TestEasyInstallTest:
    def test_install_site_py(self, tmpdir):
        dist = Distribution()
        cmd = ei.easy_install(dist)
        cmd.sitepy_installed = False
        cmd.install_dir = str(tmpdir)
        cmd.install_site_py()
        assert (tmpdir / 'site.py').exists()

    def test_get_script_args(self):
        header = ei.CommandSpec.best().from_environment().as_header()
        expected = header + DALS(r"""
            # EASY-INSTALL-ENTRY-SCRIPT: 'spec','console_scripts','name'
            __requires__ = 'spec'
            import re
            import sys
            from pkg_resources import load_entry_point

            if __name__ == '__main__':
                sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
                sys.exit(
                    load_entry_point('spec', 'console_scripts', 'name')()
                )
            """)  # noqa: E501
        dist = FakeDist()

        args = next(ei.ScriptWriter.get_args(dist))
        name, script = itertools.islice(args, 2)

        assert script == expected

    def test_no_find_links(self):
        # new option '--no-find-links', that blocks find-links added at
        # the project level
        dist = Distribution()
        cmd = ei.easy_install(dist)
        cmd.check_pth_processing = lambda: True
        cmd.no_find_links = True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        assert cmd.package_index.scanned_urls == {}

        # let's try without it (default behavior)
        cmd = ei.easy_install(dist)
        cmd.check_pth_processing = lambda: True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        keys = sorted(cmd.package_index.scanned_urls.keys())
        assert keys == ['link1', 'link2']

    def test_write_exception(self):
        """
        Test that `cant_write_to_target` is rendered as a DistutilsError.
        """
        dist = Distribution()
        cmd = ei.easy_install(dist)
        cmd.install_dir = os.getcwd()
        with pytest.raises(distutils.errors.DistutilsError):
            cmd.cant_write_to_target()

    def test_all_site_dirs(self, monkeypatch):
        """
        get_site_dirs should always return site dirs reported by
        site.getsitepackages.
        """
        path = normalize_path('/setuptools/test/site-packages')

        def mock_gsp():
            return [path]
        monkeypatch.setattr(site, 'getsitepackages', mock_gsp, raising=False)
        assert path in ei.get_site_dirs()

    def test_all_site_dirs_works_without_getsitepackages(self, monkeypatch):
        monkeypatch.delattr(site, 'getsitepackages', raising=False)
        assert ei.get_site_dirs()

    @pytest.fixture
    def sdist_unicode(self, tmpdir):
        files = [
            (
                'setup.py',
                DALS("""
                    import setuptools
                    setuptools.setup(
                        name="setuptools-test-unicode",
                        version="1.0",
                        packages=["mypkg"],
                        include_package_data=True,
                    )
                    """),
            ),
            (
                'mypkg/__init__.py',
                "",
            ),
            (
                'mypkg/☃.txt',
                "",
            ),
        ]
        sdist_name = 'setuptools-test-unicode-1.0.zip'
        sdist = tmpdir / sdist_name
        # can't use make_sdist, because the issue only occurs
        #  with zip sdists.
        sdist_zip = zipfile.ZipFile(str(sdist), 'w')
        for filename, content in files:
            sdist_zip.writestr(filename, content)
        sdist_zip.close()
        return str(sdist)

    @fail_on_ascii
    def test_unicode_filename_in_sdist(
            self, sdist_unicode, tmpdir, monkeypatch):
        """
        The install command should execute correctly even if
        the package has unicode filenames.
        """
        dist = Distribution({'script_args': ['easy_install']})
        target = (tmpdir / 'target').ensure_dir()
        cmd = ei.easy_install(
            dist,
            install_dir=str(target),
            args=['x'],
        )
        monkeypatch.setitem(os.environ, 'PYTHONPATH', str(target))
        cmd.ensure_finalized()
        cmd.easy_install(sdist_unicode)

    @pytest.fixture
    def sdist_unicode_in_script(self, tmpdir):
        files = [
            (
                "setup.py",
                DALS("""
                    import setuptools
                    setuptools.setup(
                        name="setuptools-test-unicode",
                        version="1.0",
                        packages=["mypkg"],
                        include_package_data=True,
                        scripts=['mypkg/unicode_in_script'],
                    )
                    """),
            ),
            ("mypkg/__init__.py", ""),
            (
                "mypkg/unicode_in_script",
                DALS(
                    """
                    #!/bin/sh
                    # á

                    non_python_fn() {
                    }
                """),
            ),
        ]
        sdist_name = "setuptools-test-unicode-script-1.0.zip"
        sdist = tmpdir / sdist_name
        # can't use make_sdist, because the issue only occurs
        #  with zip sdists.
        sdist_zip = zipfile.ZipFile(str(sdist), "w")
        for filename, content in files:
            sdist_zip.writestr(filename, content.encode('utf-8'))
        sdist_zip.close()
        return str(sdist)

    @fail_on_ascii
    def test_unicode_content_in_sdist(
            self, sdist_unicode_in_script, tmpdir, monkeypatch):
        """
        The install command should execute correctly even if
        the package has unicode in scripts.
        """
        dist = Distribution({"script_args": ["easy_install"]})
        target = (tmpdir / "target").ensure_dir()
        cmd = ei.easy_install(dist, install_dir=str(target), args=["x"])
        monkeypatch.setitem(os.environ, "PYTHONPATH", str(target))
        cmd.ensure_finalized()
        cmd.easy_install(sdist_unicode_in_script)

    @pytest.fixture
    def sdist_script(self, tmpdir):
        files = [
            (
                'setup.py',
                DALS("""
                    import setuptools
                    setuptools.setup(
                        name="setuptools-test-script",
                        version="1.0",
                        scripts=["mypkg_script"],
                    )
                    """),
            ),
            (
                'mypkg_script',
                DALS("""
                     #/usr/bin/python
                     print('mypkg_script')
                     """),
            ),
        ]
        sdist_name = 'setuptools-test-script-1.0.zip'
        sdist = str(tmpdir / sdist_name)
        make_sdist(sdist, files)
        return sdist

    @pytest.mark.skipif(not sys.platform.startswith('linux'),
                        reason="Test can only be run on Linux")
    def test_script_install(self, sdist_script, tmpdir, monkeypatch):
        """
        Check scripts are installed.
        """
        dist = Distribution({'script_args': ['easy_install']})
        target = (tmpdir / 'target').ensure_dir()
        cmd = ei.easy_install(
            dist,
            install_dir=str(target),
            args=['x'],
        )
        monkeypatch.setitem(os.environ, 'PYTHONPATH', str(target))
        cmd.ensure_finalized()
        cmd.easy_install(sdist_script)
        assert (target / 'mypkg_script').exists()


class TestPTHFileWriter:
    def test_add_from_cwd_site_sets_dirty(self):
        '''a pth file manager should set dirty
        if a distribution is in site but also the cwd
        '''
        pth = PthDistributions('does-not_exist', [os.getcwd()])
        assert not pth.dirty
        pth.add(PRDistribution(os.getcwd()))
        assert pth.dirty

    def test_add_from_site_is_ignored(self):
        location = '/test/location/does-not-have-to-exist'
        # PthDistributions expects all locations to be normalized
        location = pkg_resources.normalize_path(location)
        pth = PthDistributions('does-not_exist', [location, ])
        assert not pth.dirty
        pth.add(PRDistribution(location))
        assert not pth.dirty


@pytest.yield_fixture
def setup_context(tmpdir):
    with (tmpdir / 'setup.py').open('w') as f:
        f.write(SETUP_PY)
    with tmpdir.as_cwd():
        yield tmpdir


@pytest.mark.usefixtures("user_override")
@pytest.mark.usefixtures("setup_context")
class TestUserInstallTest:

    # prevent check that site-packages is writable. easy_install
    # shouldn't be writing to system site-packages during finalize
    # options, but while it does, bypass the behavior.
    prev_sp_write = mock.patch(
        'setuptools.command.easy_install.easy_install.check_site_dir',
        mock.Mock(),
    )

    # simulate setuptools installed in user site packages
    @mock.patch('setuptools.command.easy_install.__file__', site.USER_SITE)
    @mock.patch('site.ENABLE_USER_SITE', True)
    @prev_sp_write
    def test_user_install_not_implied_user_site_enabled(self):
        self.assert_not_user_site()

    @mock.patch('site.ENABLE_USER_SITE', False)
    @prev_sp_write
    def test_user_install_not_implied_user_site_disabled(self):
        self.assert_not_user_site()

    @staticmethod
    def assert_not_user_site():
        # create a finalized easy_install command
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = ei.easy_install(dist)
        cmd.args = ['py']
        cmd.ensure_finalized()
        assert not cmd.user, 'user should not be implied'

    def test_multiproc_atexit(self):
        pytest.importorskip('multiprocessing')

        log = logging.getLogger('test_easy_install')
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
        log.info('this should not break')

    @pytest.fixture()
    def foo_package(self, tmpdir):
        egg_file = tmpdir / 'foo-1.0.egg-info'
        with egg_file.open('w') as f:
            f.write('Name: foo\n')
        return str(tmpdir)

    @pytest.yield_fixture()
    def install_target(self, tmpdir):
        target = str(tmpdir)
        with mock.patch('sys.path', sys.path + [target]):
            python_path = os.path.pathsep.join(sys.path)
            with mock.patch.dict(os.environ, PYTHONPATH=python_path):
                yield target

    def test_local_index(self, foo_package, install_target):
        """
        The local index must be used when easy_install locates installed
        packages.
        """
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = ei.easy_install(dist)
        cmd.install_dir = install_target
        cmd.args = ['foo']
        cmd.ensure_finalized()
        cmd.local_index.scan([foo_package])
        res = cmd.easy_install('foo')
        actual = os.path.normcase(os.path.realpath(res.location))
        expected = os.path.normcase(os.path.realpath(foo_package))
        assert actual == expected

    @contextlib.contextmanager
    def user_install_setup_context(self, *args, **kwargs):
        """
        Wrap sandbox.setup_context to patch easy_install in that context to
        appear as user-installed.
        """
        with self.orig_context(*args, **kwargs):
            import setuptools.command.easy_install as ei
            ei.__file__ = site.USER_SITE
            yield

    def patched_setup_context(self):
        self.orig_context = sandbox.setup_context

        return mock.patch(
            'setuptools.sandbox.setup_context',
            self.user_install_setup_context,
        )


@pytest.yield_fixture
def distutils_package():
    distutils_setup_py = SETUP_PY.replace(
        'from setuptools import setup',
        'from distutils.core import setup',
    )
    with contexts.tempdir(cd=os.chdir):
        with open('setup.py', 'w') as f:
            f.write(distutils_setup_py)
        yield


class TestDistutilsPackage:
    def test_bdist_egg_available_on_distutils_pkg(self, distutils_package):
        run_setup('setup.py', ['bdist_egg'])


class TestSetupRequires:
    def test_setup_requires_honors_fetch_params(self):
        """
        When easy_install installs a source distribution which specifies
        setup_requires, it should honor the fetch parameters (such as
        allow-hosts, index-url, and find-links).
        """
        # set up a server which will simulate an alternate package index.
        p_index = setuptools.tests.server.MockServer()
        p_index.start()
        netloc = 1
        p_index_loc = urllib.parse.urlparse(p_index.url)[netloc]
        if p_index_loc.endswith(':0'):
            # Some platforms (Jython) don't find a port to which to bind,
            #  so skip this test for them.
            return
        with contexts.quiet():
            # create an sdist that has a build-time dependency.
            with TestSetupRequires.create_sdist() as dist_file:
                with contexts.tempdir() as temp_install_dir:
                    with contexts.environment(PYTHONPATH=temp_install_dir):
                        ei_params = [
                            '--index-url', p_index.url,
                            '--allow-hosts', p_index_loc,
                            '--exclude-scripts',
                            '--install-dir', temp_install_dir,
                            dist_file,
                        ]
                        with sandbox.save_argv(['easy_install']):
                            # attempt to install the dist. It should
                            # fail because it doesn't exist.
                            with pytest.raises(SystemExit):
                                easy_install_pkg.main(ei_params)
        # there should have been two or three requests to the server
        #  (three happens on Python 3.3a)
        assert 2 <= len(p_index.requests) <= 3
        assert p_index.requests[0].path == '/does-not-exist/'

    @staticmethod
    @contextlib.contextmanager
    def create_sdist():
        """
        Return an sdist with a setup_requires dependency (of something that
        doesn't exist)
        """
        with contexts.tempdir() as dir:
            dist_path = os.path.join(dir, 'setuptools-test-fetcher-1.0.tar.gz')
            make_sdist(dist_path, [
                ('setup.py', DALS("""
                    import setuptools
                    setuptools.setup(
                        name="setuptools-test-fetcher",
                        version="1.0",
                        setup_requires = ['does-not-exist'],
                    )
                """))])
            yield dist_path

    use_setup_cfg = (
        (),
        ('dependency_links',),
        ('setup_requires',),
        ('dependency_links', 'setup_requires'),
    )

    @pytest.mark.parametrize('use_setup_cfg', use_setup_cfg)
    def test_setup_requires_overrides_version_conflict(self, use_setup_cfg):
        """
        Regression test for distribution issue 323:
        https://bitbucket.org/tarek/distribute/issues/323

        Ensures that a distribution's setup_requires requirements can still be
        installed and used locally even if a conflicting version of that
        requirement is already on the path.
        """

        fake_dist = PRDistribution('does-not-matter', project_name='foobar',
                                   version='0.0')
        working_set.add(fake_dist)

        with contexts.save_pkg_resources_state():
            with contexts.tempdir() as temp_dir:
                test_pkg = create_setup_requires_package(
                    temp_dir, use_setup_cfg=use_setup_cfg)
                test_setup_py = os.path.join(test_pkg, 'setup.py')
                with contexts.quiet() as (stdout, stderr):
                    # Don't even need to install the package, just
                    # running the setup.py at all is sufficient
                    run_setup(test_setup_py, [str('--name')])

                lines = stdout.readlines()
                assert len(lines) > 0
                assert lines[-1].strip() == 'test_pkg'

    @pytest.mark.parametrize('use_setup_cfg', use_setup_cfg)
    def test_setup_requires_override_nspkg(self, use_setup_cfg):
        """
        Like ``test_setup_requires_overrides_version_conflict`` but where the
        ``setup_requires`` package is part of a namespace package that has
        *already* been imported.
        """

        with contexts.save_pkg_resources_state():
            with contexts.tempdir() as temp_dir:
                foobar_1_archive = os.path.join(temp_dir, 'foo.bar-0.1.tar.gz')
                make_nspkg_sdist(foobar_1_archive, 'foo.bar', '0.1')
                # Now actually go ahead an extract to the temp dir and add the
                # extracted path to sys.path so foo.bar v0.1 is importable
                foobar_1_dir = os.path.join(temp_dir, 'foo.bar-0.1')
                os.mkdir(foobar_1_dir)
                with tarfile.open(foobar_1_archive) as tf:
                    tf.extractall(foobar_1_dir)
                sys.path.insert(1, foobar_1_dir)

                dist = PRDistribution(foobar_1_dir, project_name='foo.bar',
                                      version='0.1')
                working_set.add(dist)

                template = DALS("""\
                    import foo  # Even with foo imported first the
                                # setup_requires package should override
                    import setuptools
                    setuptools.setup(**%r)

                    if not (hasattr(foo, '__path__') and
                            len(foo.__path__) == 2):
                        print('FAIL')

                    if 'foo.bar-0.2' not in foo.__path__[0]:
                        print('FAIL')
                """)

                test_pkg = create_setup_requires_package(
                    temp_dir, 'foo.bar', '0.2', make_nspkg_sdist, template,
                    use_setup_cfg=use_setup_cfg)

                test_setup_py = os.path.join(test_pkg, 'setup.py')

                with contexts.quiet() as (stdout, stderr):
                    try:
                        # Don't even need to install the package, just
                        # running the setup.py at all is sufficient
                        run_setup(test_setup_py, [str('--name')])
                    except pkg_resources.VersionConflict:
                        self.fail(
                            'Installing setup.py requirements '
                            'caused a VersionConflict')

                assert 'FAIL' not in stdout.getvalue()
                lines = stdout.readlines()
                assert len(lines) > 0
                assert lines[-1].strip() == 'test_pkg'

    @pytest.mark.parametrize('use_setup_cfg', use_setup_cfg)
    def test_setup_requires_with_attr_version(self, use_setup_cfg):
        def make_dependency_sdist(dist_path, distname, version):
            files = [(
                'setup.py',
                DALS("""
                    import setuptools
                    setuptools.setup(
                        name={name!r},
                        version={version!r},
                        py_modules=[{name!r}],
                    )
                    """.format(name=distname, version=version)),
            ), (
                distname + '.py',
                DALS("""
                    version = 42
                    """),
            )]
            make_sdist(dist_path, files)
        with contexts.save_pkg_resources_state():
            with contexts.tempdir() as temp_dir:
                test_pkg = create_setup_requires_package(
                    temp_dir, setup_attrs=dict(version='attr: foobar.version'),
                    make_package=make_dependency_sdist,
                    use_setup_cfg=use_setup_cfg+('version',),
                )
                test_setup_py = os.path.join(test_pkg, 'setup.py')
                with contexts.quiet() as (stdout, stderr):
                    run_setup(test_setup_py, [str('--version')])
                lines = stdout.readlines()
                assert len(lines) > 0
                assert lines[-1].strip() == '42'


def make_trivial_sdist(dist_path, distname, version):
    """
    Create a simple sdist tarball at dist_path, containing just a simple
    setup.py.
    """

    make_sdist(dist_path, [
        ('setup.py',
         DALS("""\
             import setuptools
             setuptools.setup(
                 name=%r,
                 version=%r
             )
         """ % (distname, version)))])


def make_nspkg_sdist(dist_path, distname, version):
    """
    Make an sdist tarball with distname and version which also contains one
    package with the same name as distname.  The top-level package is
    designated a namespace package).
    """

    parts = distname.split('.')
    nspackage = parts[0]

    packages = ['.'.join(parts[:idx]) for idx in range(1, len(parts) + 1)]

    setup_py = DALS("""\
        import setuptools
        setuptools.setup(
            name=%r,
            version=%r,
            packages=%r,
            namespace_packages=[%r]
        )
    """ % (distname, version, packages, nspackage))

    init = "__import__('pkg_resources').declare_namespace(__name__)"

    files = [('setup.py', setup_py),
             (os.path.join(nspackage, '__init__.py'), init)]
    for package in packages[1:]:
        filename = os.path.join(*(package.split('.') + ['__init__.py']))
        files.append((filename, ''))

    make_sdist(dist_path, files)


def make_sdist(dist_path, files):
    """
    Create a simple sdist tarball at dist_path, containing the files
    listed in ``files`` as ``(filename, content)`` tuples.
    """

    with tarfile.open(dist_path, 'w:gz') as dist:
        for filename, content in files:
            file_bytes = io.BytesIO(content.encode('utf-8'))
            file_info = tarfile.TarInfo(name=filename)
            file_info.size = len(file_bytes.getvalue())
            file_info.mtime = int(time.time())
            dist.addfile(file_info, fileobj=file_bytes)


def create_setup_requires_package(path, distname='foobar', version='0.1',
                                  make_package=make_trivial_sdist,
                                  setup_py_template=None, setup_attrs={},
                                  use_setup_cfg=()):
    """Creates a source tree under path for a trivial test package that has a
    single requirement in setup_requires--a tarball for that requirement is
    also created and added to the dependency_links argument.

    ``distname`` and ``version`` refer to the name/version of the package that
    the test package requires via ``setup_requires``.  The name of the test
    package itself is just 'test_pkg'.
    """

    test_setup_attrs = {
        'name': 'test_pkg', 'version': '0.0',
        'setup_requires': ['%s==%s' % (distname, version)],
        'dependency_links': [os.path.abspath(path)]
    }
    test_setup_attrs.update(setup_attrs)

    test_pkg = os.path.join(path, 'test_pkg')
    os.mkdir(test_pkg)

    if use_setup_cfg:
        test_setup_cfg = os.path.join(test_pkg, 'setup.cfg')
        options = []
        metadata = []
        for name in use_setup_cfg:
            value = test_setup_attrs.pop(name)
            if name in 'name version'.split():
                section = metadata
            else:
                section = options
            if isinstance(value, (tuple, list)):
                value = ';'.join(value)
            section.append('%s: %s' % (name, value))
        with open(test_setup_cfg, 'w') as f:
            f.write(DALS(
                """
                [metadata]
                {metadata}
                [options]
                {options}
                """
            ).format(
                options='\n'.join(options),
                metadata='\n'.join(metadata),
            ))

    test_setup_py = os.path.join(test_pkg, 'setup.py')

    if setup_py_template is None:
        setup_py_template = DALS("""\
            import setuptools
            setuptools.setup(**%r)
        """)
    with open(test_setup_py, 'w') as f:
        f.write(setup_py_template % test_setup_attrs)

    foobar_path = os.path.join(path, '%s-%s.tar.gz' % (distname, version))
    make_package(foobar_path, distname, version)

    return test_pkg


@pytest.mark.skipif(
    sys.platform.startswith('java') and ei.is_sh(sys.executable),
    reason="Test cannot run under java when executable is sh"
)
class TestScriptHeader:
    non_ascii_exe = '/Users/José/bin/python'
    if six.PY2:
        non_ascii_exe = non_ascii_exe.encode('utf-8')
    exe_with_spaces = r'C:\Program Files\Python36\python.exe'

    def test_get_script_header(self):
        expected = '#!%s\n' % ei.nt_quote_arg(os.path.normpath(sys.executable))
        actual = ei.ScriptWriter.get_script_header('#!/usr/local/bin/python')
        assert actual == expected

    def test_get_script_header_args(self):
        expected = '#!%s -x\n' % ei.nt_quote_arg(
            os.path.normpath(sys.executable))
        actual = ei.ScriptWriter.get_script_header('#!/usr/bin/python -x')
        assert actual == expected

    def test_get_script_header_non_ascii_exe(self):
        actual = ei.ScriptWriter.get_script_header(
            '#!/usr/bin/python',
            executable=self.non_ascii_exe)
        expected = str('#!%s -x\n') % self.non_ascii_exe
        assert actual == expected

    def test_get_script_header_exe_with_spaces(self):
        actual = ei.ScriptWriter.get_script_header(
            '#!/usr/bin/python',
            executable='"' + self.exe_with_spaces + '"')
        expected = '#!"%s"\n' % self.exe_with_spaces
        assert actual == expected


class TestCommandSpec:
    def test_custom_launch_command(self):
        """
        Show how a custom CommandSpec could be used to specify a #! executable
        which takes parameters.
        """
        cmd = ei.CommandSpec(['/usr/bin/env', 'python3'])
        assert cmd.as_header() == '#!/usr/bin/env python3\n'

    def test_from_param_for_CommandSpec_is_passthrough(self):
        """
        from_param should return an instance of a CommandSpec
        """
        cmd = ei.CommandSpec(['python'])
        cmd_new = ei.CommandSpec.from_param(cmd)
        assert cmd is cmd_new

    @mock.patch('sys.executable', TestScriptHeader.exe_with_spaces)
    @mock.patch.dict(os.environ)
    def test_from_environment_with_spaces_in_executable(self):
        os.environ.pop('__PYVENV_LAUNCHER__', None)
        cmd = ei.CommandSpec.from_environment()
        assert len(cmd) == 1
        assert cmd.as_header().startswith('#!"')

    def test_from_simple_string_uses_shlex(self):
        """
        In order to support `executable = /usr/bin/env my-python`, make sure
        from_param invokes shlex on that input.
        """
        cmd = ei.CommandSpec.from_param('/usr/bin/env my-python')
        assert len(cmd) == 2
        assert '"' not in cmd.as_header()


class TestWindowsScriptWriter:
    def test_header(self):
        hdr = ei.WindowsScriptWriter.get_script_header('')
        assert hdr.startswith('#!')
        assert hdr.endswith('\n')
        hdr = hdr.lstrip('#!')
        hdr = hdr.rstrip('\n')
        # header should not start with an escaped quote
        assert not hdr.startswith('\\"')
