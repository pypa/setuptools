----------------------------
Bootstrapping ``setuptools``
----------------------------

If you need to *build* ``setuptools`` without the help of any third party tool
(like :pypi:`build` or :pypi:`pip`), you can use the following procedure:

1. Obtain ``setuptools``'s source code and change to the project root directory.
   For example::

        $ git clone https://github.com/pypa/setuptools
        $ cd setuptools

2. Run the bootstrap utility with the version of Python you intend to use
   ``setuptools`` with::

        $ python3 -m setuptools._bootstrap

   This will create a :term:`setuptools-*.whl <PyPUG:Wheel>` file in the ``./dist`` directory.

Furthermore, if you also need to bootstrap the *installation* of ``setuptools``,
you can follow the additional steps:

3. Find out the directory where Python expects packages to be installed.
   The following command can help with that::

       $ python3 -m sysconfig

   Since ``setuptools`` is a pure-Python distribution,
   usually you will only need the path referring to ``purelib``.

4. Extract the created ``.whl`` file into the relevant directory.
   For example::

      $ python3 -m zipfile -e ./dist/setuptools-*.whl $TARGET_DIR


Notes
~~~~~

This procedure assumes that you have access to a fully functional Python
installation, including the standard library.

The ``setuptools._bootstrap`` tools is still experimental
and it is named with a ``_`` character because it is not intended for general
use, only in the cases when developers (or downstream packaging consumers)
need to deploy ``setuptools`` from scratch.

This is a CLI-only tool, with no API provided.
Users interested in API usage are invited to follow :pep:`PyPA's build-system spec <517>`.
