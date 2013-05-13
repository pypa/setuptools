#!/usr/bin/env python
"""Distutils setup file, used to install or test 'setuptools'"""
import sys
import os
import textwrap
import re

# Allow to run setup.py from another directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

src_root = None
if sys.version_info >= (3,):
    tmp_src = os.path.join("build", "src")
    from distutils.filelist import FileList
    from distutils import dir_util, file_util, util, log
    log.set_verbosity(1)
    fl = FileList()
    manifest_file = open("MANIFEST.in")
    for line in manifest_file:
        fl.process_template_line(line)
    manifest_file.close()
    dir_util.create_tree(tmp_src, fl.files)
    outfiles_2to3 = []
    dist_script = os.path.join("build", "src", "ez_setup.py")
    for f in fl.files:
        outf, copied = file_util.copy_file(f, os.path.join(tmp_src, f), update=1)
        if copied and outf.endswith(".py") and outf != dist_script:
            outfiles_2to3.append(outf)
        if copied and outf.endswith('api_tests.txt'):
            # XXX support this in distutils as well
            from lib2to3.main import main
            main('lib2to3.fixes', ['-wd', os.path.join(tmp_src, 'tests', 'api_tests.txt')])

    util.run_2to3(outfiles_2to3)

    # arrange setup to use the copy
    sys.path.insert(0, os.path.abspath(tmp_src))
    src_root = tmp_src

from distutils.util import convert_path

d = {}
init_path = convert_path('setuptools/command/__init__.py')
init_file = open(init_path)
exec(init_file.read(), d)
init_file.close()

SETUP_COMMANDS = d['__all__']
VERSION = "0.7b1"

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.test import test as _test

scripts = []

console_scripts = ["easy_install = setuptools.command.easy_install:main"]
if os.environ.get("DISTRIBUTE_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT") is None:
    console_scripts.append("easy_install-%s = setuptools.command.easy_install:main" % sys.version[:3])

# specific command that is used to generate windows .exe files
class build_py(_build_py):
    def build_package_data(self):
        """Copy data files into build directory"""
        lastdir = None
        for package, src_dir, build_dir, filenames in self.data_files:
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                srcfile = os.path.join(src_dir, filename)
                outf, copied = self.copy_file(srcfile, target)
                srcfile = os.path.abspath(srcfile)

                # avoid a bootstrapping issue with easy_install -U (when the
                # previous version doesn't have convert_2to3_doctests)
                if not hasattr(self.distribution, 'convert_2to3_doctests'):
                    continue

                if copied and srcfile in self.distribution.convert_2to3_doctests:
                    self.__doctests_2to3.append(outf)

class test(_test):
    """Specific test class to avoid rewriting the entry_points.txt"""
    def run(self):
        entry_points = os.path.join('setuptools.egg-info', 'entry_points.txt')

        if not os.path.exists(entry_points):
            _test.run(self)
            return # even though _test.run will raise SystemExit

        f = open(entry_points)

        # running the test
        try:
            ep_content = f.read()
        finally:
            f.close()

        try:
            _test.run(self)
        finally:
            # restoring the file
            f = open(entry_points, 'w')
            try:
                f.write(ep_content)
            finally:
                f.close()


readme_file = open('README.txt')
# the release script adds hyperlinks to issues
if os.path.exists('CHANGES (links).txt'):
    changes_file = open('CHANGES (links).txt')
else:
    # but if the release script has not run, fall back to the source file
    changes_file = open('CHANGES.txt')
long_description = readme_file.read() + changes_file.read()
readme_file.close()
changes_file.close()

dist = setup(
    name="setuptools",
    version=VERSION,
    description="Easily download, build, install, upgrade, and uninstall "
                "Python packages",
    author="The fellowship of the packaging",
    author_email="distutils-sig@python.org",
    license="PSF or ZPL",
    long_description = long_description,
    keywords = "CPAN PyPI distutils eggs package management",
    url = "http://pypi.python.org/pypi/setuptools",
    test_suite = 'setuptools.tests',
    src_root = src_root,
    packages = find_packages(),
    package_data = {'setuptools':['*.exe'], 'setuptools.command':['*.xml']},

    py_modules = ['pkg_resources', 'easy_install', 'site'],

    zip_safe = (sys.version>="2.5"),   # <2.5 needs unzipped for -m to work

    cmdclass = {'test': test},
    entry_points = {

        "distutils.commands" : [
            "%(cmd)s = setuptools.command.%(cmd)s:%(cmd)s" % locals()
            for cmd in SETUP_COMMANDS
        ],

        "distutils.setup_keywords": [
            "eager_resources        = setuptools.dist:assert_string_list",
            "namespace_packages     = setuptools.dist:check_nsp",
            "extras_require         = setuptools.dist:check_extras",
            "install_requires       = setuptools.dist:check_requirements",
            "tests_require          = setuptools.dist:check_requirements",
            "entry_points           = setuptools.dist:check_entry_points",
            "test_suite             = setuptools.dist:check_test_suite",
            "zip_safe               = setuptools.dist:assert_bool",
            "package_data           = setuptools.dist:check_package_data",
            "exclude_package_data   = setuptools.dist:check_package_data",
            "include_package_data   = setuptools.dist:assert_bool",
            "packages               = setuptools.dist:check_packages",
            "dependency_links       = setuptools.dist:assert_string_list",
            "test_loader            = setuptools.dist:check_importable",
            "use_2to3               = setuptools.dist:assert_bool",
            "convert_2to3_doctests  = setuptools.dist:assert_string_list",
            "use_2to3_fixers        = setuptools.dist:assert_string_list",
            "use_2to3_exclude_fixers = setuptools.dist:assert_string_list",
        ],

        "egg_info.writers": [
            "PKG-INFO = setuptools.command.egg_info:write_pkg_info",
            "requires.txt = setuptools.command.egg_info:write_requirements",
            "entry_points.txt = setuptools.command.egg_info:write_entries",
            "eager_resources.txt = setuptools.command.egg_info:overwrite_arg",
            "namespace_packages.txt = setuptools.command.egg_info:overwrite_arg",
            "top_level.txt = setuptools.command.egg_info:write_toplevel_names",
            "depends.txt = setuptools.command.egg_info:warn_depends_obsolete",
            "dependency_links.txt = setuptools.command.egg_info:overwrite_arg",
        ],

        "console_scripts": console_scripts,

        "setuptools.file_finders":
            ["svn_cvs = setuptools.command.sdist:_default_revctrl"],

        "setuptools.installation":
            ['eggsecutable = setuptools.command.easy_install:bootstrap'],
        },


    classifiers = textwrap.dedent("""
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        License :: OSI Approved :: Python Software Foundation License
        License :: OSI Approved :: Zope Public License
        Operating System :: OS Independent
        Programming Language :: Python :: 2.4
        Programming Language :: Python :: 2.5
        Programming Language :: Python :: 2.6
        Programming Language :: Python :: 2.7
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.1
        Programming Language :: Python :: 3.2
        Programming Language :: Python :: 3.3
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: System :: Archiving :: Packaging
        Topic :: System :: Systems Administration
        Topic :: Utilities
        """).strip().splitlines(),
    extras_require = {
        "ssl:sys_platform=='win32'": "wincertstore==0.1",
        "ssl:sys_platform=='win32' and python_version=='2.4'": "ctypes==1.0.2",
        "ssl:python_version in '2.4, 2.5'":"ssl==1.16",
        "certs": "certifi==0.0.8",
    },
    dependency_links = [
        'http://pypi.python.org/packages/source/c/certifi/certifi-0.0.8.tar.gz#md5=dc5f5e7f0b5fc08d27654b17daa6ecec',
        'http://pypi.python.org/packages/source/s/ssl/ssl-1.16.tar.gz#md5=fb12d335d56f3c8c7c1fefc1c06c4bfb',
        'http://pypi.python.org/packages/source/w/wincertstore/wincertstore-0.1.zip#md5=2f9accbebe8f7b4c06ac7aa83879b81c',
        'http://sourceforge.net/projects/ctypes/files/ctypes/1.0.2/ctypes-1.0.2.win32-py2.3.exe/download#md5=9afe4b75240a8808a24df7a76b6081e3',
        'http://bitbucket.org/pypa/setuptools/downloads/ctypes-1.0.2.win32-py2.4.exe#md5=9092a0ad5a3d79fa2d980f1ddc5e9dbc',
        'http://bitbucket.org/pypa/setuptools/downloads/ssl-1.16-py2.4-win32.egg#md5=3cfa2c526dc66e318e8520b6f1aadce5',
        'http://bitbucket.org/pypa/setuptools/downloads/ssl-1.16-py2.5-win32.egg#md5=85ad1cda806d639743121c0bbcb5f39b',
    ],
    scripts = [],
    # tests_require = "setuptools[ssl]",
)
