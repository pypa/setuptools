from distutils.core import Extension as _Extension

try:
    from Pyrex.Distutils.build_ext import build_ext

except ImportError:

    # Pyrex isn't around, so fix up the sources

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

else:

    # Pyrex is here, just use regular extension type
    Extension = _Extension
