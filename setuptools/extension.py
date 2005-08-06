from distutils.core import Extension as _Extension

try:
    from Pyrex.Distutils.build_ext import build_ext

except ImportError:

    # Pyrex isn't around, so fix up the sources

    from dist import _get_unpatched
    _Extension = _get_unpatched(_Extension)

    class Extension(_Extension):

        """Extension that uses '.c' files in place of '.pyx' files"""

        def __init__(self,*args,**kw):
            _Extension.__init__(self,*args,**kw)
            sources = []
            for s in self.sources:
                if s.endswith('.pyx'):
                    sources.append(s[:-3]+'c')
                else:
                    sources.append(s)
            self.sources = sources

    import sys, distutils.core, distutils.extension
    distutils.core.Extension = Extension
    distutils.extension.Extension = Extension
    if 'distutils.command.build_ext' in sys.modules:
        sys.modules['distutils.command.build_ext'].Extension = Extension

else:

    # Pyrex is here, just use regular extension type
    Extension = _Extension

