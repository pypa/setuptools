"""
Sphinx plugin to add links to the changelog.
"""

import re
import os


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

def setup(app):
    _linkify('CHANGES.txt', 'CHANGES (links).txt')
    app.connect('build-finished', remove_file)

def remove_file(app, exception):
    os.remove('CHANGES (links).txt')
