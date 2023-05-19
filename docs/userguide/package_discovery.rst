.. _`package_discovery`:

========================================
Package Discovery and Namespace Packages
========================================

.. note::
    a full specification for the keywords supplied to ``setup.cfg`` or
    ``setup.py`` can be found at :doc:`keywords reference </references/keywords>`

.. important::
    The examples provided here are only to demonstrate the functionality
    introduced. More metadata and options arguments need to be supplied
    if you want to replicate them on your system. If you are completely
    new to setuptools, the :doc:`quickstart` section is a good place to start.

``Setuptools`` provides powerful tools to handle package discovery, including
support for namespace packages.

Normally, you would specify the packages to be included manually in the following manner:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        packages =
            mypkg
            mypkg.subpkg1
            mypkg.subpkg2

.. tab:: setup.py

    .. code-block:: python

        setup(
            # ...
            packages=['mypkg', 'mypkg.subpkg1', 'mypkg.subpkg2']
        )

.. tab:: pyproject.toml (**BETA**) [#beta]_

    .. code-block:: toml

        # ...
        [tool.setuptools]
        packages = ["mypkg", "mypkg.subpkg1", "mypkg.subpkg2"]
        # ...


If your packages are not in the root of the repository or do not correspond
exactly to the directory structure, you also need to configure ``package_dir``:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        # ...
        package_dir =
            = src
            # directory containing all the packages (e.g.  src/mypkg, src/mypkg/subpkg1, ...)
        # OR
        package_dir =
            mypkg = lib
            # mypkg.module corresponds to lib/module.py
            mypkg.subpkg1 = lib1
            # mypkg.subpkg1.module1 corresponds to lib1/module1.py
            mypkg.subpkg2 = lib2
            # mypkg.subpkg2.module2 corresponds to lib2/module2.py
        # ...

.. tab:: setup.py

    .. code-block:: python

        setup(
            # ...
            package_dir = {"": "src"}
            # directory containing all the packages (e.g.  src/mypkg, src/mypkg/subpkg1, ...)
        )

        # OR

        setup(
            # ...
            package_dir = {
                "mypkg": "lib",  # mypkg.module corresponds to lib/mod.py
                "mypkg.subpkg1": "lib1",  # mypkg.subpkg1.module1 corresponds to lib1/module1.py
                "mypkg.subpkg2": "lib2"   # mypkg.subpkg2.module2 corresponds to lib2/module2.py
                # ...
        )

.. tab:: pyproject.toml (**BETA**) [#beta]_

    .. code-block:: toml

        [tool.setuptools]
        # ...
        package-dir = {"" = "src"}
            # directory containing all the packages (e.g.  src/mypkg1, src/mypkg2)

        # OR

        [tool.setuptools.package-dir]
        mypkg = "lib"
        # mypkg.module corresponds to lib/module.py
        "mypkg.subpkg1" = "lib1"
        # mypkg.subpkg1.module1 corresponds to lib1/module1.py
        "mypkg.subpkg2" = "lib2"
        # mypkg.subpkg2.module2 corresponds to lib2/module2.py
        # ...

This can get tiresome really quickly. To speed things up, you can rely on
setuptools automatic discovery, or use the provided tools, as explained in
the following sections.

.. important::
   Although ``setuptools`` allows developers to create a very complex mapping
   between directory names and package names, it is better to *keep it simple*
   and reflect the desired package hierarchy in the directory structure,
   preserving the same names.

.. _auto-discovery:

Automatic discovery
===================

.. warning:: Automatic discovery is a **beta** feature and might change in the future.
   See :ref:`custom-discovery` for other methods of discovery.

By default ``setuptools`` will consider 2 popular project layouts, each one with
its own set of advantages and disadvantages [#layout1]_ [#layout2]_ as
discussed in the following sections.

Setuptools will automatically scan your project directory looking for these
layouts and try to guess the correct values for the :ref:`packages <declarative
config>` and :doc:`py_modules </references/keywords>` configuration.

.. important::
   Automatic discovery will **only** be enabled if you **don't** provide any
   configuration for ``packages`` and ``py_modules``.
   If at least one of them is explicitly set, automatic discovery will not take place.

   **Note**: specifying ``ext_modules`` might also prevent auto-discover from
   taking place, unless your opt into :doc:`pyproject_config` (which will
   disable the backward compatible behaviour).

.. _src-layout:

src-layout
----------
The project should contain a ``src`` directory under the project root and
all modules and packages meant for distribution are placed inside this
directory::

    project_root_directory
    ├── pyproject.toml  # AND/OR setup.cfg, setup.py
    ├── ...
    └── src/
        └── mypkg/
            ├── __init__.py
            ├── ...
            ├── module.py
            ├── subpkg1/
            │   ├── __init__.py
            │   ├── ...
            │   └── module1.py
            └── subpkg2/
                ├── __init__.py
                ├── ...
                └── module2.py

This layout is very handy when you wish to use automatic discovery,
since you don't have to worry about other Python files or folders in your
project root being distributed by mistake. In some circumstances it can be
also less error-prone for testing or when using :pep:`420`-style packages.
On the other hand you cannot rely on the implicit ``PYTHONPATH=.`` to fire
up the Python REPL and play with your package (you will need an
`editable install`_ to be able to do that).

.. _flat-layout:

flat-layout
-----------
*(also known as "adhoc")*

The package folder(s) are placed directly under the project root::

    project_root_directory
    ├── pyproject.toml  # AND/OR setup.cfg, setup.py
    ├── ...
    └── mypkg/
        ├── __init__.py
        ├── ...
        ├── module.py
        ├── subpkg1/
        │   ├── __init__.py
        │   ├── ...
        │   └── module1.py
        └── subpkg2/
            ├── __init__.py
            ├── ...
            └── module2.py

This layout is very practical for using the REPL, but in some situations
it can be more error-prone (e.g. during tests or if you have a bunch
of folders or Python files hanging around your project root).

To avoid confusion, file and folder names that are used by popular tools (or
that correspond to well-known conventions, such as distributing documentation
alongside the project code) are automatically filtered out in the case of
*flat-layout*:

.. autoattribute:: setuptools.discovery.FlatLayoutPackageFinder.DEFAULT_EXCLUDE

.. autoattribute:: setuptools.discovery.FlatLayoutModuleFinder.DEFAULT_EXCLUDE

.. warning::
   If you are using auto-discovery with *flat-layout*, ``setuptools`` will
   refuse to create :term:`distribution archives <Distribution Package>` with
   multiple top-level packages or modules.

   This is done to prevent common errors such as accidentally publishing code
   not meant for distribution (e.g. maintenance-related scripts).

   Users that purposefully want to create multi-package distributions are
   advised to use :ref:`custom-discovery` or the ``src-layout``.

There is also a handy variation of the *flat-layout* for utilities/libraries
that can be implemented with a single Python file:

single-module distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^

A standalone module is placed directly under the project root, instead of
inside a package folder::

    project_root_directory
    ├── pyproject.toml  # AND/OR setup.cfg, setup.py
    ├── ...
    └── single_file_lib.py


.. _custom-discovery:

Custom discovery
================

If the automatic discovery does not work for you
(e.g., you want to *include* in the distribution top-level packages with
reserved names such as ``tasks``, ``example`` or ``docs``, or you want to
*exclude* nested packages that would be otherwise included), you can use
the provided tools for package discovery:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        packages = find:
        #or
        packages = find_namespace:

.. tab:: setup.py

    .. code-block:: python

        from setuptools import find_packages
        # or
        from setuptools import find_namespace_packages

.. tab:: pyproject.toml (**BETA**) [#beta]_

    .. code-block:: toml

        # ...
        [tool.setuptools.packages]
        find = {}  # Scanning implicit namespaces is active by default
        # OR
        find = {namespaces = false}  # Disable implicit namespaces


Finding simple packages
-----------------------
Let's start with the first tool. ``find:`` (``find_packages()``) takes a source
directory and two lists of package name patterns to exclude and include, and
then returns a list of ``str`` representing the packages it could find. To use
it, consider the following directory::

    mypkg
    ├── pyproject.toml  # AND/OR setup.cfg, setup.py
    └── src
        ├── pkg1
        │   └── __init__.py
        ├── pkg2
        │   └── __init__.py
        ├── additional
        │   └── __init__.py
        └── pkg
            └── namespace
                └── __init__.py

To have setuptools to automatically include packages found
in ``src`` that start with the name ``pkg`` and not ``additional``:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        packages = find:
        package_dir =
            =src

        [options.packages.find]
        where = src
        include = pkg*
        # alternatively: `exclude = additional*`

    .. note::
        ``pkg`` does not contain an ``__init__.py`` file, therefore
        ``pkg.namespace`` is ignored by ``find:`` (see ``find_namespace:`` below).

.. tab:: setup.py

    .. code-block:: python

        setup(
            # ...
            packages=find_packages(
                where='src',
                include=['pkg*'],  # alternatively: `exclude=['additional*']`
            ),
            package_dir={"": "src"}
            # ...
        )


    .. note::
        ``pkg`` does not contain an ``__init__.py`` file, therefore
        ``pkg.namespace`` is ignored by ``find_packages()``
        (see ``find_namespace_packages()`` below).

.. tab:: pyproject.toml (**BETA**) [#beta]_

    .. code-block:: toml

        [tool.setuptools.packages.find]
        where = ["src"]
        include = ["pkg*"]  # alternatively: `exclude = ["additional*"]`
        namespaces = false

    .. note::
        When using ``tool.setuptools.packages.find`` in ``pyproject.toml``,
        setuptools will consider :pep:`implicit namespaces <420>` by default when
        scanning your project directory.
        To avoid ``pkg.namespace`` from being added to your package list
        you can set ``namespaces = false``. This will prevent any folder
        without an ``__init__.py`` file from being scanned.

.. important::
   ``include`` and ``exclude`` accept strings representing :mod:`glob` patterns.
   These patterns should match the **full** name of the Python module (as if it
   was written in an ``import`` statement).

   For example if you have ``util`` pattern, it will match
   ``util/__init__.py`` but not ``util/files/__init__.py``.

   The fact that the parent package is matched by the pattern will not dictate
   if the submodule will be included or excluded from the distribution.
   You will need to explicitly add a wildcard (e.g. ``util*``)
   if you want the pattern to also match submodules.

.. _Namespace Packages:

Finding namespace packages
--------------------------
``setuptools``  provides ``find_namespace:`` (``find_namespace_packages()``)
which behaves similarly to ``find:`` but works with namespace packages.

Before diving in, it is important to have a good understanding of what
:pep:`namespace packages <420>` are. Here is a quick recap.

When you have two packages organized as follows:

.. code-block:: bash

    /Users/Desktop/timmins/foo/__init__.py
    /Library/timmins/bar/__init__.py

If both ``Desktop`` and ``Library`` are on your ``PYTHONPATH``, then a
namespace package called ``timmins`` will be created automatically for you when
you invoke the import mechanism, allowing you to accomplish the following:

.. code-block:: pycon

    >>> import timmins.foo
    >>> import timmins.bar

as if there is only one ``timmins`` on your system. The two packages can then
be distributed separately and installed individually without affecting the
other one.

Now, suppose you decide to package the ``foo`` part for distribution and start
by creating a project directory organized as follows::

   foo
   ├── pyproject.toml  # AND/OR setup.cfg, setup.py
   └── src
       └── timmins
           └── foo
               └── __init__.py

If you want the ``timmins.foo`` to be automatically included in the
distribution, then you will need to specify:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        package_dir =
            =src
        packages = find_namespace:

        [options.packages.find]
        where = src

    ``find:`` won't work because ``timmins`` doesn't contain ``__init__.py``
    directly, instead, you have to use ``find_namespace:``.

    You can think of ``find_namespace:`` as identical to ``find:`` except it
    would count a directory as a package even if it doesn't contain ``__init__.py``
    file directly.

.. tab:: setup.py

    .. code-block:: python

        setup(
            # ...
            packages=find_namespace_packages(where='src'),
            package_dir={"": "src"}
            # ...
        )

    When you use ``find_packages()``, all directories without an
    ``__init__.py`` file will be disconsidered.
    On the other hand, ``find_namespace_packages()`` will scan all
    directories.

.. tab:: pyproject.toml (**BETA**) [#beta]_

    .. code-block:: toml

        [tool.setuptools.packages.find]
        where = ["src"]

    When using ``tool.setuptools.packages.find`` in ``pyproject.toml``,
    setuptools will consider :pep:`implicit namespaces <420>` by default when
    scanning your project directory.

After installing the package distribution, ``timmins.foo`` would become
available to your interpreter.

.. warning::
   Please have in mind that ``find_namespace:`` (setup.cfg),
   ``find_namespace_packages()`` (setup.py) and ``find`` (pyproject.toml) will
   scan **all** folders that you have in your project directory if you use a
   :ref:`flat-layout`.

   If used naïvely, this might result in unwanted files being added to your
   final wheel. For example, with a project directory organized as follows::

       foo
       ├── docs
       │   └── conf.py
       ├── timmins
       │   └── foo
       │       └── __init__.py
       └── tests
           └── tests_foo
               └── __init__.py

   final users will end up installing not only ``timmins.foo``, but also
   ``docs`` and ``tests.tests_foo``.

   A simple way to fix this is to adopt the aforementioned :ref:`src-layout`,
   or make sure to properly configure the ``include`` and/or ``exclude``
   accordingly.

.. tip::
   After :ref:`building your package <building>`, you can have a look if all
   the files are correct (nothing missing or extra), by running the following
   commands:

   .. code-block:: bash

      tar tf dist/*.tar.gz
      unzip -l dist/*.whl

   This requires the ``tar`` and ``unzip`` to be installed in your OS.
   On Windows you can also use a GUI program such as 7zip_.


Legacy Namespace Packages
=========================
The fact you can create namespace packages so effortlessly above is credited
to :pep:`420`. It used to be more
cumbersome to accomplish the same result. Historically, there were two methods
to create namespace packages. One is the ``pkg_resources`` style supported by
``setuptools`` and the other one being ``pkgutils`` style offered by
``pkgutils`` module in Python. Both are now considered *deprecated* despite the
fact they still linger in many existing packages. These two differ in many
subtle yet significant aspects and you can find out more on `Python packaging
user guide <https://packaging.python.org/guides/packaging-namespace-packages/>`_.


``pkg_resource`` style namespace package
----------------------------------------
This is the method ``setuptools`` directly supports. Starting with the same
layout, there are two pieces you need to add to it. First, an ``__init__.py``
file directly under your namespace package directory that contains the
following:

.. code-block:: python

    __import__("pkg_resources").declare_namespace(__name__)

And the ``namespace_packages`` keyword in your ``setup.cfg`` or ``setup.py``:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        namespace_packages = timmins

.. tab:: setup.py

    .. code-block:: python

        setup(
            # ...
            namespace_packages=['timmins']
        )

And your directory should look like this

.. code-block:: bash

   foo
   ├── pyproject.toml  # AND/OR setup.cfg, setup.py
   └── src
       └── timmins
           ├── __init__.py
           └── foo
               └── __init__.py

Repeat the same for other packages and you can achieve the same result as
the previous section.

``pkgutil`` style namespace package
-----------------------------------
This method is almost identical to the ``pkg_resource`` except that the
``namespace_packages`` declaration is omitted and the ``__init__.py``
file contains the following:

.. code-block:: python

    __path__ = __import__('pkgutil').extend_path(__path__, __name__)

The project layout remains the same and ``pyproject.toml/setup.cfg`` remains the same.


----


.. [#beta]
   Support for adding build configuration options via the ``[tool.setuptools]``
   table in the ``pyproject.toml`` file is still in **beta** stage.
   See :doc:`/userguide/pyproject_config`.
.. [#layout1] https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure
.. [#layout2] https://blog.ionelmc.ro/2017/09/25/rehashing-the-src-layout/

.. _editable install: https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs
.. _7zip: https://www.7-zip.org
