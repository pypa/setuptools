"""Tests for :mod:`setuptools._normalization`.

The functions here are pure string transformations, so they are checked
directly, without building anything.
"""

import pytest

from setuptools import _normalization


@pytest.mark.parametrize(
    ('version', 'expected'),
    [
        # A `v` prefix is legal PEP 440 (and explicitly accepted by
        # ``_PEP440_FALLBACK``), so it must not change the sanitized result.
        ('0.23-', '0.23.dev0+sanitized'),
        ('v0.23-', '0.23.dev0+sanitized'),
        ('V0.23-', '0.23.dev0+sanitized'),
        ('1.2-foo', '1.2.dev0+sanitized.foo'),
        ('v1.2-foo', '1.2.dev0+sanitized.foo'),
        ('1!2.0-foo', '1!2.0.dev0+sanitized.foo'),
        ('v1!2.0-foo', '1!2.0.dev0+sanitized.foo'),
        # Nothing after the numeric prefix: no leftover in the local segment.
        ('v1.2', '1.2'),
        ('v1.2.', '1.2.dev0+sanitized'),
    ],
)
def test_best_effort_version_v_prefix_is_not_duplicated(version, expected):
    """The ``v`` prefix is consumed by the fallback regex, so it must not be
    miscounted when splitting the version into its numeric and remaining parts.
    """
    assert _normalization.best_effort_version(version) == expected


@pytest.mark.parametrize('prefix', ['', 'v', 'V'])
def test_best_effort_version_ignores_v_prefix(prefix):
    """``best_effort_version`` is reached exactly when ``safe_version`` fails,
    and both accept a ``v`` prefix, so adding one cannot change the result.
    """
    assert _normalization.best_effort_version(f'{prefix}1.2-foo') == (
        _normalization.best_effort_version('1.2-foo')
    )
