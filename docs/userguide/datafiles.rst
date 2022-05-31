====================
Data Files Support
====================

The distutils have traditionally allowed installation of "data files", which
are placed in a platform-specific location.  However, the most common use case
for data files distributed with a package is for use *by* the package, usually
by including the data files **inside the package directory**.

Setuptools offers three ways to specify this most common type of data files to
be included in your package's [#datafiles]_.
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

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        include_package_data = True

.. tab:: setup.py

   .. code-block:: python

    from setuptools import setup
    setup(
        # ...,
        include_package_data=True
    )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [tool.setuptools]
        # ...
        # By default, include-package-data is true in pyproject.toml, so you do
        # NOT have to specify this line.
        include-package-data = true

then all the ``.txt`` and ``.rst`` files will be automatically installed with
your package, provided:

1. These files are included via the |MANIFEST.in|_ file, like so::

        include src/mypkg/*.txt
        include src/mypkg/*.rst

2. OR, they are being tracked by a revision control system such as Git, Mercurial
   or SVN, and you have configured an appropriate plugin such as
   :pypi:`setuptools-scm` or :pypi:`setuptools-svn`.
   (See the section below on :ref:`Adding Support for Revision
   Control Systems` for information on how to write such plugins.)

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

You can use the following configuration to capture the ``.txt`` and ``.rst`` files as
data files:

.. tab:: setup.cfg

   .. code-block:: ini

        # ...
        [options.package_data]
        mypkg =
            *.txt
            *.rst

.. tab:: setup.py

    .. code-block:: python

        from setuptools import setup
        setup(
            # ...,
            package_data={"mypkg": ["*.txt", "*.rst"]}
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        # ...
        [tool.setuptools.package_data]
        mypkg = ["*.txt", "*.rst"]

The ``package_data`` argument is a dictionary that maps from package names to
lists of glob patterns.  The globs may include subdirectory names, if the data
files are contained in a subdirectory of the package.  For example, if the
package tree looks like this::

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

The configuration might look like this:

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        packages =
            mypkg
        package_dir =
            mypkg = src

        [options.package_data]
        mypkg =
            *.txt
            data/*.rst

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup
        setup(
            # ...,
            packages=["mypkg"],
            package_dir={"mypkg": "src"},
            package_data={"mypkg": ["*.txt", "data/*.rst"]}
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [tool.setuptools]
        # ...
        packages = ["mypkg"]
        package-dir = { mypkg = "src" }

        [tool.setuptools.package-data]
        mypkg = ["*.txt", "data/*.rst"]

In other words, if datafiles are contained in a subdirectory of a package that isn't a
package itself (no ``__init__.py``), then the subdirectory names (or ``*`` to include
all subdirectories) are required in the ``package_data`` argument (as shown above with
``"data/*.rst"``).

If you have multiple top-level packages and a common pattern of data files for both packages, for example::

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

then you can supply a configuration like this to capture both ``mypkg1/data1.txt`` and
``mypkg2/data2.txt``, as well as ``mypkg1/data1.rst``.

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        packages = 
            mypkg1
            mypkg2
        package_dir =
            mypkg1 = src
            mypkg2 = src

        [options.package_data]
        * =
          *.txt
        mypkg1 =
          data1.rst

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup
        setup(
            # ...,
            packages=["mypkg1", "mypkg2"],
            package_dir={"mypkg1": "src", "mypkg2": "src"},
            package_data={"": ["*.txt"], "mypkg1": ["data1.rst"]},
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [tool.setuptools]
        # ...
        packages = ["mypkg1", "mypkg2"]
        package-dir = { mypkg1 = "src", mypkg2 = "src" }
        
        [tool.setuptools.package-data]
        "*" = ["*.txt"]
        mypkg1 = ["data1.rst"]

Notice that if you list patterns in ``package_data`` under the empty string ``""`` in
``setup.py``, and the asterisk ``*`` in ``setup.cfg`` and ``pyproject.toml``, these
patterns are used to find files in every package. For example, both files
``mypkg1/data1.txt`` and ``mypkg2/data2.txt`` are captured as data files. Also note
how other patterns specified for individual packages continue to work, i.e.
``mypkg1/data1.rst`` is captured as well.

Also notice that if you use paths, you *must* use a forward slash (``/``) as
the path separator, even if you are on Windows.  Setuptools automatically
converts slashes to appropriate platform-specific separators at build time.

.. note::
    When building an ``sdist``, the datafiles are also drawn from the
    ``package_name.egg-info/SOURCES.txt`` file, so make sure that this is removed if
    the ``setup.py`` ``package_data`` list is updated before calling ``setup.py``.

.. note::
   If using the ``include_package_data`` argument, files specified by
   ``package_data`` will *not* be automatically added to the manifest unless
   they are listed in the |MANIFEST.in|_ file or by a plugin like
   :pypi:`setuptools-scm` or :pypi:`setuptools-svn`.

.. https://docs.python.org/3/distutils/setupscript.html#installing-package-data

Sometimes, the ``include_package_data`` or ``package_data`` options alone
aren't sufficient to precisely define what files you want included.  For
example, you may want to include package README files in your revision control
system and source distributions, but exclude them from being installed.  So,
setuptools offers an ``exclude_package_data`` option as well, that allows you
to do things like this:

.. tab:: setup.cfg

   .. code-block:: ini

        [options]
        # ...
        packages =
            mypkg
        package_dir =
            mypkg = src
        include_package_data = True

        [options.exclude_package_data]
        mypkg =
            README.txt

.. tab:: setup.py

    .. code-block:: python

        from setuptools import setup
        setup(
            # ...,
            packages=["mypkg"],
            package_dir={"mypkg": "src"},
            include_package_data=True,
            exclude_package_data={"mypkg": ["README.txt"]},
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [tool.setuptools]
        # ...
        packages = ["mypkg"]
        package-dir = { mypkg = "src" }

        [tool.setuptools.exclude-package-data]
        mypkg = ["README.txt"]

The ``exclude_package_data`` option is a dictionary mapping package names to
lists of wildcard patterns, just like the ``package_data`` option.  And, just
as with that option, you can use the empty string key ``""`` in ``setup.py`` and the
asterisk ``*`` in ``setup.cfg`` and ``pyproject.toml`` to match all top-level packages.
However, any files that match these patterns will be *excluded* from installation,
even if they were listed in ``package_data`` or were included as a result of using
``include_package_data``.

In summary, the three options allow you to:

``include_package_data``
    Accept all data files and directories matched by |MANIFEST.in|_ or added by
    a :ref:`plugin <Adding Support for Revision Control Systems>`.

``package_data``
    Specify additional patterns to match files that may or may
    not be matched by |MANIFEST.in|_ or added by
    a :ref:`plugin <Adding Support for Revision Control Systems>`.

``exclude_package_data``
    Specify patterns for data files and directories that should *not* be
    included when a package is installed, even if they would otherwise have
    been included due to the use of the preceding options.

.. note::
    Due to the way the distutils build process works, a data file that you
    include in your project and then stop including may be "orphaned" in your
    project's build directories, requiring you to run ``setup.py clean --all`` to
    fully remove them.  This may also be important for your users and contributors
    if they track intermediate revisions of your project using Subversion; be sure
    to let them know when you make changes that remove files from inclusion so they
    can run ``setup.py clean --all``.


.. _Accessing Data Files at Runtime:

Accessing Data Files at Runtime
-------------------------------

Typically, existing programs manipulate a package's ``__file__`` attribute in
order to find the location of data files.  However, this manipulation isn't
compatible with PEP 302-based import hooks, including importing from zip files
and Python Eggs.  It is strongly recommended that, if you are using data files,
you should use :mod:`importlib.resources` to access them.
:mod:`importlib.resources` was added to Python 3.7 and the latest version of
the library is also available via the :pypi:`importlib-resources` backport.
See :doc:`importlib-resources:using` for detailed instructions [#importlib]_.

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


Non-Package Data Files
----------------------

Historically, ``setuptools`` by way of ``easy_install`` would encapsulate data
files from the distribution into the egg (see `the old docs
<https://github.com/pypa/setuptools/blob/52aacd5b276fedd6849c3a648a0014f5da563e93/docs/setuptools.txt#L970-L1001>`_). As eggs are deprecated and pip-based installs
fall back to the platform-specific location for installing data files, there is
no supported facility to reliably retrieve these resources.

Instead, the PyPA recommends that any data files you wish to be accessible at
run time be included **inside the package**.


----

.. [#experimental]
   Support for specifying package metadata and build configuration options via
   ``pyproject.toml`` is experimental and might change
   in the future. See :doc:`/userguide/pyproject_config`.

.. [#datafiles] ``setuptools`` consider a *package data file* any non-Python
   file **inside the package directory** (i.e., that co-exists in the same
   location as the regular ``.py`` files being distributed).

.. [#system-dirs] These locations can be discovered with the help of
   third-party libraries such as :pypi:`platformdirs`.

.. [#importlib] Recent versions of :mod:`importlib.resources` available in
   Pythons' standard library should be API compatible with
   :pypi:`importlib-metadata`. However this might vary depending on which version
   of Python is installed.


.. |MANIFEST.in| replace:: ``MANIFEST.in``
.. _MANIFEST.in: https://packaging.python.org/en/latest/guides/using-manifest-in/
