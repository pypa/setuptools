# -*- coding: utf-8 -*-
"""sdist tests"""

import contextlib
import os
import shutil
import sys
import tempfile

from setuptools.command.egg_info import egg_info
from setuptools.dist import Distribution
from setuptools.extern import six
from setuptools.tests.textwrap import DALS

import pytest

py3_only = pytest.mark.xfail(six.PY2, reason="Test runs on Python 3 only")


def make_local_path(s):
    """Converts '/' in a string to os.sep"""
    return s.replace('/', os.sep)


SETUP_ATTRS = {
    'name': 'app',
    'version': '0.0',
    'packages': ['app'],
}


SETUP_PY = """\
from setuptools import setup

setup(**%r)
""" % SETUP_ATTRS


@contextlib.contextmanager
def quiet():
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = six.StringIO(), six.StringIO()
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


def touch(filename):
    open(filename, 'w').close()

# The set of files always in the manifest, including all files in the
# .egg-info directory
default_files = frozenset(map(make_local_path, [
    'README.rst',
    'MANIFEST.in',
    'setup.py',
    'app.egg-info/PKG-INFO',
    'app.egg-info/SOURCES.txt',
    'app.egg-info/dependency_links.txt',
    'app.egg-info/top_level.txt',
    'app/__init__.py',
]))


class TestManifestTest:

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp()
        f = open(os.path.join(self.temp_dir, 'setup.py'), 'w')
        f.write(SETUP_PY)
        f.close()

        """
        Create a file tree like:
        - LICENSE
        - README.rst
        - testing.rst
        - .hidden.rst
        - app/
            - __init__.py
            - a.txt
            - b.txt
            - c.rst
            - static/
                - app.js
                - app.js.map
                - app.css
                - app.css.map
        """

        for fname in ['README.rst', '.hidden.rst', 'testing.rst', 'LICENSE']:
            touch(os.path.join(self.temp_dir, fname))

        # Set up the rest of the test package
        test_pkg = os.path.join(self.temp_dir, 'app')
        os.mkdir(test_pkg)
        for fname in ['__init__.py', 'a.txt', 'b.txt', 'c.rst']:
            touch(os.path.join(test_pkg, fname))

        # Some compiled front-end assets to include
        static = os.path.join(test_pkg, 'static')
        os.mkdir(static)
        for fname in ['app.js', 'app.js.map', 'app.css', 'app.css.map']:
            touch(os.path.join(static, fname))

        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self, method):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)

    def make_manifest(self, contents):
        """Write a MANIFEST.in."""
        with open(os.path.join(self.temp_dir, 'MANIFEST.in'), 'w') as f:
            f.write(DALS(contents))

    def get_files(self):
        """Run egg_info and get all the files to include, as a set"""
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = egg_info(dist)
        cmd.ensure_finalized()

        cmd.run()

        return set(cmd.filelist.files)

    def test_no_manifest(self):
        """Check a missing MANIFEST.in includes only the standard files."""
        assert (default_files - set(['MANIFEST.in'])) == self.get_files()

    def test_empty_files(self):
        """Check an empty MANIFEST.in includes only the standard files."""
        self.make_manifest("")
        assert default_files == self.get_files()

    def test_include(self):
        """Include extra rst files in the project root."""
        self.make_manifest("include *.rst")
        files = default_files | set([
            'testing.rst', '.hidden.rst'])
        assert files == self.get_files()

    def test_exclude(self):
        """Include everything in app/ except the text files"""
        l = make_local_path
        self.make_manifest(
            """
            include app/*
            exclude app/*.txt
            """)
        files = default_files | set([l('app/c.rst')])
        assert files == self.get_files()

    def test_include_multiple(self):
        """Include with multiple patterns."""
        l = make_local_path
        self.make_manifest("include app/*.txt app/static/*")
        files = default_files | set([
            l('app/a.txt'), l('app/b.txt'),
            l('app/static/app.js'), l('app/static/app.js.map'),
            l('app/static/app.css'), l('app/static/app.css.map')])
        assert files == self.get_files()

    def test_graft(self):
        """Include the whole app/static/ directory."""
        l = make_local_path
        self.make_manifest("graft app/static")
        files = default_files | set([
            l('app/static/app.js'), l('app/static/app.js.map'),
            l('app/static/app.css'), l('app/static/app.css.map')])
        assert files == self.get_files()

    def test_graft_global_exclude(self):
        """Exclude all *.map files in the project."""
        l = make_local_path
        self.make_manifest(
            """
            graft app/static
            global-exclude *.map
            """)
        files = default_files | set([
            l('app/static/app.js'), l('app/static/app.css')])
        assert files == self.get_files()

    def test_global_include(self):
        """Include all *.rst, *.js, and *.css files in the whole tree."""
        l = make_local_path
        self.make_manifest(
            """
            global-include *.rst *.js *.css
            """)
        files = default_files | set([
            '.hidden.rst', 'testing.rst', l('app/c.rst'),
            l('app/static/app.js'), l('app/static/app.css')])
        assert files == self.get_files()

    def test_graft_prune(self):
        """Include all files in app/, except for the whole app/static/ dir."""
        l = make_local_path
        self.make_manifest(
            """
            graft app
            prune app/static
            """)
        files = default_files | set([
            l('app/a.txt'), l('app/b.txt'), l('app/c.rst')])
        assert files == self.get_files()
