"""Regression tests for setuptools.extension.Extension semantics."""

import pytest

from setuptools.extension import Extension, Library


def make(name='x', sources=('y.c',)):
    return Extension(name, list(sources))


def test_extension_is_hashable():
    """Extension must stay hashable (set membership, dict keys).

    The dataclass conversion of the base class (pypa/distutils#373,
    vendored since 84.0.0) set ``__hash__ = None``, breaking setup
    scripts that collect live extension objects in sets or dict keys,
    e.g. pywin32's ``{ext for ext, why in self.excluded_extensions}``.
    """
    ext = make()
    assert hash(ext) is not None
    assert len({ext, make()}) == 2
    registry = {ext: 'built'}
    assert registry[ext] == 'built'


def test_library_is_hashable():
    lib = Library('x', ['y.c'])
    assert hash(lib) is not None
    assert len({lib, Library('x', ['y.c'])}) == 2


def test_extension_equality_is_identity():
    """Distinct instances stay distinct even with identical field values.

    Pre-84.0.0 ``Extension`` used inherited identity equality; the
    generated value-based ``__eq__`` made ``ext in some_list`` true for
    objects that were never added, on top of removing hashability.
    Pinning both halves of the contract so a future conversion cannot
    silently flip either again.
    """
    a, b = make(), make()
    assert a != b
    registry = {a: 'built'}
    with pytest.raises(KeyError):
        registry[b]


def test_same_object_is_equal_to_itself():
    """Reflexivity: the *same* object still dedups and matches in lookups."""
    a = make()
    assert len({a, a}) == 1
    assert [a].count(a) == 1
    b = make()
    assert [a].count(b) == 0
