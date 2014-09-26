import sys
import re
import functools
import distutils.core
import distutils.errors
import distutils.extension
import distutils.msvc9compiler

from setuptools.dist import _get_unpatched

_Extension = _get_unpatched(distutils.core.Extension)

def _patch_msvc9compiler_find_vcvarsall():
    """
    Looks for the standalone VC for Python before falling back on
    distutils's original approach.
    """
    VC_BASE = r'Software\%sMicrosoft\DevDiv\VCForPython\%0.1f'
    find_vcvarsall = distutils.msvc9compiler.find_vcvarsall
    query_vcvarsall = distutils.msvc9compiler.query_vcvarsall
    if find_vcvarsall and find_vcvarsall.__module__.startswith('setuptools.'):
        # Already patched
        return

    def _find_vcvarsall(version):
        Reg = distutils.msvc9compiler.Reg
        try:
            # Per-user installs register the compiler path here
            productdir = Reg.get_value(VC_BASE % ('', version), "installdir")
        except KeyError:
            try:
                # All-user installs on a 64-bit system register here
                productdir = Reg.get_value(VC_BASE % ('Wow6432Node\\', version), "installdir")
            except KeyError:
                productdir = None

        if productdir:
            import os
            vcvarsall = os.path.join(productdir, "vcvarsall.bat")
            if os.path.isfile(vcvarsall):
                return vcvarsall

        return find_vcvarsall(version)

    def _query_vcvarsall(version, *args, **kwargs):
        try:
            return query_vcvarsall(version, *args, **kwargs)
        except distutils.errors.DistutilsPlatformError:
            exc = sys.exc_info()[1]
            if exc and "vcvarsall.bat" in exc.args[0]:
                message = 'Microsoft Visual C++ %0.1f is required (%s).' % (version, exc.args[0])
                if int(version) == 9:
                    # This redirection link is maintained by Microsoft.
                    # Contact vspython@microsoft.com if it needs updating.
                    raise distutils.errors.DistutilsPlatformError(
                        message + ' Get it from http://aka.ms/vcpython27'
                    )
                raise distutils.errors.DistutilsPlatformError(message)
            raise

    distutils.msvc9compiler.find_vcvarsall = _find_vcvarsall
    distutils.msvc9compiler.query_vcvarsall = _query_vcvarsall
_patch_msvc9compiler_find_vcvarsall()

def have_pyrex():
    """
    Return True if Cython or Pyrex can be imported.
    """
    pyrex_impls = 'Cython.Distutils.build_ext', 'Pyrex.Distutils.build_ext'
    for pyrex_impl in pyrex_impls:
        try:
            # from (pyrex_impl) import build_ext
            __import__(pyrex_impl, fromlist=['build_ext']).build_ext
            return True
        except Exception:
            pass
    return False


class Extension(_Extension):
    """Extension that uses '.c' files in place of '.pyx' files"""

    def __init__(self, *args, **kw):
        _Extension.__init__(self, *args, **kw)
        self._convert_pyx_sources_to_lang()

    def _convert_pyx_sources_to_lang(self):
        """
        Replace sources with .pyx extensions to sources with the target
        language extension. This mechanism allows language authors to supply
        pre-converted sources but to prefer the .pyx sources.
        """
        if have_pyrex():
            # the build has Cython, so allow it to compile the .pyx files
            return
        lang = self.language or ''
        target_ext = '.cpp' if lang.lower() == 'c++' else '.c'
        sub = functools.partial(re.sub, '.pyx$', target_ext)
        self.sources = list(map(sub, self.sources))

class Library(Extension):
    """Just like a regular Extension, but built as a library instead"""

distutils.core.Extension = Extension
distutils.extension.Extension = Extension
if 'distutils.command.build_ext' in sys.modules:
    sys.modules['distutils.command.build_ext'].Extension = Extension
