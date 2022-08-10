"""Tests for distutils.log"""

import io
import sys
from test.support import swap_attr

import pytest

from distutils import log


class TestLog:
    @pytest.mark.parametrize(
        'errors',
        (
            'strict',
            'backslashreplace',
            'surrogateescape',
            'replace',
            'ignore',
        ),
    )
    def test_non_ascii(self, errors):
        # Issues #8663, #34421: test that non-encodable text is escaped with
        # backslashreplace error handler and encodable non-ASCII text is
        # output as is.
        stdout = io.TextIOWrapper(io.BytesIO(), encoding='cp437', errors=errors)
        stderr = io.TextIOWrapper(io.BytesIO(), encoding='cp437', errors=errors)
        old_threshold = log.set_threshold(log.DEBUG)
        try:
            with swap_attr(sys, 'stdout', stdout), swap_attr(sys, 'stderr', stderr):
                log.debug('Dεbug\tMėssãge')
                log.fatal('Fαtal\tÈrrōr')
        finally:
            log.set_threshold(old_threshold)

        stdout.seek(0)
        assert stdout.read().rstrip() == (
            'Dεbug\tM?ss?ge'
            if errors == 'replace'
            else 'Dεbug\tMssge'
            if errors == 'ignore'
            else 'Dεbug\tM\\u0117ss\\xe3ge'
        )
        stderr.seek(0)
        assert stderr.read().rstrip() == (
            'Fαtal\t?rr?r'
            if errors == 'replace'
            else 'Fαtal\trrr'
            if errors == 'ignore'
            else 'Fαtal\t\\xc8rr\\u014dr'
        )
