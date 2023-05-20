==========================
Building Extension Modules
==========================

Setuptools can build C/C++ extension modules.  The keyword argument
``ext_modules`` of ``setup()`` should be a list of instances of the
:class:`setuptools.Extension` class.


For example, let's consider a simple project with only one extension module::

    <project_folder>
    ├── pyproject.toml
    └── foo.c

and all project metadata configuration in the ``pyproject.toml`` file:

.. code-block:: toml

   # pyproject.toml
   [build-system]
   requires = ["setuptools"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "mylib-foo"  # as it would appear on PyPI
   version = "0.42"

To instruct setuptools to compile the ``foo.c`` file into the extension module
``mylib.foo``, we need to add a ``setup.py`` file similar to the following:

.. code-block:: python

   from setuptools import Extension, setup

   setup(
       ext_modules=[
           Extension(
               name="mylib.foo",  # as it would be imported
                                  # may include packages/namespaces separated by `.`

               sources=["foo.c"], # all sources are compiled into a single binary file
           ),
       ]
   )

.. seealso::
   You can find more information on the `Python docs about C/C++ extensions`_.
   Alternatively, you might also be interested in learning about `Cython`_.

   If you plan to distribute a package that uses extensions across multiple
   platforms, :pypi:`cibuildwheel` can also be helpful.

.. important::
   All files used to compile your extension need to be available on the system
   when building the package, so please make sure to include some documentation
   on how developers interested in building your package from source
   can obtain operating system level dependencies
   (e.g. compilers and external binary libraries/artifacts).

   You will also need to make sure that all auxiliary files that are contained
   inside your :term:`project` (e.g. C headers authored by you or your team)
   are configured to be included in your :term:`sdist <Source Distribution (or "sdist")>`.
   Please have a look on our section on :ref:`Controlling files in the distribution`.


Compiler and linker options
===========================

The command ``build_ext`` builds C/C++ extension modules.  It creates
a command line for running the compiler and linker by combining
compiler and linker options from various sources:

.. Reference: `test_customize_compiler` in distutils/tests/test_sysconfig.py

* the ``sysconfig`` variables ``CC``, ``CXX``, ``CCSHARED``,
  ``LDSHARED``, and ``CFLAGS``,
* the environment variables ``CC``, ``CPP``,
  ``CXX``, ``LDSHARED`` and ``CFLAGS``,
  ``CPPFLAGS``, ``LDFLAGS``,
* the ``Extension`` attributes ``include_dirs``,
  ``library_dirs``, ``extra_compile_args``, ``extra_link_args``,
  ``runtime_library_dirs``.

.. Ignoring AR, ARFLAGS, RANLIB here because they are used by the (obsolete?) build_clib, not build_ext.

Specifically, if the environment variables ``CC``, ``CPP``, ``CXX``, and ``LDSHARED``
are set, they will be used instead of the ``sysconfig`` variables of the same names.

The compiler options appear in the command line in the following order:

.. Reference: "compiler_so" and distutils.ccompiler.gen_preprocess_options, CCompiler.compile, UnixCCompiler._compile

* first, the options provided by the ``sysconfig`` variable ``CFLAGS``,
* then, the options provided by the environment variables ``CFLAGS`` and ``CPPFLAGS``,
* then, the options provided by the ``sysconfig`` variable ``CCSHARED``,
* then, a ``-I`` option for each element of ``Extension.include_dirs``,
* finally, the options provided by ``Extension.extra_compile_args``.

The linker options appear in the command line in the following order:

.. Reference: "linker_so" and CCompiler.link

* first, the options provided by environment variables and ``sysconfig`` variables,
* then, a ``-L`` option for each element of ``Extension.library_dirs``,
* then, a linker-specific option like ``-Wl,-rpath`` for each element of ``Extension.runtime_library_dirs``,
* finally, the options provided by ``Extension.extra_link_args``.

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


Distributing Extensions compiled with Cython
============================================

When your :pypi:`Cython` extension modules *are declared using the*
:class:`setuptools.Extension` *class*, ``setuptools`` will detect at build time
whether Cython is installed or not.

If Cython is present, then ``setuptools`` will use it to build the ``.pyx`` files.
Otherwise, ``setuptools`` will try to find and compile the equivalent ``.c`` files
(instead of ``.pyx``). These files can be generated using the
`cython command line tool`_.

You can ensure that Cython is always automatically installed into the build
environment by including it as a :ref:`build dependency <build-requires>` in
your ``pyproject.toml``:

.. code-block:: toml

    [build-system]
    requires = [..., "cython"]

Alternatively, you can include the ``.c`` code that is pre-compiled by Cython
into your source distribution, alongside the original ``.pyx`` files (this
might save a few seconds when building from an ``sdist``).
To improve version compatibility, you probably also want to include current
``.c`` files in your :wiki:`revision control system`, and rebuild them whenever
you check changes in for the ``.pyx`` source files.
This will ensure that people tracking your project will be able to build it
without installing Cython, and that there will be no variation due to small
differences in the generate C files.
Please checkout our docs on :ref:`controlling files in the distribution` for
more information.

----

Extension API Reference
=======================

.. autoclass:: setuptools.Extension


.. _Python docs about C/C++ extensions: https://docs.python.org/3/extending/extending.html
.. _Cython: https://cython.readthedocs.io/en/stable/index.html
.. _directory options: https://gcc.gnu.org/onlinedocs/gcc/Directory-Options.html
.. _environment variables: https://gcc.gnu.org/onlinedocs/gcc/Environment-Variables.html
.. _cython command line tool: https://cython.readthedocs.io/en/stable/src/userguide/source_files_and_compilation.html
