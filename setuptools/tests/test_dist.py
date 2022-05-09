import io
import collections
import re
import functools
import os
import urllib.request
import urllib.parse
from distutils.errors import DistutilsSetupError
from setuptools.dist import (
    _get_unpatched,
    check_package_data,
    DistDeprecationWarning,
    check_specifier,
    rfc822_escape,
    rfc822_unescape,
)
from setuptools import sic
from setuptools import Distribution

from .textwrap import DALS
from .test_easy_install import make_nspkg_sdist
from .test_find_packages import ensure_files

import pytest


def test_dist_fetch_build_egg(tmpdir):
    """
    Check multiple calls to `Distribution.fetch_build_egg` work as expected.
    """
    index = tmpdir.mkdir('index')
    index_url = urllib.parse.urljoin(
        'file://', urllib.request.pathname2url(str(index)))

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


EXAMPLE_BASE_INFO = dict(
    name="package",
    version="0.0.1",
    author="Foo Bar",
    author_email="foo@bar.net",
    long_description="Long\ndescription",
    description="Short description",
    keywords=["one", "two"],
)


def __read_test_cases():
    base = EXAMPLE_BASE_INFO

    params = functools.partial(dict, base)

    test_cases = [
        ('Metadata version 1.0', params()),
        ('Metadata Version 1.0: Short long description', params(
            long_description='Short long description',
        )),
        ('Metadata version 1.1: Classifiers', params(
            classifiers=[
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.7',
                'License :: OSI Approved :: MIT License',
            ],
        )),
        ('Metadata version 1.1: Download URL', params(
            download_url='https://example.com',
        )),
        ('Metadata Version 1.2: Requires-Python', params(
            python_requires='>=3.7',
        )),
        pytest.param(
            'Metadata Version 1.2: Project-Url',
            params(project_urls=dict(Foo='https://example.bar')),
            marks=pytest.mark.xfail(
                reason="Issue #1578: project_urls not read",
            ),
        ),
        ('Metadata Version 2.1: Long Description Content Type', params(
            long_description_content_type='text/x-rst; charset=UTF-8',
        )),
        ('License', params(license='MIT', )),
        ('License multiline', params(
            license='This is a long license \nover multiple lines',
        )),
        pytest.param(
            'Metadata Version 2.1: Provides Extra',
            params(provides_extras=['foo', 'bar']),
            marks=pytest.mark.xfail(reason="provides_extras not read"),
        ),
        ('Missing author', dict(
            name='foo',
            version='1.0.0',
            author_email='snorri@sturluson.name',
        )),
        ('Missing author e-mail', dict(
            name='foo',
            version='1.0.0',
            author='Snorri Sturluson',
        )),
        ('Missing author and e-mail', dict(
            name='foo',
            version='1.0.0',
        )),
        ('Bypass normalized version', dict(
            name='foo',
            version=sic('1.0.0a'),
        )),
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
        "\"values of 'package_data' dict\" "
        "must be a list of strings (got '*.msg')"
    )),
    # Invalid value type (generators are single use)
    ({
        'hello': (x for x in "generator"),
    }, (
        "\"values of 'package_data' dict\" must be a list of strings "
        "(got <generator object"
    )),
)


@pytest.mark.parametrize(
    'package_data, expected_message', CHECK_PACKAGE_DATA_TESTS)
def test_check_package_data(package_data, expected_message):
    if expected_message is None:
        assert check_package_data(None, 'package_data', package_data) is None
    else:
        with pytest.raises(
                DistutilsSetupError, match=re.escape(expected_message)):
            check_package_data(None, str('package_data'), package_data)


def test_check_specifier():
    # valid specifier value
    attrs = {'name': 'foo', 'python_requires': '>=3.0, !=3.1'}
    dist = Distribution(attrs)
    check_specifier(dist, attrs, attrs['python_requires'])

    # invalid specifier value
    attrs = {'name': 'foo', 'python_requires': ['>=3.0', '!=3.1']}
    with pytest.raises(DistutilsSetupError):
        dist = Distribution(attrs)


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
    )
)
def test_rfc822_unescape(content, result):
    assert (result or content) == rfc822_unescape(rfc822_escape(content))


def test_metadata_name():
    with pytest.raises(DistutilsSetupError, match='missing.*name'):
        Distribution()._validate_metadata()


@pytest.mark.parametrize(
    "dist_name, py_module",
    [
        ("my.pkg", "my_pkg"),
        ("my-pkg", "my_pkg"),
        ("my_pkg", "my_pkg"),
        ("pkg", "pkg"),
    ]
)
def test_dist_default_py_modules(tmp_path, dist_name, py_module):
    (tmp_path / f"{py_module}.py").touch()

    (tmp_path / "setup.py").touch()
    (tmp_path / "noxfile.py").touch()
    # ^-- make sure common tool files are ignored

    attrs = {
        **EXAMPLE_BASE_INFO,
        "name": dist_name,
        "src_root": str(tmp_path)
    }
    # Find `py_modules` corresponding to dist_name if not given
    dist = Distribution(attrs)
    dist.set_defaults()
    assert dist.py_modules == [py_module]
    # When `py_modules` is given, don't do anything
    dist = Distribution({**attrs, "py_modules": ["explicity_py_module"]})
    dist.set_defaults()
    assert dist.py_modules == ["explicity_py_module"]
    # When `packages` is given, don't do anything
    dist = Distribution({**attrs, "packages": ["explicity_package"]})
    dist.set_defaults()
    assert not dist.py_modules


@pytest.mark.parametrize(
    "dist_name, package_dir, package_files, packages",
    [
        ("my.pkg", None, ["my_pkg/__init__.py", "my_pkg/mod.py"], ["my_pkg"]),
        ("my-pkg", None, ["my_pkg/__init__.py", "my_pkg/mod.py"], ["my_pkg"]),
        ("my_pkg", None, ["my_pkg/__init__.py", "my_pkg/mod.py"], ["my_pkg"]),
        ("my.pkg", None, ["my/pkg/__init__.py"], ["my", "my.pkg"]),
        (
            "my_pkg",
            None,
            ["src/my_pkg/__init__.py", "src/my_pkg2/__init__.py"],
            ["my_pkg", "my_pkg2"]
        ),
        (
            "my_pkg",
            {"pkg": "lib", "pkg2": "lib2"},
            ["lib/__init__.py", "lib/nested/__init__.pyt", "lib2/__init__.py"],
            ["pkg", "pkg.nested", "pkg2"]
        ),
    ]
)
def test_dist_default_packages(
    tmp_path, dist_name, package_dir, package_files, packages
):
    ensure_files(tmp_path, package_files)

    (tmp_path / "setup.py").touch()
    (tmp_path / "noxfile.py").touch()
    # ^-- should not be included by default

    attrs = {
        **EXAMPLE_BASE_INFO,
        "name": dist_name,
        "src_root": str(tmp_path),
        "package_dir": package_dir
    }
    # Find `packages` either corresponding to dist_name or inside src
    dist = Distribution(attrs)
    dist.set_defaults()
    assert not dist.py_modules
    assert not dist.py_modules
    assert set(dist.packages) == set(packages)
    # When `py_modules` is given, don't do anything
    dist = Distribution({**attrs, "py_modules": ["explicit_py_module"]})
    dist.set_defaults()
    assert not dist.packages
    assert set(dist.py_modules) == {"explicit_py_module"}
    # When `packages` is given, don't do anything
    dist = Distribution({**attrs, "packages": ["explicit_package"]})
    dist.set_defaults()
    assert not dist.py_modules
    assert set(dist.packages) == {"explicit_package"}


@pytest.mark.parametrize(
    "dist_name, package_dir, package_files",
    [
        ("my.pkg.nested", None, ["my/pkg/nested/__init__.py"]),
        ("my.pkg", None, ["my/pkg/__init__.py", "my/pkg/file.py"]),
        ("my_pkg", None, ["my_pkg.py"]),
        ("my_pkg", None, ["my_pkg/__init__.py", "my_pkg/nested/__init__.py"]),
        ("my_pkg", None, ["src/my_pkg/__init__.py", "src/my_pkg/nested/__init__.py"]),
        (
            "my_pkg",
            {"my_pkg": "lib", "my_pkg.lib2": "lib2"},
            ["lib/__init__.py", "lib/nested/__init__.pyt", "lib2/__init__.py"],
        ),
        # Should not try to guess a name from multiple py_modules/packages
        ("UNKNOWN", None, ["src/mod1.py", "src/mod2.py"]),
        ("UNKNOWN", None, ["src/pkg1/__ini__.py", "src/pkg2/__init__.py"]),
    ]
)
def test_dist_default_name(tmp_path, dist_name, package_dir, package_files):
    """Make sure dist.name is discovered from packages/py_modules"""
    ensure_files(tmp_path, package_files)
    attrs = {
        **EXAMPLE_BASE_INFO,
        "src_root": "/".join(os.path.split(tmp_path)),  # POSIX-style
        "package_dir": package_dir
    }
    del attrs["name"]

    dist = Distribution(attrs)
    dist.set_defaults()
    assert dist.py_modules or dist.packages
    assert dist.get_name() == dist_name
