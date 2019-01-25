import locale

import pytest

from setuptools.extern.six import PY2, PY3


__all__ = [
  'fail_on_ascii', 'py2_only', 'py3_only'
]


is_ascii = locale.getpreferredencoding() == 'ANSI_X3.4-1968'
fail_on_ascii = pytest.mark.xfail(is_ascii, reason="Test fails in this locale")


py2_only = pytest.mark.skipif(not PY2, reason="Test runs on Python 2 only")
py3_only = pytest.mark.skipif(not PY3, reason="Test runs on Python 3 only")
