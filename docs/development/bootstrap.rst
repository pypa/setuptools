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

The ``setuptools._bootstrap`` tool is a modest bare-bones implementation
that follows the :pep:`PyPA's build-system spec <517>`,
simplified and stripped down to only support the ``setuptools`` package.

This procedure is not intended for other packages, it will not
provide the same guarantees as a proper Python package installer
or build-frontend tool, and it is still experimental.

The naming intentionally uses a ``_`` character to discourage
regular users, as the tool is only provided for developers (or downstream packaging
consumers) that need to deploy ``setuptools`` from scratch.

This is a CLI-only implementation, with no API provided.
Users interested in API usage are invited to follow :pep:`PyPA's build-system spec <517>`.
