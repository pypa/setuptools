from setuptools.ccompiler import CCompiler
from setuptools.ccompiler import customize_compiler
from setuptools.ccompiler import new_compiler

import pytest


def test_ccompiler_namespace(_avoid_permanent_changes_in_sysconfig):
    ccompiler = new_compiler()
    customize_compiler(ccompiler)
    assert hasattr(ccompiler, "compile")


@pytest.fixture
def _avoid_permanent_changes_in_sysconfig(monkeypatch):
    import importlib
    import sys

    # Avoid caching `distutils.sysconfig` and force it to be re-imported later.
    # This should "cancel out" any permanent changes that comes as a side-effect of
    # import thing `distutils.sysconfig`.
    monkeypatch.setattr(sys, "modules", sys.modules.copy())
    yield
    importlib.invalidate_caches()
