# Attempt to use Pyrex for building extensions, if available

try:
    from Pyrex.Distutils.build_ext import build_ext
except ImportError:
    from distutils.command.build_ext import build_ext
