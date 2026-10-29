import sys

import pytest

from setuptools.command.install_lib import install_lib


def test_exclusion_paths_include_bytecode_cache() -> None:
    paths = list(install_lib._gen_exclusion_paths())
    assert '__init__.py' in paths
    if sys.implementation.cache_tag is not None:
        assert any(path.endswith('.pyc') and '__pycache__' in path for path in paths)


def test_exclusion_paths_without_cache_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    When ``sys.implementation.cache_tag`` is None, module caching is disabled
    and there are no bytecode cache files to exclude.
    """
    monkeypatch.setattr(sys.implementation, 'cache_tag', None, raising=False)
    paths = list(install_lib._gen_exclusion_paths())
    assert paths == ['__init__.py', '__init__.pyc', '__init__.pyo']
