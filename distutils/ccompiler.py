from .compilers.C import base
from .compilers.C.base import (
    # `_default_compilers` is needed by numpy.distutils, which is supported until
    #  Python 3.11 is deprecated. This import & export can be removed when
    #  Python 3.11 is no longer supported by distutils.
    _default_compilers,
    compiler_class,
    gen_lib_options,
    gen_preprocess_options,
    get_default_compiler,
    new_compiler,
    show_compilers,
)
from .compilers.C.errors import CompileError, LinkError

__all__ = [
    "CompileError",
    "LinkError",
    "_default_compilers",
    "compiler_class",
    "gen_lib_options",
    "gen_preprocess_options",
    "get_default_compiler",
    "new_compiler",
    "show_compilers",
]


CCompiler = base.Compiler
