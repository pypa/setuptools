"""
Setuptools is released using 'jaraco.packaging.release'. To make a release,
install jaraco.packaging and run 'python -m jaraco.packaging.release'
"""

import re
import os
import subprocess

import pkg_resources

pkg_resources.require('jaraco.packaging>=2.0')

def before_upload():
    _linkify('CHANGES.txt', 'CHANGES (links).txt')
    BootstrapBookmark.add()

def after_push():
    BootstrapBookmark.push()

files_with_versions = (
    'ez_setup.py', 'setuptools/version.py',
)

test_info = "Travis-CI tests: http://travis-ci.org/#!/jaraco/setuptools"

os.environ["SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES"] = "1"

link_patterns = [
    r"(Issue )?#(?P<issue>\d+)",
    r"Distribute #(?P<distribute>\d+)",
    r"Buildout #(?P<buildout>\d+)",
    r"Old Setuptools #(?P<old_setuptools>\d+)",
    r"Jython #(?P<jython>\d+)",
    r"Python #(?P<python>\d+)",
]

issue_urls = dict(
    issue='https://bitbucket.org/pypa/setuptools/issue/{issue}',
    distribute='https://bitbucket.org/tarek/distribute/issue/{distribute}',
    buildout='https://github.com/buildout/buildout/issues/{buildout}',
    old_setuptools='http://bugs.python.org/setuptools/issue{old_setuptools}',
    jython='http://bugs.jython.org/issue{jython}',
    python='http://bugs.python.org/issue{python}',
)


def _linkify(source, dest):
    pattern = '|'.join(link_patterns)
    with open(source) as source:
        out = re.sub(pattern, replacer, source.read())
    with open(dest, 'w') as dest:
        dest.write(out)


def replacer(match):
    text = match.group(0)
    match_dict = match.groupdict()
    for key in match_dict:
        if match_dict[key]:
            url = issue_urls[key].format(**match_dict)
            return "`{text} <{url}>`_".format(text=text, url=url)

class BootstrapBookmark:
    @staticmethod
    def add():
        cmd = ['hg', 'bookmark', '-i', 'bootstrap', '-f']
        subprocess.Popen(cmd)

    @staticmethod
    def push():
        """
        Push the bootstrap bookmark
        """
        push_command = ['hg', 'push', '-B', 'bootstrap']
        # don't use check_call here because mercurial will return a non-zero
        # code even if it succeeds at pushing the bookmark (because there are
        # no changesets to be pushed). !dm mercurial
        subprocess.call(push_command)
