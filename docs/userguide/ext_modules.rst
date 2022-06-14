==========================
Building Extension Modules
==========================

Setuptools can build C/C++ extension modules.  The keyword argument
``ext_modules`` of ``setup`` should be a list of instances of the
:class:`setuptools.Extension` class.


Compiler and linker options
===========================

The command ``build_ext`` builds C/C++ extension modules.  It creates
a command line for running the compiler and linker by combining
compiler and linker options from various sources:

.. Reference: `test_customize_compiler` in distutils/tests/test_sysconfig.py

* the ``sysconfig`` variables ``CC``, ``CXX``, ``CCSHARED``,
  ``LDSHARED``, and ``CFLAGS``,
* the environment variables ``CC``, ``CPP``,
  ``CXX``, ``LDSHARED`` and ``LDFLAGS``,
  ``CFLAGS``, ``CPPFLAGS``, ``LDFLAGS``,
* the ``Extension`` attributes ``include_dirs``,
  ``library_dirs``, ``extra_compile_args``, ``extra_link_args``,
  ``runtime_library_dirs``.

.. Ignoring AR, ARFLAGS, RANLIB here because they are used by the (obsolete?) build_clib, not build_ext.

The resulting command line is then processed by the compiler and linker.
According to the GCC manual sections on `directory options`_ and
`environment variables`_, the C/C++ compiler searches for files named in
``#include <file>`` directives in the following order:

* first, in directories given by ``-I`` options (in left-to-right order),
* then, in directories given by the environment variable ``CPATH`` (in left-to-right order),
* then, in directories given by ``-isystem`` options (in left-to-right order),
* then, in directories given by the environment variable ``C_INCLUDE_PATH`` (for C) and ``CPLUS_INCLUDE_PATH`` (for C++),
* then, in standard system directories,
* finally, in directories given by ``-idirafter`` options (in left-to-right order).

The linker searches for libraries in the following order:

* first, in directories given by ``-L`` options (in left-to-right order),
* then, in directories given by the environment variable ``LIBRARY_PATH`` (in left-to-right order).


----

API Reference
-------------

.. autoclass:: setuptools.Extension


.. _Python docs about C/C++ extensions: https://docs.python.org/3/extending/extending.html
.. _Cython: https://cython.readthedocs.io/en/stable/index.html
.. _directory options: https://gcc.gnu.org/onlinedocs/gcc/Directory-Options.html
.. _environment variables: https://gcc.gnu.org/onlinedocs/gcc/Environment-Variables.html>
