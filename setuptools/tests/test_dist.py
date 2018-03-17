# -*- coding: utf-8 -*-
from setuptools import Distribution
from setuptools.extern.six.moves.urllib.request import pathname2url
from setuptools.extern.six.moves.urllib_parse import urljoin
from setuptools.extern.six import StringIO

from .textwrap import DALS
from .test_easy_install import make_nspkg_sdist

import pytest

def test_dist_fetch_build_egg(tmpdir):
    """
    Check multiple calls to `Distribution.fetch_build_egg` work as expected.
    """
    index = tmpdir.mkdir('index')
    index_url = urljoin('file://', pathname2url(str(index)))
    def sdist_with_index(distname, version):
        dist_dir = index.mkdir(distname)
        dist_sdist = '%s-%s.tar.gz' % (distname, version)
        make_nspkg_sdist(str(dist_dir.join(dist_sdist)), distname, version)
        with dist_dir.join('index.html').open('w') as fp:
            fp.write(DALS(
                '''
                <!DOCTYPE html><html><body>
                <a href="{dist_sdist}" rel="internal">{dist_sdist}</a><br/>
                </body></html>
                '''
            ).format(dist_sdist=dist_sdist))
    sdist_with_index('barbazquux', '3.2.0')
    sdist_with_index('barbazquux-runner', '2.11.1')
    with tmpdir.join('setup.cfg').open('w') as fp:
        fp.write(DALS(
            '''
            [easy_install]
            index_url = {index_url}
            '''
        ).format(index_url=index_url))
    reqs = '''
    barbazquux-runner
    barbazquux
    '''.split()
    with tmpdir.as_cwd():
        dist = Distribution()
        dist.parse_config_files()
        resolved_dists = [
            dist.fetch_build_egg(r)
            for r in reqs
        ]
    assert [dist.key for dist in resolved_dists if dist] == reqs


def __maintainer_test_cases():
    attrs = {"name": "package",
             "version": "1.0",
             "description": "xxx"}

    def merge_dicts(d1, d2):
        d1 = d1.copy()
        d1.update(d2)

        return d1

    test_cases = [
        ('No author, no maintainer', attrs.copy()),
        ('Author (no e-mail), no maintainer', merge_dicts(attrs,
            {'author': 'Author Name'})),
        ('Author (e-mail), no maintainer', merge_dicts(attrs,
            {'author': 'Author Name',
             'author_email': 'author@name.com'})),
        ('No author, maintainer (no e-mail)', merge_dicts(attrs,
            {'maintainer': 'Maintainer Name'})),
        ('No author, maintainer (e-mail)', merge_dicts(attrs,
            {'maintainer': 'Maintainer Name',
             'maintainer_email': 'maintainer@name.com'})),
        ('Author (no e-mail), Maintainer (no-email)', merge_dicts(attrs,
            {'author': 'Author Name',
             'maintainer': 'Maintainer Name'})),
        ('Author (e-mail), Maintainer (e-mail)', merge_dicts(attrs,
            {'author': 'Author Name',
             'author_email': 'author@name.com',
             'maintainer': 'Maintainer Name',
             'maintainer_email': 'maintainer@name.com'})),
        ('No author (e-mail), no maintainer (e-mail)', merge_dicts(attrs,
            {'author_email': 'author@name.com',
             'maintainer_email': 'maintainer@name.com'})),
        ('Author unicode', merge_dicts(attrs,
            {'author': '鉄沢寛'})),
        ('Maintainer unicode', merge_dicts(attrs,
            {'maintainer': 'Jan Łukasiewicz'})),
    ]

    return test_cases

@pytest.mark.parametrize('name,attrs', __maintainer_test_cases())
def test_maintainer_author(name, attrs):
    tested_keys = {
        'author': 'Author',
        'author_email': 'Author-email',
        'maintainer': 'Maintainer',
        'maintainer_email': 'Maintainer-email',
    }

    # Generate a PKG-INFO file
    dist = Distribution(attrs)
    PKG_INFO = StringIO()
    dist.metadata.write_pkg_file(PKG_INFO)
    PKG_INFO.seek(0)

    pkg_lines = PKG_INFO.readlines()
    pkg_lines = [_ for _ in pkg_lines if _]   # Drop blank lines
    pkg_lines_set = set(pkg_lines)

    # Duplicate lines should not be generated
    assert len(pkg_lines) == len(pkg_lines_set)

    for fkey, dkey in tested_keys.items():
        val = attrs.get(dkey, None)
        if val is None:
            for line in pkg_lines:
                assert not line.startswith(fkey + ':')
        else:
            line = '%s: %s' % (fkey, val)
            assert line in pkg_lines_set

