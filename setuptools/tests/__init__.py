import locale

import pytest


__all__ = ['fail_on_ascii']


is_ascii = locale.getpreferredencoding() == 'ANSI_X3.4-1968'
fail_on_ascii = pytest.mark.xfail(is_ascii, reason="Test fails in this locale")
