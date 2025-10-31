import pytest
from jaraco import path

from setuptools.glob import glob


@pytest.mark.parametrize(
    ('tree', 'pattern', 'matches'),
    (
        ('', b'', []),
        ('', '', []),
        (
            """
     appveyor.yml
     CHANGES.rst
     LICENSE
     MANIFEST.in
     pyproject.toml
     README.rst
     setup.cfg
     setup.py
     """,
            '*.rst',
            ('CHANGES.rst', 'README.rst'),
        ),
        (
            """
     appveyor.yml
     CHANGES.rst
     LICENSE
     MANIFEST.in
     pyproject.toml
     README.rst
     setup.cfg
     setup.py
     """,
            b'*.rst',
            (b'CHANGES.rst', b'README.rst'),
        ),
    ),
)
def test_glob(monkeypatch, tmpdir, tree, pattern, matches):
    monkeypatch.chdir(tmpdir)
    path.build(dict.fromkeys(tree.split(), ''))
    assert sorted(glob(pattern)) == sorted(matches)
