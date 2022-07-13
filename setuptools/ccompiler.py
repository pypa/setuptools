# Expose a subset of distutils as public API
# to help with migration to Python 3.12

from ._distutils.ccompiler import CCompiler
from ._distutils.sysconfig import customize_compiler
from ._distutils.ccompiler import new_compiler
