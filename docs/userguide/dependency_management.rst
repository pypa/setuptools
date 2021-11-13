=====================================
Dependencies Management in Setuptools
=====================================

There are three types of dependency styles offered by setuptools:
1) build system requirement, 2) required dependency and 3) optional
dependency.

.. Note::
    Packages that are added to dependency can be optionally specified with the
    version by following `PEP 440 <https://www.python.org/dev/peps/pep-0440/>`_


Build system requirement
========================

Package requirement
-------------------
After organizing all the scripts and files and getting ready for packaging,
there needs to be a way to tell Python what programs it needs to actually
do the packaging (in our case, ``setuptools`` of course). Usually,
you also need the ``wheel`` package as well since it is recommended that you
upload a ``.whl`` file to PyPI alongside your ``.tar.gz`` file. Unlike the
other two types of dependency keyword, this one is specified in your
``pyproject.toml`` file (if you have forgot what this is, go to
:doc:`quickstart` or (WIP)):

.. code-block:: ini

    [build-system]
    requires = ["setuptools", "wheel"]
    #...

.. note::
    This used to be accomplished with the ``setup_requires`` keyword but is
    now considered deprecated in favor of the PEP 517 style described above.
    To peek into how this legacy keyword is used, consult our :doc:`guide on
    deprecated practice (WIP) <../deprecated/index>`


.. _Declaring Dependencies:

Declaring required dependency
=============================
This is where a package declares its core dependencies, without which it won't
be able to run. ``setuptools`` support automatically download and install
these dependencies when the package is installed. Although there is more
finesse to it, let's start with a simple example.

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        install_requires =
            docutils
            BazSpam ==1.1

.. tab:: setup.py

    .. code-block:: python

        setup(
            ...,
            install_requires=[
                'docutils',
                'BazSpam ==1.1',
            ],
        )


When your project is installed (e.g. using pip), all of the dependencies not
already installed will be located (via PyPI), downloaded, built (if necessary),
and installed and 2) Any scripts in your project will be installed with wrappers
that verify the availability of the specified dependencies at runtime.


Platform specific dependencies
------------------------------
Setuptools offer the capability to evaluate certain conditions before blindly
installing everything listed in ``install_requires``. This is great for platform
specific dependencies. For example, the ``enum`` package was added in Python
3.4, therefore, package that depends on it can elect to install it only when
the Python version is older than 3.4. To accomplish this

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        install_requires =
            enum34;python_version<'3.4'

.. tab:: setup.py

    .. code-block:: python

        setup(
            ...,
            install_requires=[
                "enum34;python_version<'3.4'",
            ],
        )

Similarly, if you also wish to declare ``pywin32`` with a minimal version of 1.0
and only install it if the user is using a Windows operating system:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        install_requires =
            enum34;python_version<'3.4'
            pywin32 >= 1.0;platform_system=='Windows'

.. tab:: setup.py

    .. code-block:: python

        setup(
            ...,
            install_requires=[
                "enum34;python_version<'3.4'",
                "pywin32 >= 1.0;platform_system=='Windows'",
            ],
        )

The environmental markers that may be used for testing platform types are
detailed in `PEP 508 <https://www.python.org/dev/peps/pep-0508/>`_.


Dependencies that aren't in PyPI
--------------------------------
.. warning::
    Dependency links support has been dropped by pip starting with version
    19.0 (released 2019-01-22).

If your project depends on packages that don't exist on PyPI, you may still be
able to depend on them, as long as they are available for download as:

- an egg, in the standard distutils ``sdist`` format,
- a single ``.py`` file, or
- a VCS repository (Subversion, Mercurial, or Git).

You just need to add some URLs to the ``dependency_links`` argument to
``setup()``.

The URLs must be either:

1. direct download URLs,
2. the URLs of web pages that contain direct download links, or
3. the repository's URL

In general, it's better to link to web pages, because it is usually less
complex to update a web page than to release a new version of your project.
You can also use a SourceForge ``showfiles.php`` link in the case where a
package you depend on is distributed via SourceForge.

If you depend on a package that's distributed as a single ``.py`` file, you
must include an ``"#egg=project-version"`` suffix to the URL, to give a project
name and version number.  (Be sure to escape any dashes in the name or version
by replacing them with underscores.)  EasyInstall will recognize this suffix
and automatically create a trivial ``setup.py`` to wrap the single ``.py`` file
as an egg.

In the case of a VCS checkout, you should also append ``#egg=project-version``
in order to identify for what package that checkout should be used. You can
append ``@REV`` to the URL's path (before the fragment) to specify a revision.
Additionally, you can also force the VCS being used by prepending the URL with
a certain prefix. Currently available are:

-  ``svn+URL`` for Subversion,
-  ``git+URL`` for Git, and
-  ``hg+URL`` for Mercurial

A more complete example would be:

    ``vcs+proto://host/path@revision#egg=project-version``

Be careful with the version. It should match the one inside the project files.
If you want to disregard the version, you have to omit it both in the
``requires`` and in the URL's fragment.

This will do a checkout (or a clone, in Git and Mercurial parlance) to a
temporary folder and run ``setup.py bdist_egg``.

The ``dependency_links`` option takes the form of a list of URL strings.  For
example, this will cause a search of the specified page for eggs or source
distributions, if the package's dependencies aren't already installed:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        dependency_links = http://peak.telecommunity.com/snapshots/

.. tab:: setup.py

    .. code-block:: python

        setup(
            ...,
            dependency_links=[
                "http://peak.telecommunity.com/snapshots/",
            ],
        )


Optional dependencies
=====================
Setuptools allows you to declare dependencies that only get installed under
specific circumstances. These dependencies are specified with ``extras_require``
keyword and are only installed if another package depends on it (either
directly or indirectly) This makes it convenient to declare dependencies for
ancillary functions such as "tests" and "docs".

.. note::
    ``tests_require`` is now deprecated

For example, Package-A offers optional PDF support and requires two other
dependencies for it to work:

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Package-A

        [options.extras_require]
        PDF = ReportLab>=1.2; RXP


.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Project-A",
            ...,
            extras_require={
                "PDF": ["ReportLab>=1.2", "RXP"],
            },
        )

The name ``PDF`` is an arbitrary identifier of such a list of dependencies, to
which other components can refer and have them installed. There are two common
use cases.

First is the console_scripts entry point:

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Project A
        #...

        [options]
        #...
        entry_points=
            [console_scripts]
            rst2pdf = project_a.tools.pdfgen [PDF]
            rst2html = project_a.tools.htmlgen

.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Project-A",
            ...,
            entry_points={
                "console_scripts": [
                    "rst2pdf = project_a.tools.pdfgen [PDF]",
                    "rst2html = project_a.tools.htmlgen",
                ],
            },
        )

This syntax indicates that the entry point (in this case a console script)
is only valid when the PDF extra is installed. It is up to the installer
to determine how to handle the situation where PDF was not indicated
(e.g. omit the console script, provide a warning when attempting to load
the entry point, assume the extras are present and let the implementation
fail later).

The second use case is that other package can use this "extra" for their
own dependencies. For example, if "Project-B" needs "project A" with PDF support
installed, it might declare the dependency like this:

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Project-B
        #...

        [options]
        #...
        install_requires =
            Project-A[PDF]

.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Project-B",
            install_requires=["Project-A[PDF]"],
            ...,
        )

This will cause ReportLab to be installed along with project A, if project B is
installed -- even if project A was already installed.  In this way, a project
can encapsulate groups of optional "downstream dependencies" under a feature
name, so that packages that depend on it don't have to know what the downstream
dependencies are.  If a later version of Project A builds in PDF support and
no longer needs ReportLab, or if it ends up needing other dependencies besides
ReportLab in order to provide PDF support, Project B's setup information does
not need to change, but the right packages will still be installed if needed.

.. note::
    Best practice: if a project ends up not needing any other packages to
    support a feature, it should keep an empty requirements list for that feature
    in its ``extras_require`` argument, so that packages depending on that feature
    don't break (due to an invalid feature name).


Python requirement
==================
In some cases, you might need to specify the minimum required python version.
This is handled with the ``python_requires`` keyword supplied to ``setup.cfg``
or ``setup.py``.


.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Project-B
        #...

        [options]
        #...
        python_requires = >=3.6

.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Project-B",
            python_requires=[">=3.6"],
            ...,
        )
