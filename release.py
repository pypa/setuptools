"""
Setuptools is released using 'jaraco.packaging.release'. To make a release,
install jaraco.packaging and run 'python -m jaraco.packaging.release'
"""

import os
import subprocess

import pkg_resources

pkg_resources.require('jaraco.packaging>=2.0')
pkg_resources.require('wheel')


def before_upload():
    BootstrapBookmark.add()


def after_push():
    BootstrapBookmark.push()

files_with_versions = (
    'ez_setup.py', 'setuptools/version.py',
)

# bdist_wheel must be included or pip will break
dist_commands = 'sdist', 'bdist_wheel'

test_info = "Travis-CI tests: http://travis-ci.org/#!/jaraco/setuptools"

os.environ["SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES"] = "1"

class BootstrapBookmark:
    name = 'bootstrap'

    @classmethod
    def add(cls):
        cmd = ['hg', 'bookmark', '-i', cls.name, '-f']
        subprocess.Popen(cmd)

    @classmethod
    def push(cls):
        """
        Push the bootstrap bookmark
        """
        push_command = ['hg', 'push', '-B', cls.name]
        # don't use check_call here because mercurial will return a non-zero
        # code even if it succeeds at pushing the bookmark (because there are
        # no changesets to be pushed). !dm mercurial
        subprocess.call(push_command)
