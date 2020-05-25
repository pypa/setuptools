import pytest

from setuptools.glob import glob

from .files import build_files


@pytest.mark.parametrize('tree, pattern, matches', (
    ('', b'', []),
    ('', '', []),
    ('''
     appveyor.yml
     CHANGES.rst
     LICENSE
     MANIFEST.in
     pyproject.toml
     README.rst
     setup.cfg
     setup.py
     ''', '*.rst', ('CHANGES.rst', 'README.rst')),
    ('''
     appveyor.yml
     CHANGES.rst
     LICENSE
     MANIFEST.in
     pyproject.toml
     README.rst
     setup.cfg
     setup.py
     ''', b'*.rst', (b'CHANGES.rst', b'README.rst')),
))
def test_glob(monkeypatch, tmpdir, tree, pattern, matches):
    monkeypatch.chdir(tmpdir)
    build_files({name: '' for name in tree.split()})
    assert list(sorted(glob(pattern))) == list(sorted(matches))
