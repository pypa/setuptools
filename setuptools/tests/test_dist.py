# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import collections
import re
from distutils.errors import DistutilsSetupError
from setuptools.dist import (
    _get_unpatched,
    check_package_data,
    DistDeprecationWarning,
)
from setuptools import Distribution
from setuptools.extern.six.moves.urllib.request import pathname2url
from setuptools.extern.six.moves.urllib_parse import urljoin
from setuptools.extern import six

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


def test_dist__get_unpatched_deprecated():
    pytest.warns(DistDeprecationWarning, _get_unpatched, [""])


def __read_test_cases():
    # Metadata version 1.0
    base_attrs = {
        "name": "package",
        "version": "0.0.1",
        "author": "Foo Bar",
        "author_email": "foo@bar.net",
        "long_description": "Long\ndescription",
        "description": "Short description",
        "keywords": ["one", "two"]
    }

    def merge_dicts(d1, d2):
        d1 = d1.copy()
        d1.update(d2)

        return d1

    test_cases = [
        ('Metadata version 1.0', base_attrs.copy()),
        ('Metadata version 1.1: Provides', merge_dicts(base_attrs, {
            'provides': ['package']
        })),
        ('Metadata version 1.1: Obsoletes', merge_dicts(base_attrs, {
            'obsoletes': ['foo']
        })),
        ('Metadata version 1.1: Classifiers', merge_dicts(base_attrs, {
            'classifiers': [
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.7',
                'License :: OSI Approved :: MIT License',
            ]})),
        ('Metadata version 1.1: Download URL', merge_dicts(base_attrs, {
            'download_url': 'https://example.com'
        })),
        ('Metadata Version 1.2: Requires-Python', merge_dicts(base_attrs, {
            'python_requires': '>=3.7'
        })),
        pytest.param(
            'Metadata Version 1.2: Project-Url',
            merge_dicts(base_attrs, {
                'project_urls': {
                    'Foo': 'https://example.bar'
                }
            }), marks=pytest.mark.xfail(
                reason="Issue #1578: project_urls not read"
            )),
        ('Metadata Version 2.1: Long Description Content Type',
         merge_dicts(base_attrs, {
             'long_description_content_type': 'text/x-rst; charset=UTF-8'
         })),
        pytest.param(
            'Metadata Version 2.1: Provides Extra',
            merge_dicts(base_attrs, {
                'provides_extras': ['foo', 'bar']
            }), marks=pytest.mark.xfail(reason="provides_extras not read")),
        ('Missing author, missing author e-mail',
         {'name': 'foo', 'version': '1.0.0'}),
        ('Missing author',
         {'name': 'foo',
          'version': '1.0.0',
          'author_email': 'snorri@sturluson.name'}),
        ('Missing author e-mail',
         {'name': 'foo',
          'version': '1.0.0',
          'author': 'Snorri Sturluson'}),
        ('Missing author',
         {'name': 'foo',
          'version': '1.0.0',
          'author': 'Snorri Sturluson'}),
    ]

    return test_cases


@pytest.mark.parametrize('name,attrs', __read_test_cases())
def test_read_metadata(name, attrs):
    dist = Distribution(attrs)
    metadata_out = dist.metadata
    dist_class = metadata_out.__class__

    # Write to PKG_INFO and then load into a new metadata object
    if six.PY2:
        PKG_INFO = io.BytesIO()
    else:
        PKG_INFO = io.StringIO()

    metadata_out.write_pkg_file(PKG_INFO)

    PKG_INFO.seek(0)
    metadata_in = dist_class()
    metadata_in.read_pkg_file(PKG_INFO)

    tested_attrs = [
        ('name', dist_class.get_name),
        ('version', dist_class.get_version),
        ('author', dist_class.get_contact),
        ('author_email', dist_class.get_contact_email),
        ('metadata_version', dist_class.get_metadata_version),
        ('provides', dist_class.get_provides),
        ('description', dist_class.get_description),
        ('download_url', dist_class.get_download_url),
        ('keywords', dist_class.get_keywords),
        ('platforms', dist_class.get_platforms),
        ('obsoletes', dist_class.get_obsoletes),
        ('requires', dist_class.get_requires),
        ('classifiers', dist_class.get_classifiers),
        ('project_urls', lambda s: getattr(s, 'project_urls', {})),
        ('provides_extras', lambda s: getattr(s, 'provides_extras', set())),
    ]

    for attr, getter in tested_attrs:
        assert getter(metadata_in) == getter(metadata_out)


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
        ('Author (no e-mail), no maintainer', merge_dicts(
            attrs,
            {'author': 'Author Name'})),
        ('Author (e-mail), no maintainer', merge_dicts(
            attrs,
            {'author': 'Author Name',
             'author_email': 'author@name.com'})),
        ('No author, maintainer (no e-mail)', merge_dicts(
            attrs,
            {'maintainer': 'Maintainer Name'})),
        ('No author, maintainer (e-mail)', merge_dicts(
            attrs,
            {'maintainer': 'Maintainer Name',
             'maintainer_email': 'maintainer@name.com'})),
        ('Author (no e-mail), Maintainer (no-email)', merge_dicts(
            attrs,
            {'author': 'Author Name',
             'maintainer': 'Maintainer Name'})),
        ('Author (e-mail), Maintainer (e-mail)', merge_dicts(
            attrs,
            {'author': 'Author Name',
             'author_email': 'author@name.com',
             'maintainer': 'Maintainer Name',
             'maintainer_email': 'maintainer@name.com'})),
        ('No author (e-mail), no maintainer (e-mail)', merge_dicts(
            attrs,
            {'author_email': 'author@name.com',
             'maintainer_email': 'maintainer@name.com'})),
        ('Author unicode', merge_dicts(
            attrs,
            {'author': '鉄沢寛'})),
        ('Maintainer unicode', merge_dicts(
            attrs,
            {'maintainer': 'Jan Łukasiewicz'})),
    ]

    return test_cases


@pytest.mark.parametrize('name,attrs', __maintainer_test_cases())
def test_maintainer_author(name, attrs, tmpdir):
    tested_keys = {
        'author': 'Author',
        'author_email': 'Author-email',
        'maintainer': 'Maintainer',
        'maintainer_email': 'Maintainer-email',
    }

    # Generate a PKG-INFO file
    dist = Distribution(attrs)
    fn = tmpdir.mkdir('pkg_info')
    fn_s = str(fn)

    dist.metadata.write_pkg_info(fn_s)

    with io.open(str(fn.join('PKG-INFO')), 'r', encoding='utf-8') as f:
        raw_pkg_lines = f.readlines()

    # Drop blank lines
    pkg_lines = list(filter(None, raw_pkg_lines))

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


def test_provides_extras_deterministic_order():
    extras = collections.OrderedDict()
    extras['a'] = ['foo']
    extras['b'] = ['bar']
    attrs = dict(extras_require=extras)
    dist = Distribution(attrs)
    assert dist.metadata.provides_extras == ['a', 'b']
    attrs['extras_require'] = collections.OrderedDict(
        reversed(list(attrs['extras_require'].items())))
    dist = Distribution(attrs)
    assert dist.metadata.provides_extras == ['b', 'a']

   
CHECK_PACKAGE_DATA_TESTS = (
    # Valid.
    ({
        '': ['*.txt', '*.rst'],
        'hello': ['*.msg'],
    }, None),
    # Not a dictionary.
    ((
        ('', ['*.txt', '*.rst']),
        ('hello', ['*.msg']),
    ), (
        "'package_data' must be a dictionary mapping package"
        " names to lists of string wildcard patterns"
    )),
    # Invalid key type.
    ({
        400: ['*.txt', '*.rst'],
    }, (
        "keys of 'package_data' dict must be strings (got 400)"
    )),
    # Invalid value type.
    ({
        'hello': str('*.msg'),
    }, (
        "\"values of 'package_data' dict\" must be a list of strings (got '*.msg')"
    )),
    # Invalid value type (generators are single use)
    ({
        'hello': (x for x in "generator"),
    }, (
        "\"values of 'package_data' dict\" must be a list of strings "
        "(got <generator object"
    )),
)


@pytest.mark.parametrize('package_data, expected_message', CHECK_PACKAGE_DATA_TESTS)
def test_check_package_data(package_data, expected_message):
    if expected_message is None:
        assert check_package_data(None, 'package_data', package_data) is None
    else:
        with pytest.raises(DistutilsSetupError, match=re.escape(expected_message)):
            check_package_data(None, str('package_data'), package_data)
