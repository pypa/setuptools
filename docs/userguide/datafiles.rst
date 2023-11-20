====================
Data Files Support
====================

Old packaging installation methods in the Python ecosystem
have traditionally allowed installation of "data files", which
are placed in a platform-specific location.  However, the most common use case
for data files distributed with a package is for use *by* the package, usually
by including the data files **inside the package directory**.

Setuptools focuses on this most common type of data files and offers three ways
of specifying which files should be included in your packages, as described in
the following sections.

include_package_data
====================

First, you can simply use the ``include_package_data`` keyword.
For example, if the package tree looks like this::

    project_root_directory
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── mypkg
            ├── __init__.py
            ├── data1.rst
            ├── data2.rst
            ├── data1.txt
            └── data2.txt

and you supply this configuration:

.. tab:: pyproject.toml

   .. code-block:: toml

        [tool.setuptools]
        # ...
        # By default, include-package-data is true in pyproject.toml, so you do
        # NOT have to specify this line.
        include-package-data = true

        [tool.setuptools.packages.find]
        where = ["src"]

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        packages = find:
        package_dir =
            = src
        include_package_data = True

        [options.packages.find]
        where = src

.. tab:: setup.py

   .. code-block:: python

    from setuptools import setup, find_packages
    setup(
        # ...,
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        include_package_data=True
    )

then all the ``.txt`` and ``.rst`` files will be automatically installed with
your package, provided:

1. These files are included via the :ref:`MANIFEST.in <Using MANIFEST.in>` file,
   like so::

        include src/mypkg/*.txt
        include src/mypkg/*.rst

2. OR, they are being tracked by a revision control system such as Git, Mercurial
   or SVN, and you have configured an appropriate plugin such as
   :pypi:`setuptools-scm` or :pypi:`setuptools-svn`.
   (See the section below on :ref:`Adding Support for Revision
   Control Systems` for information on how to write such plugins.)

.. note::
   .. versionadded:: v61.0.0
      The default value for ``tool.setuptools.include-package-data`` is ``True``
      when projects are configured via ``pyproject.toml``.
      This behaviour differs from ``setup.cfg`` and ``setup.py``
      (where ``include_package_data=False`` by default), which was not changed
      to ensure backwards compatibility with existing projects.

package_data
============

By default, ``include_package_data`` considers **all** non ``.py`` files found inside
the package directory (``src/mypkg`` in this case) as data files, and includes those that
satisfy (at least) one of the above two conditions into the source distribution, and
consequently in the installation of your package.
If you want finer-grained control over what files are included, then you can also use
the ``package_data`` keyword.
For example, if the package tree looks like this::

    project_root_directory
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── mypkg
            ├── __init__.py
            ├── data1.rst
            ├── data2.rst
            ├── data1.txt
            └── data2.txt

then you can use the following configuration to capture the ``.txt`` and ``.rst`` files as
data files:

.. tab:: pyproject.toml

   .. code-block:: toml

        [tool.setuptools.packages.find]
        where = ["src"]

        [tool.setuptools.package-data]
        mypkg = ["*.txt", "*.rst"]

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        packages = find:
        package_dir =
            = src

        [options.packages.find]
        where = src

        [options.package_data]
        mypkg =
            *.txt
            *.rst

.. tab:: setup.py

    .. code-block:: python

        from setuptools import setup, find_packages
        setup(
            # ...,
            packages=find_packages(where="src"),
            package_dir={"": "src"},
            package_data={"mypkg": ["*.txt", "*.rst"]}
        )

The ``package_data`` argument is a dictionary that maps from package names to
lists of glob patterns. Note that the data files specified using the ``package_data``
option neither require to be included within a :ref:`MANIFEST.in <Using MANIFEST.in>`
file, nor require to be added by a revision control system plugin.

.. note::
        If your glob patterns use paths, you *must* use a forward slash (``/``) as
        the path separator, even if you are on Windows.  Setuptools automatically
        converts slashes to appropriate platform-specific separators at build time.

.. important::
        Glob patterns do not automatically match dotfiles, i.e., directory or file names
        starting with a dot (``.``). To include such files, you must explicitly start
        the pattern with a dot, e.g. ``.*`` to match ``.gitignore``.

If you have multiple top-level packages and a common pattern of data files for all these
packages, for example::

    project_root_directory
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        ├── mypkg1
        │   ├── data1.rst
        │   ├── data1.txt
        │   └── __init__.py
        └── mypkg2
            ├── data2.txt
            └── __init__.py

Here, both packages ``mypkg1`` and ``mypkg2`` share a common pattern of having ``.txt``
data files. However, only ``mypkg1`` has ``.rst`` data files. In such a case, if you want to
use the ``package_data`` option, the following configuration will work:

.. tab:: pyproject.toml

   .. code-block:: toml

        [tool.setuptools.packages.find]
        where = ["src"]

        [tool.setuptools.package-data]
        "*" = ["*.txt"]
        mypkg1 = ["data1.rst"]

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        packages = find:
        package_dir =
            = src

        [options.packages.find]
        where = src

        [options.package_data]
        * =
          *.txt
        mypkg1 =
          data1.rst

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup, find_packages
        setup(
            # ...,
            packages=find_packages(where="src"),
            package_dir={"": "src"},
            package_data={"": ["*.txt"], "mypkg1": ["data1.rst"]},
        )

Notice that if you list patterns in ``package_data`` under the empty string ``""`` in
``setup.py``, and the asterisk ``*`` in ``setup.cfg`` and ``pyproject.toml``, these
patterns are used to find files in every package. For example, we use ``""`` or ``*``
to indicate that the ``.txt`` files from all packages should be captured as data files.
These placeholders are treated as a special case, ``setuptools`` **do not**
support glob patterns on package names for this configuration
(patterns are only supported on the file paths).
Also note how we can continue to specify patterns for individual packages, i.e.
we specify that ``data1.rst`` from ``mypkg1`` alone should be captured as well.

.. note::
    When building an ``sdist``, the data files are also drawn from the
    ``package_name.egg-info/SOURCES.txt`` file which works as a form of cache.
    So make sure that this file is removed if ``package_data`` is updated,
    before re-building the package.

.. attention::
   In Python any directory is considered a package
   (even if it does not contain ``__init__.py``,
   see *native namespaces packages* on :doc:`PyPUG:guides/packaging-namespace-packages`).
   Therefore, if you are not relying on :doc:`automatic discovery </userguide/package_discovery>`,
   you *SHOULD* ensure that **all** packages (including the ones that don't
   contain any Python files) are included in the ``packages`` configuration
   (see :doc:`/userguide/package_discovery` for more information).

   Moreover, it is advisable to use full packages name using the dot
   notation instead of a nested path, to avoid error prone configurations.
   Please check :ref:`section subdirectories <subdir-data-files>` below.


exclude_package_data
====================

Sometimes, the ``include_package_data`` or ``package_data`` options alone
aren't sufficient to precisely define what files you want included. For example,
consider a scenario where you have ``include_package_data=True``, and you are using
a revision control system with an appropriate plugin.
Sometimes developers add directory-specific marker files (such as ``.gitignore``,
``.gitkeep``, ``.gitattributes``, or ``.hgignore``), these files are probably being
tracked by the revision control system, and therefore by default they will be
included when the package is installed.

Supposing you want to prevent these files from being included in the
installation (they are not relevant to Python or the package), then you could
use the ``exclude_package_data`` option:

.. tab:: pyproject.toml

   .. code-block:: toml

        [tool.setuptools.packages.find]
        where = ["src"]

        [tool.setuptools.exclude-package-data]
        mypkg = [".gitattributes"]

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        packages = find:
        package_dir =
            = src
        include_package_data = True

        [options.packages.find]
        where = src

        [options.exclude_package_data]
        mypkg =
            .gitattributes

.. tab:: setup.py

    .. code-block:: python

        from setuptools import setup, find_packages
        setup(
            # ...,
            packages=find_packages(where="src"),
            package_dir={"": "src"},
            include_package_data=True,
            exclude_package_data={"mypkg": [".gitattributes"]},
        )

The ``exclude_package_data`` option is a dictionary mapping package names to
lists of wildcard patterns, just like the ``package_data`` option.  And, just
as with that option, you can use the empty string key ``""`` in ``setup.py`` and the
asterisk ``*`` in ``setup.cfg`` and ``pyproject.toml`` to match all top-level packages.

Any files that match these patterns will be *excluded* from installation,
even if they were listed in ``package_data`` or were included as a result of using
``include_package_data``.


.. _subdir-data-files:

Subdirectory for Data Files
===========================

A common pattern is where some (or all) of the data files are placed under
a separate subdirectory. For example::

    project_root_directory
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── mypkg
            ├── data
            │   ├── data1.rst
            │   └── data2.rst
            ├── __init__.py
            ├── data1.txt
            └── data2.txt

Here, the ``.rst`` files are placed under a ``data`` subdirectory inside ``mypkg``,
while the ``.txt`` files are directly under ``mypkg``.

In this case, the recommended approach is to treat ``data`` as a namespace package
(refer :pep:`420`). With ``package_data``,
the configuration might look like this:

.. tab:: pyproject.toml

   .. code-block:: toml

        # Scanning for namespace packages in the ``src`` directory is true by
        # default in pyproject.toml, so you do NOT need to include the
        # `tool.setuptools.packages.find` if it looks like the following:
        # [tool.setuptools.packages.find]
        # namespaces = true
        # where = ["src"]

        [tool.setuptools.package-data]
        mypkg = ["*.txt"]
        "mypkg.data" = ["*.rst"]

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        packages = find_namespace:
        package_dir =
            = src

        [options.packages.find]
        where = src

        [options.package_data]
        mypkg =
            *.txt
        mypkg.data =
            *.rst

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup, find_namespace_packages
        setup(
            # ...,
            packages=find_namespace_packages(where="src"),
            package_dir={"": "src"},
            package_data={
                "mypkg": ["*.txt"],
                "mypkg.data": ["*.rst"],
            }
        )

In other words, we allow Setuptools to scan for namespace packages in the ``src`` directory,
which enables the ``data`` directory to be identified, and then, we separately specify data
files for the root package ``mypkg``, and the namespace package ``data`` under the package
``mypkg``.

With ``include_package_data`` the configuration is simpler: you simply need to enable
scanning of namespace packages in the ``src`` directory and the rest is handled by Setuptools.

.. tab:: pyproject.toml

   .. code-block:: toml

        [tool.setuptools]
        # ...
        # By default, include-package-data is true in pyproject.toml, so you do
        # NOT have to specify this line.
        include-package-data = true

        [tool.setuptools.packages.find]
        # scanning for namespace packages is true by default in pyproject.toml, so
        # you need NOT include the following line.
        namespaces = true
        where = ["src"]

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        packages = find_namespace:
        package_dir =
            = src
        include_package_data = True

        [options.packages.find]
        where = src

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup, find_namespace_packages
        setup(
            # ... ,
            packages=find_namespace_packages(where="src"),
            package_dir={"": "src"},
            include_package_data=True,
        )

Summary
=======

In summary, the three options allow you to:

``include_package_data``
    Accept all data files and directories matched by
    :ref:`MANIFEST.in <Using MANIFEST.in>` or added by
    a :ref:`plugin <Adding Support for Revision Control Systems>`.

``package_data``
    Specify additional patterns to match files that may or may
    not be matched by :ref:`MANIFEST.in <Using MANIFEST.in>`
    or added by a :ref:`plugin <Adding Support for Revision Control Systems>`.

``exclude_package_data``
    Specify patterns for data files and directories that should *not* be
    included when a package is installed, even if they would otherwise have
    been included due to the use of the preceding options.

.. note::
    Due to the way the build process works, a data file that you
    include in your project and then stop including may be "orphaned" in your
    project's build directories, requiring you to manually deleting them.
    This may also be important for your users and contributors
    if they track intermediate revisions of your project using Subversion; be sure
    to let them know when you make changes that remove files from inclusion so they
    can also manually delete them.


.. _Accessing Data Files at Runtime:

Accessing Data Files at Runtime
===============================

Typically, existing programs manipulate a package's ``__file__`` attribute in
order to find the location of data files. For example, if you have a structure
like this::

    project_root_directory
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── mypkg
            ├── data
            │   └── data1.txt
            ├── __init__.py
            └── foo.py

Then, in ``mypkg/foo.py``, you may try something like this in order to access
``mypkg/data/data1.txt``:

.. code-block:: python

   import os
   data_path = os.path.join(os.path.dirname(__file__), 'data', 'data1.txt')
   with open(data_path, 'r') as data_file:
        ...

However, this manipulation isn't compatible with :pep:`302`-based import hooks,
including importing from zip files and Python Eggs.  It is strongly recommended that,
if you are using data files, you should use :mod:`importlib.resources` to access them.
In this case, you would do something like this:

.. code-block:: python

   from importlib.resources import files
   data_text = files('mypkg.data').joinpath('data1.txt').read_text()

:mod:`importlib.resources` was added to Python 3.7. However, the API illustrated in
this code (using ``files()``) was added only in Python 3.9, [#files_api]_ and support
for accessing data files via namespace packages was added only in Python 3.10 [#namespace_support]_
(the ``data`` subdirectory is a namespace package under the root package ``mypkg``).
Therefore, you may find this code to work only in Python 3.10 (and above). For other
versions of Python, you are recommended to use the :pypi:`importlib-resources` backport
which provides the latest version of this library. In this case, the only change that
has to be made to the above code is to replace ``importlib.resources`` with ``importlib_resources``, i.e.

.. code-block:: python

   from importlib_resources import files
   ...

See :doc:`importlib-resources:using` for detailed instructions.

.. tip:: Files inside the package directory should be *read-only* to avoid a
   series of common problems (e.g. when multiple users share a common Python
   installation, when the package is loaded from a zip file, or when multiple
   instances of a Python application run in parallel).

   If your Python package needs to write to a file for shared data or configuration,
   you can use standard platform/OS-specific system directories, such as
   ``~/.local/config/$appname`` or ``/usr/share/$appname/$version`` (Linux specific) [#system-dirs]_.
   A common approach is to add a read-only template file to the package
   directory that is then copied to the correct system directory if no
   pre-existing file is found.


Data Files from Plugins and Extensions
======================================

You can resort to a :doc:`native/implicit namespace package
<PyPUG:guides/packaging-namespace-packages>` (as a container for files)
if you want plugins and extensions to your package to contribute with package data files.
This way, all files will be listed during runtime
when :doc:`using importlib.resources <importlib-resources:using>`.
Note that, although not strictly guaranteed, mainstream Python package managers,
like :pypi:`pip` and derived tools, will install files belong to multiple distributions
that share a same namespace into the same directory in the file system.
This means that the overhead for :mod:`importlib.resources` will be minimum.


Non-Package Data Files
======================

Historically, ``setuptools`` by way of ``easy_install`` would encapsulate data
files from the distribution into the egg (see `the old docs
<https://github.com/pypa/setuptools/blob/52aacd5b276fedd6849c3a648a0014f5da563e93/docs/setuptools.txt#L970-L1001>`_). As eggs are deprecated and pip-based installs
fall back to the platform-specific location for installing data files, there is
no supported facility to reliably retrieve these resources.

Instead, the PyPA recommends that any data files you wish to be accessible at
run time be included **inside the package**.


----

.. [#system-dirs] These locations can be discovered with the help of
   third-party libraries such as :pypi:`platformdirs`.

.. [#files_api] Reference: https://importlib-resources.readthedocs.io/en/latest/using.html#migrating-from-legacy

.. [#namespace_support] Reference: https://github.com/python/importlib_resources/pull/196#issuecomment-734520374
