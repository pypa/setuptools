"""
Setuptools is released using 'jaraco.packaging.release'. To make a release,
install jaraco.packaging and run 'python -m jaraco.packaging.release'
"""

import re
import os
import itertools

try:
    zip_longest = itertools.zip_longest
except AttributeError:
    zip_longest = itertools.izip_longest

def before_upload():
    _linkify('CHANGES.txt', 'CHANGES (linked).txt')

files_with_versions = (
    'ez_setup.py', 'setuptools/__init__.py',
)

test_info = "Travis-CI tests: http://travis-ci.org/#!/jaraco/setuptools"

os.environ["SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES"] = "1"

def _linkify(source, dest):
    with open(source) as source:
        out = _linkified_text(source.read())
    with open(dest, 'w') as dest:
        dest.write(out)

def _linkified(rst_path):
    "return contents of reStructureText file with linked issue references"
    rst_file = open(rst_path)
    rst_content = rst_file.read()
    rst_file.close()

    return _linkified_text(rst_content)

def _linkified_text(rst_content):
    # first identify any existing HREFs so they're not changed
    HREF_pattern = re.compile('`.*?`_', re.MULTILINE | re.DOTALL)

    # split on the HREF pattern, returning the parts to be linkified
    plain_text_parts = HREF_pattern.split(rst_content)
    anchors = []
    linkified_parts = [_linkified_part(part, anchors)
        for part in plain_text_parts]
    pairs = zip_longest(
        linkified_parts,
        HREF_pattern.findall(rst_content),
        fillvalue='',
    )
    rst_content = ''.join(flatten(pairs))

    anchors = sorted(anchors)

    bitroot = 'https://bitbucket.org/tarek/distribute'
    rst_content += "\n"
    for x in anchors:
        issue = re.findall(r'\d+', x)[0]
        rst_content += '.. _`%s`: %s/issue/%s\n' % (x, bitroot, issue)
    rst_content += "\n"
    return rst_content

def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)


def _linkified_part(text, anchors):
    """
    Linkify a part and collect any anchors generated
    """
    revision = re.compile(r'\b(issue\s+#?\d+)\b', re.M | re.I)

    anchors.extend(revision.findall(text)) # ['Issue #43', ...]
    return revision.sub(r'`\1`_', text)
