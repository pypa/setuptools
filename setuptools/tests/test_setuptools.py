import os

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
    expected = ['readme.txt', os.path.join('foo', 'bar.py')]
    assert found == expected


@pytest.fixture
def can_symlink(tmpdir):
    """
    Skip if cannot create a symbolic link
    """
    link_fn = 'link'
    target_fn = 'target'
    try:
        os.symlink(target_fn, link_fn)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("Cannot create symbolic links")
    os.remove(link_fn)


def test_findall_missing_symlink(tmpdir, can_symlink):
    with tmpdir.as_cwd():
        os.symlink('foo', 'bar')
        found = list(setuptools.findall())
        assert found == []
