from __future__ import annotations

import functools
import re
import sys
from dataclasses import field
from typing import TYPE_CHECKING

from ._distutils._dataclass import lenient_dataclass
from .monkey import get_unpatched

import distutils.core


def _have_cython() -> bool:
    """
    Return True if Cython can be imported.
    """
    cython_impl = 'Cython.Distutils.build_ext'
    try:
        # from (cython_impl) import build_ext
        __import__(cython_impl, fromlist=['build_ext']).build_ext  # noqa: B018 # evaluated to trigger validation/side effect
    except Exception:  # noqa: BLE001 # intentional broad fallback
        return False
    return True


# for compatibility
have_pyrex = _have_cython
if TYPE_CHECKING:
    if sys.version_info < (3, 12):
        from ._distutils.core import Extension as _Extension
        # Hacky workaround for mypy using stdlib distutils on Python < 3.12, where Extension isn't a dataclass
    else:
        # Work around a mypy issue where type[T] can't be used as a base: https://github.com/python/mypy/issues/10962
        from distutils.core import Extension as _Extension
else:
    _Extension = get_unpatched(distutils.core.Extension)

@lenient_dataclass()
class Extension(_Extension):
    """
    Describes a single extension module.

    This means that all source files will be compiled into a single binary file
    ``<module path>.<suffix>`` (with ``<module path>`` derived from ``name`` and
    ``<suffix>`` defined by one of the values in
    ``importlib.machinery.EXTENSION_SUFFIXES``).

    In the case ``.pyx`` files are passed as ``sources and`` ``Cython`` is **not**
    installed in the build environment, ``setuptools`` may also try to look for the
    equivalent ``.cpp`` or ``.c`` files.

    :raises setuptools.errors.PlatformError: if ``runtime_library_dirs`` is
      specified on Windows. (since v63)
    """

    py_limited_api: bool = False
    """opt-in flag for the usage of :doc:`Python's limited API <python:c-api/stable>`."""

    # These 4 are set and used in setuptools/command/build_ext.py
    # The lack of a default value and risk of `AttributeError` is purposeful
    # to avoid people forgetting to call finalize_options if they modify the extension list.
    # See example/rationale in https://github.com/pypa/setuptools/issues/4529.
    _full_name: str = field(init=False)  #: Private API, internal use only.
    _links_to_dynamic: bool = field(init=False)  #: Private API, internal use only.
    _needs_stub: bool = field(init=False)  #: Private API, internal use only.
    _file_name: str = field(init=False)  #: Private API, internal use only.

    def _convert_pyx_sources_to_lang(self):
        """
        Replace sources with .pyx extensions to sources with the target
        language extension. This mechanism allows language authors to supply
        pre-converted sources but to prefer the .pyx sources.
        """
        if _have_cython():
            # the build has Cython, so allow it to compile the .pyx files
            return
        lang = self.language or ''
        target_ext = '.cpp' if lang.lower() == 'c++' else '.c'
        sub = functools.partial(re.sub, '.pyx$', target_ext)
        self.sources = list(map(sub, self.sources))


@lenient_dataclass()
class Library(Extension):
    """Just like a regular Extension, but built as a library instead"""
