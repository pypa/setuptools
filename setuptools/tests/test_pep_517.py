import pytest
import os

# Only test the backend on Python 3
# because we don't want to require
# a concurrent.futures backport for testing
pytest.importorskip('concurrent.futures')

from importlib import import_module
from concurrent.futures import ProcessPoolExecutor

class BuildBackend(object):
    """PEP 517 Build Backend"""
    def __init__(self, cwd=None, env={}, backend_name='setuptools.pep517'):
        self.cwd = cwd
        self.env = env
        self.backend_name = backend_name
        self.pool = ProcessPoolExecutor()

    def __getattr__(self, name):
        """Handles aribrary function invokations on the build backend."""

        def method(**kw):
            return self.pool.submit(
                BuildBackendCaller(self.cwd, self.env, self.backend_name),
                (name, kw)).result()

        return method


class BuildBackendCaller(object):
    def __init__(self, cwd, env, backend_name):
        self.cwd = cwd
        self.env = env
        self.backend_name = backend_name

    def __getattr__(self, name):
        """Handles aribrary function invokations on the build backend."""
        os.chdir(self.cwd)
        os.environ.update(self.env)
        return getattr(import_module(self.backend_name), name)
