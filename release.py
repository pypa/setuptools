"""
Setuptools is released using 'jaraco.packaging.release'. To make a release,
install jaraco.packaging and run 'python -m jaraco.packaging.release'
"""

import re
import os
import subprocess

import pkg_resources

pkg_resources.require('jaraco.packaging>=2.0')
pkg_resources.require('wheel')


def before_upload():
    _linkify('CHANGES.txt', 'CHANGES (links).txt')
    BootstrapBookmark.add()


def after_push():
    os.remove('CHANGES (links).txt')
    BootstrapBookmark.push()

files_with_versions = (
    'ez_setup.py', 'setuptools/version.py',
)

# bdist_wheel must be included or pip will break
dist_commands = 'sdist', 'bdist_wheel'

test_info = "Travis-CI tests: http://travis-ci.org/#!/jaraco/setuptools"

os.environ["SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES"] = "1"

link_patterns = [
    r"(Issue )?#(?P<issue>\d+)",
    r"Pull Request ?#(?P<pull_request>\d+)",
    r"Distribute #(?P<distribute>\d+)",
    r"Buildout #(?P<buildout>\d+)",
    r"Old Setuptools #(?P<old_setuptools>\d+)",
    r"Jython #(?P<jython>\d+)",
    r"Python #(?P<python>\d+)",
]

issue_urls = dict(
    pull_request='https://bitbucket.org'
        '/pypa/setuptools/pull-request/{pull_request}',
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
