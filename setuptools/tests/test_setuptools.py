import pytest

import setuptools


@pytest.fixture
def example_source(tmpdir):
    tmpdir.mkdir('foo')
    (tmpdir / 'foo/bar.py').write('')
    (tmpdir / 'readme.txt').write('')
    return tmpdir


def test_findall(example_source):
    found = list(setuptools.findall(str(example_source)))
    expected = ['readme.txt', 'foo/bar.py']
    expected = [example_source.join(fn) for fn in expected]
    assert found == expected


def test_findall_curdir(example_source):
    with example_source.as_cwd():
        found = list(setuptools.findall())
    expected = ['readme.txt', 'foo/bar.py']
    assert found == expected
