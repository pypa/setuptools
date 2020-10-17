====================
Data Files Support
====================

The distutils have traditionally allowed installation of "data files", which
are placed in a platform-specific location.  However, the most common use case
for data files distributed with a package is for use *by* the package, usually
by including the data files in the package directory.

Setuptools offers three ways to specify data files to be included in your
packages.  First, you can simply use the ``include_package_data`` keyword,
e.g.::

    from setuptools import setup, find_packages
    setup(
        ...
        include_package_data=True
    )

This tells setuptools to install any data files it finds in your packages.
The data files must be specified via the distutils' ``MANIFEST.in`` file.
(They can also be tracked by a revision control system, using an appropriate
plugin.  See the section below on :ref:`Adding Support for Revision
Control Systems` for information on how to write such plugins.)

If you want finer-grained control over what files are included (for example,
if you have documentation files in your package directories and want to exclude
them from installation), then you can also use the ``package_data`` keyword,
e.g.::

    from setuptools import setup, find_packages
    setup(
        ...
        package_data={
            # If any package contains *.txt or *.rst files, include them:
            "": ["*.txt", "*.rst"],
            # And include any *.msg files found in the "hello" package, too:
            "hello": ["*.msg"],
        }
    )

The ``package_data`` argument is a dictionary that maps from package names to
lists of glob patterns.  The globs may include subdirectory names, if the data
files are contained in a subdirectory of the package.  For example, if the
package tree looks like this::

    setup.py
    src/
        mypkg/
            __init__.py
            mypkg.txt
            data/
                somefile.dat
                otherdata.dat

The setuptools setup file might look like this::

    from setuptools import setup, find_packages
    setup(
        ...
        packages=find_packages("src"),  # include all packages under src
        package_dir={"": "src"},   # tell distutils packages are under src

        package_data={
            # If any package contains *.txt files, include them:
            "": ["*.txt"],
            # And include any *.dat files found in the "data" subdirectory
            # of the "mypkg" package, also:
            "mypkg": ["data/*.dat"],
        }
    )

Notice that if you list patterns in ``package_data`` under the empty string,
these patterns are used to find files in every package, even ones that also
have their own patterns listed.  Thus, in the above example, the ``mypkg.txt``
file gets included even though it's not listed in the patterns for ``mypkg``.

Also notice that if you use paths, you *must* use a forward slash (``/``) as
the path separator, even if you are on Windows.  Setuptools automatically
converts slashes to appropriate platform-specific separators at build time.

If datafiles are contained in a subdirectory of a package that isn't a package
itself (no ``__init__.py``), then the subdirectory names (or ``*``) are required
in the ``package_data`` argument (as shown above with ``"data/*.dat"``).

When building an ``sdist``, the datafiles are also drawn from the
``package_name.egg-info/SOURCES.txt`` file, so make sure that this is removed if
the ``setup.py`` ``package_data`` list is updated before calling ``setup.py``.

(Note: although the ``package_data`` argument was previously only available in
``setuptools``, it was also added to the Python ``distutils`` package as of
Python 2.4; there is `some documentation for the feature`__ available on the
python.org website.  If using the setuptools-specific ``include_package_data``
argument, files specified by ``package_data`` will *not* be automatically
added to the manifest unless they are listed in the MANIFEST.in file.)

__ https://docs.python.org/3/distutils/setupscript.html#installing-package-data

Sometimes, the ``include_package_data`` or ``package_data`` options alone
aren't sufficient to precisely define what files you want included.  For
example, you may want to include package README files in your revision control
system and source distributions, but exclude them from being installed.  So,
setuptools offers an ``exclude_package_data`` option as well, that allows you
to do things like this::

    from setuptools import setup, find_packages
    setup(
        ...
        packages=find_packages("src"),  # include all packages under src
        package_dir={"": "src"},   # tell distutils packages are under src

        include_package_data=True,    # include everything in source control

        # ...but exclude README.txt from all packages
        exclude_package_data={"": ["README.txt"]},
    )

The ``exclude_package_data`` option is a dictionary mapping package names to
lists of wildcard patterns, just like the ``package_data`` option.  And, just
as with that option, a key of ``""`` will apply the given pattern(s) to all
packages.  However, any files that match these patterns will be *excluded*
from installation, even if they were listed in ``package_data`` or were
included as a result of using ``include_package_data``.

In summary, the three options allow you to:

``include_package_data``
    Accept all data files and directories matched by ``MANIFEST.in``.

``package_data``
    Specify additional patterns to match files that may or may
    not be matched by ``MANIFEST.in`` or found in source control.

``exclude_package_data``
    Specify patterns for data files and directories that should *not* be
    included when a package is installed, even if they would otherwise have
    been included due to the use of the preceding options.

NOTE: Due to the way the distutils build process works, a data file that you
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
you should use the :ref:`ResourceManager API` of ``pkg_resources`` to access
them.  The ``pkg_resources`` module is distributed as part of setuptools, so if
you're using setuptools to distribute your package, there is no reason not to
use its resource management API.  See also `Importlib Resources`_ for
a quick example of converting code that uses ``__file__`` to use
``pkg_resources`` instead.

.. _Importlib Resources: https://docs.python.org/3/library/importlib.html#module-importlib.resources


Non-Package Data Files
----------------------

Historically, ``setuptools`` by way of ``easy_install`` would encapsulate data
files from the distribution into the egg (see `the old docs
<https://github.com/pypa/setuptools/blob/52aacd5b276fedd6849c3a648a0014f5da563e93/docs/setuptools.txt#L970-L1001>`_). As eggs are deprecated and pip-based installs
fall back to the platform-specific location for installing data files, there is
no supported facility to reliably retrieve these resources.

Instead, the PyPA recommends that any data files you wish to be accessible at
run time be included in the package.
