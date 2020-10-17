import locale

import pytest


__all__ = ['fail_on_ascii', 'ack_2to3']


is_ascii = locale.getpreferredencoding() == 'ANSI_X3.4-1968'
fail_on_ascii = pytest.mark.xfail(is_ascii, reason="Test fails in this locale")


ack_2to3 = pytest.mark.filterwarnings('ignore:2to3 support is deprecated')
