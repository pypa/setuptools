==========================
Building Extension Modules
==========================

Setuptools can build C/C++ extension modules.  The keyword argument
``ext_modules`` of :func:`setup` should be a list of instances of the
`Extension class
<https://github.com/pypa/setuptools/blob/main/setuptools/_distutils/extension.py>`_.


Compiler and linker options
===========================

The command ``build_ext`` builds C/C++ extension modules.  It creates
a command line for running the compiler and linker by combining
compiler and linker options from various sources, as specified by
`test_customize_compiler
<https://github.com/pypa/setuptools/blob/main/setuptools/_distutils/tests/test_sysconfig.py>`_:

 * the ``sysconfig`` variables ``CFLAGS`` and ``LDFLAGS``,
 * the environment variables :envvar:`CC`, :envvar:`CPP`,
   :envvar:`CXX`, :envvar:`LDSHARED` and :envvar:`LDFLAGS`,
   :envvar:`CFLAGS`, :envvar:`CPPFLAGS`, :envvar:`LDFLAGS`,
 * the :class:`Extension` attributes ``include_dirs``,
   ``library_dirs``, ``extra_compile_args``, ``extra_link_args``,
   ``runtime_library_dirs``.

.. Ignoring AR, ARFLAGS, RANLIB here because they are used by the (obsolete?) build_clib, not build_ext.

The resulting command line is then processed by the compiler and linker.
According to the GCC manual sections on `directory options
<https://gcc.gnu.org/onlinedocs/gcc/Directory-Options.html>`_ and
`environment variables
<https://gcc.gnu.org/onlinedocs/gcc/Environment-Variables.html`_, the
C/C++ compiler searches for files named in ``#include <file>``
directives in the following order:

 * first, in directories given by ``-I`` options (in left-to-right order),
 * then, in directories given by the environment variable :envvar:`CPATH` (in left-to-right order),
 * then, in directories given by ``-isystem`` options (in left-to-right order),
 * then, in directories given by the environment variable :envvar:`C_INCLUDE_PATH` (for C) and :envvar:`CPLUS_INCLUDE_PATH` (for C++),
 * then, in standard system directories,
 * finally, in directories given by ``-idirafter`` options (in left-to-right order).

The linker searches for libraries in the following order:

 * first, in directories given by ``-L`` options (in left-to-right order),
 * then, in directories given by the environment variable :envvar:`LIBRARY_PATH` (in left-to-right order).
