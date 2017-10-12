import locale

import pytest

is_ascii = locale.getpreferredencoding() == 'ANSI_X3.4-1968'
fail_on_ascii = pytest.mark.xfail(is_ascii, reason="Test fails in this locale")
