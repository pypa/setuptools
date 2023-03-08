import functools
import io

import pytest

from setuptools import sic
from setuptools.dist import Distribution
from setuptools._core_metadata import rfc822_escape, rfc822_unescape


EXAMPLE_BASE_INFO = dict(
    name="package",
    version="0.0.1",
    author="Foo Bar",
    author_email="foo@bar.net",
    long_description="Long\ndescription",
    description="Short description",
    keywords=["one", "two"],
)


@pytest.mark.parametrize(
    'content, result',
    (
        pytest.param(
            "Just a single line",
            None,
            id="single_line",
        ),
        pytest.param(
            "Multiline\nText\nwithout\nextra indents\n",
            None,
            id="multiline",
        ),
        pytest.param(
            "Multiline\n    With\n\nadditional\n  indentation",
            None,
            id="multiline_with_indentation",
        ),
        pytest.param(
            "  Leading whitespace",
            "Leading whitespace",
            id="remove_leading_whitespace",
        ),
        pytest.param(
            "  Leading whitespace\nIn\n    Multiline comment",
            "Leading whitespace\nIn\n    Multiline comment",
            id="remove_leading_whitespace_multiline",
        ),
    ),
)
def test_rfc822_unescape(content, result):
    assert (result or content) == rfc822_unescape(rfc822_escape(content))


def __read_test_cases():
    base = EXAMPLE_BASE_INFO

    params = functools.partial(dict, base)

    test_cases = [
        ('Metadata version 1.0', params()),
        (
            'Metadata Version 1.0: Short long description',
            params(
                long_description='Short long description',
            ),
        ),
        (
            'Metadata version 1.1: Classifiers',
            params(
                classifiers=[
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.7',
                    'License :: OSI Approved :: MIT License',
                ],
            ),
        ),
        (
            'Metadata version 1.1: Download URL',
            params(
                download_url='https://example.com',
            ),
        ),
        (
            'Metadata Version 1.2: Requires-Python',
            params(
                python_requires='>=3.7',
            ),
        ),
        pytest.param(
            'Metadata Version 1.2: Project-Url',
            params(project_urls=dict(Foo='https://example.bar')),
            marks=pytest.mark.xfail(
                reason="Issue #1578: project_urls not read",
            ),
        ),
        (
            'Metadata Version 2.1: Long Description Content Type',
            params(
                long_description_content_type='text/x-rst; charset=UTF-8',
            ),
        ),
        (
            'License',
            params(
                license='MIT',
            ),
        ),
        (
            'License multiline',
            params(
                license='This is a long license \nover multiple lines',
            ),
        ),
        pytest.param(
            'Metadata Version 2.1: Provides Extra',
            params(provides_extras=['foo', 'bar']),
            marks=pytest.mark.xfail(reason="provides_extras not read"),
        ),
        (
            'Missing author',
            dict(
                name='foo',
                version='1.0.0',
                author_email='snorri@sturluson.name',
            ),
        ),
        (
            'Missing author e-mail',
            dict(
                name='foo',
                version='1.0.0',
                author='Snorri Sturluson',
            ),
        ),
        (
            'Missing author and e-mail',
            dict(
                name='foo',
                version='1.0.0',
            ),
        ),
        (
            'Bypass normalized version',
            dict(
                name='foo',
                version=sic('1.0.0a'),
            ),
        ),
    ]

    return test_cases


@pytest.mark.parametrize('name,attrs', __read_test_cases())
def test_read_metadata(name, attrs):
    dist = Distribution(attrs)
    metadata_out = dist.metadata
    dist_class = metadata_out.__class__

    # Write to PKG_INFO and then load into a new metadata object
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
        ('long_description', dist_class.get_long_description),
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
    attrs = {"name": "package", "version": "1.0", "description": "xxx"}

    def merge_dicts(d1, d2):
        d1 = d1.copy()
        d1.update(d2)

        return d1

    test_cases = [
        ('No author, no maintainer', attrs.copy()),
        (
            'Author (no e-mail), no maintainer',
            merge_dicts(attrs, {'author': 'Author Name'}),
        ),
        (
            'Author (e-mail), no maintainer',
            merge_dicts(
                attrs, {'author': 'Author Name', 'author_email': 'author@name.com'}
            ),
        ),
        (
            'No author, maintainer (no e-mail)',
            merge_dicts(attrs, {'maintainer': 'Maintainer Name'}),
        ),
        (
            'No author, maintainer (e-mail)',
            merge_dicts(
                attrs,
                {
                    'maintainer': 'Maintainer Name',
                    'maintainer_email': 'maintainer@name.com',
                },
            ),
        ),
        (
            'Author (no e-mail), Maintainer (no-email)',
            merge_dicts(
                attrs, {'author': 'Author Name', 'maintainer': 'Maintainer Name'}
            ),
        ),
        (
            'Author (e-mail), Maintainer (e-mail)',
            merge_dicts(
                attrs,
                {
                    'author': 'Author Name',
                    'author_email': 'author@name.com',
                    'maintainer': 'Maintainer Name',
                    'maintainer_email': 'maintainer@name.com',
                },
            ),
        ),
        (
            'No author (e-mail), no maintainer (e-mail)',
            merge_dicts(
                attrs,
                {
                    'author_email': 'author@name.com',
                    'maintainer_email': 'maintainer@name.com',
                },
            ),
        ),
        ('Author unicode', merge_dicts(attrs, {'author': '鉄沢寛'})),
        ('Maintainer unicode', merge_dicts(attrs, {'maintainer': 'Jan Łukasiewicz'})),
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

    # Drop blank lines and strip lines from default description
    pkg_lines = list(filter(None, raw_pkg_lines[:-2]))

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
