# coding: utf-8
from __future__ import unicode_literals

import sys
import tempfile
import os
import zipfile
import datetime
import time
import subprocess
import stat
import distutils.dist
import distutils.command.install_egg_info

from pkg_resources.extern.six.moves import map

import pytest

import pkg_resources

try:
    unicode
except NameError:
    unicode = str


def timestamp(dt):
    """
    Return a timestamp for a local, naive datetime instance.
    """
    try:
        return dt.timestamp()
    except AttributeError:
        # Python 3.2 and earlier
        return time.mktime(dt.timetuple())


class EggRemover(unicode):
    def __call__(self):
        if self in sys.path:
            sys.path.remove(self)
        if os.path.exists(self):
            os.remove(self)


class TestZipProvider(object):
    finalizers = []

    ref_time = datetime.datetime(2013, 5, 12, 13, 25, 0)
    "A reference time for a file modification"

    @classmethod
    def setup_class(cls):
        "create a zip egg and add it to sys.path"
        egg = tempfile.NamedTemporaryFile(suffix='.egg', delete=False)
        zip_egg = zipfile.ZipFile(egg, 'w')
        zip_info = zipfile.ZipInfo()
        zip_info.filename = 'mod.py'
        zip_info.date_time = cls.ref_time.timetuple()
        zip_egg.writestr(zip_info, 'x = 3\n')
        zip_info = zipfile.ZipInfo()
        zip_info.filename = 'data.dat'
        zip_info.date_time = cls.ref_time.timetuple()
        zip_egg.writestr(zip_info, 'hello, world!')
        zip_info = zipfile.ZipInfo()
        zip_info.filename = 'subdir/mod2.py'
        zip_info.date_time = cls.ref_time.timetuple()
        zip_egg.writestr(zip_info, 'x = 6\n')
        zip_info = zipfile.ZipInfo()
        zip_info.filename = 'subdir/data2.dat'
        zip_info.date_time = cls.ref_time.timetuple()
        zip_egg.writestr(zip_info, 'goodbye, world!')
        zip_egg.close()
        egg.close()

        sys.path.append(egg.name)
        subdir = os.path.join(egg.name, 'subdir')
        sys.path.append(subdir)
        cls.finalizers.append(EggRemover(subdir))
        cls.finalizers.append(EggRemover(egg.name))

    @classmethod
    def teardown_class(cls):
        for finalizer in cls.finalizers:
            finalizer()

    def test_resource_listdir(self):
        import mod
        zp = pkg_resources.ZipProvider(mod)

        expected_root = ['data.dat', 'mod.py', 'subdir']
        assert sorted(zp.resource_listdir('')) == expected_root
        assert sorted(zp.resource_listdir('/')) == expected_root

        expected_subdir = ['data2.dat', 'mod2.py']
        assert sorted(zp.resource_listdir('subdir')) == expected_subdir
        assert sorted(zp.resource_listdir('subdir/')) == expected_subdir

        assert zp.resource_listdir('nonexistent') == []
        assert zp.resource_listdir('nonexistent/') == []

        import mod2
        zp2 = pkg_resources.ZipProvider(mod2)

        assert sorted(zp2.resource_listdir('')) == expected_subdir
        assert sorted(zp2.resource_listdir('/')) == expected_subdir

        assert zp2.resource_listdir('subdir') == []
        assert zp2.resource_listdir('subdir/') == []

    def test_resource_filename_rewrites_on_change(self):
        """
        If a previous call to get_resource_filename has saved the file, but
        the file has been subsequently mutated with different file of the
        same size and modification time, it should not be overwritten on a
        subsequent call to get_resource_filename.
        """
        import mod
        manager = pkg_resources.ResourceManager()
        zp = pkg_resources.ZipProvider(mod)
        filename = zp.get_resource_filename(manager, 'data.dat')
        actual = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
        assert actual == self.ref_time
        f = open(filename, 'w')
        f.write('hello, world?')
        f.close()
        ts = timestamp(self.ref_time)
        os.utime(filename, (ts, ts))
        filename = zp.get_resource_filename(manager, 'data.dat')
        with open(filename) as f:
            assert f.read() == 'hello, world!'
        manager.cleanup_resources()


class TestResourceManager(object):
    def test_get_cache_path(self):
        mgr = pkg_resources.ResourceManager()
        path = mgr.get_cache_path('foo')
        type_ = str(type(path))
        message = "Unexpected type from get_cache_path: " + type_
        assert isinstance(path, (unicode, str)), message


class TestIndependence:
    """
    Tests to ensure that pkg_resources runs independently from setuptools.
    """

    def test_setuptools_not_imported(self):
        """
        In a separate Python environment, import pkg_resources and assert
        that action doesn't cause setuptools to be imported.
        """
        lines = (
            'import pkg_resources',
            'import sys',
            'assert "setuptools" not in sys.modules, '
                '"setuptools was imported"',
        )
        cmd = [sys.executable, '-c', '; '.join(lines)]
        subprocess.check_call(cmd)


class TestDeepVersionLookupDistutils(object):
    @pytest.fixture
    def env(self, tmpdir):
        """
        Create a package environment, similar to a virtualenv,
        in which packages are installed.
        """

        class Environment(str):
            pass

        env = Environment(tmpdir)
        tmpdir.chmod(stat.S_IRWXU)
        subs = 'home', 'lib', 'scripts', 'data', 'egg-base'
        env.paths = dict(
            (dirname, str(tmpdir / dirname))
            for dirname in subs
        )
        list(map(os.mkdir, env.paths.values()))
        return env

    def create_foo_pkg(self, env, version):
        """
        Create a foo package installed (distutils-style) to env.paths['lib']
        as version.
        """
        ld = "This package has unicode metadata! ❄"
        attrs = dict(name='foo', version=version, long_description=ld)
        dist = distutils.dist.Distribution(attrs)
        iei_cmd = distutils.command.install_egg_info.install_egg_info(dist)
        iei_cmd.initialize_options()
        iei_cmd.install_dir = env.paths['lib']
        iei_cmd.finalize_options()
        iei_cmd.run()

    def test_version_resolved_from_egg_info(self, env):
        version = '1.11.0.dev0+2329eae'
        self.create_foo_pkg(env, version)

        # this requirement parsing will raise a VersionConflict unless the
        # .egg-info file is parsed (see #419 on BitBucket)
        req = pkg_resources.Requirement.parse('foo>=1.9')
        dist = pkg_resources.WorkingSet([env.paths['lib']]).find(req)
        assert dist.version == version
