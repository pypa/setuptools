import tempfile
import os
import shutil
import sys
import contextlib

from ..compat import StringIO


@contextlib.contextmanager
def tempdir(cd=lambda dir:None):
    temp_dir = tempfile.mkdtemp()
    orig_dir = os.getcwd()
    try:
        cd(temp_dir)
        yield temp_dir
    finally:
        cd(orig_dir)
        shutil.rmtree(temp_dir)


@contextlib.contextmanager
def environment(**updates):
    old_env = os.environ.copy()
    os.environ.update(updates)
    try:
        yield
    finally:
        for key in updates:
            del os.environ[key]
        os.environ.update(old_env)


@contextlib.contextmanager
def argv(repl):
    old_argv = sys.argv[:]
    sys.argv[:] = repl
    yield
    sys.argv[:] = old_argv


@contextlib.contextmanager
def quiet():
    """
    Redirect stdout/stderr to StringIO objects to prevent console output from
    distutils commands.
    """

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    new_stdout = sys.stdout = StringIO()
    new_stderr = sys.stderr = StringIO()
    try:
        yield new_stdout, new_stderr
    finally:
        new_stdout.seek(0)
        new_stderr.seek(0)
        sys.stdout = old_stdout
        sys.stderr = old_stderr
