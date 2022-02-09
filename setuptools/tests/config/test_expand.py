import os

import pytest

from distutils.errors import DistutilsOptionError
from setuptools.command.sdist import sdist
from setuptools.config import expand
from setuptools.sandbox import pushd


def write_files(files, root_dir):
    for file, content in files.items():
        path = root_dir / file
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(content)


def test_glob_relative(tmp_path):
    files = {
        "dir1/dir2/dir3/file1.txt",
        "dir1/dir2/file2.txt",
        "dir1/file3.txt",
        "a.ini",
        "b.ini",
        "dir1/c.ini",
        "dir1/dir2/a.ini",
    }

    write_files({k: "" for k in files}, tmp_path)
    patterns = ["**/*.txt", "[ab].*", "**/[ac].ini"]
    with pushd(tmp_path):
        assert set(expand.glob_relative(patterns)) == files
    # Make sure the same APIs work outside cwd
    assert set(expand.glob_relative(patterns, tmp_path)) == files


def test_read_files(tmp_path):
    files = {
        "a.txt": "a",
        "dir1/b.txt": "b",
        "dir1/dir2/c.txt": "c"
    }
    write_files(files, tmp_path)
    with pushd(tmp_path):
        assert expand.read_files(list(files)) == "a\nb\nc"

    with pushd(tmp_path / "dir1"), pytest.raises(DistutilsOptionError):
        expand.read_files(["../a.txt"])

    # Make sure the same APIs work outside cwd
    assert expand.read_files(list(files), tmp_path) == "a\nb\nc"
    with pytest.raises(DistutilsOptionError):
        expand.read_files(["../a.txt"], tmp_path)


def test_read_attr(tmp_path):
    files = {
        "pkg/__init__.py": "",
        "pkg/sub/__init__.py": "VERSION = '0.1.1'",
        "pkg/sub/mod.py": (
            "VALUES = {'a': 0, 'b': {42}, 'c': (0, 1, 1)}\n"
            "raise SystemExit(1)"
        ),
    }
    write_files(files, tmp_path)
    # Make sure it can read the attr statically without evaluating the module
    with pushd(tmp_path):
        assert expand.read_attr('pkg.sub.VERSION') == '0.1.1'
        values = expand.read_attr('lib.mod.VALUES', {'lib': 'pkg/sub'})
    assert values['a'] == 0
    assert values['b'] == {42}

    # Make sure the same APIs work outside cwd
    assert expand.read_attr('pkg.sub.VERSION', root_dir=tmp_path) == '0.1.1'
    values = expand.read_attr('lib.mod.VALUES', {'lib': 'pkg/sub'}, tmp_path)
    assert values['c'] == (0, 1, 1)


def test_resolve_class():
    assert expand.resolve_class("setuptools.command.sdist.sdist") == sdist


def test_find_packages(tmp_path):
    files = {
        "pkg/__init__.py",
        "other/__init__.py",
        "dir1/dir2/__init__.py",
    }

    write_files({k: "" for k in files}, tmp_path)
    with pushd(tmp_path):
        assert set(expand.find_packages(where=['.'])) == {"pkg", "other"}
        expected = {"pkg", "other", "dir2"}
        assert set(expand.find_packages(where=['.', "dir1"])) == expected
        expected = {"pkg", "other", "dir1", "dir1.dir2"}
        assert set(expand.find_packages(namespaces="True")) == expected

    # Make sure the same APIs work outside cwd
    path = str(tmp_path).replace(os.sep, '/')  # ensure posix-style paths
    dir1_path = str(tmp_path / "dir1").replace(os.sep, '/')

    assert set(expand.find_packages(where=[path])) == {"pkg", "other"}
    expected = {"pkg", "other", "dir2"}
    assert set(expand.find_packages(where=[path, dir1_path])) == expected
    expected = {"pkg", "other", "dir1", "dir1.dir2"}
    assert set(expand.find_packages(where=[path], namespaces="True")) == expected
