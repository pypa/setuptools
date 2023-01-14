=====================================
Dependencies Management in Setuptools
=====================================

There are three types of dependency styles offered by setuptools:
1) build system requirement, 2) required dependency and 3) optional
dependency.

Each dependency, regardless of type, needs to be specified according to :pep:`508`
and :pep:`440`.
This allows adding version :pep:`range restrictions <440#version-specifiers>`
and :ref:`environment markers <environment-markers>`.


.. _build-requires:

Build system requirement
========================

After organizing all the scripts and files and getting ready for packaging,
there needs to be a way to specify what programs and libraries are actually needed
do the packaging (in our case, ``setuptools`` of course).
This needs to be specified in your ``pyproject.toml`` file
(if you have forgot what this is, go to :doc:`/userguide/quickstart` or :doc:`/build_meta`):

.. code-block:: toml

    [build-system]
    requires = ["setuptools"]
    #...

Please note that you should also include here any other ``setuptools`` plugin
(e.g., :pypi:`setuptools-scm`, :pypi:`setuptools-golang`, :pypi:`setuptools-rust`)
or build-time dependency (e.g., :pypi:`Cython`, :pypi:`cppy`, :pypi:`pybind11`).

.. note::
    In previous versions of ``setuptools``,
    this used to be accomplished with the ``setup_requires`` keyword but is
    now considered deprecated in favor of the :pep:`517` style described above.
    To peek into how this legacy keyword is used, consult our :doc:`guide on
    deprecated practice (WIP) </deprecated/index>`.


.. _Declaring Dependencies:

Declaring required dependency
=============================
This is where a package declares its core dependencies, without which it won't
be able to run. ``setuptools`` supports automatically downloading and installing
these dependencies when the package is installed. Although there is more
finesse to it, let's start with a simple example.

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        # ...
        dependencies = [
            "docutils",
            "BazSpam == 1.1",
        ]
        # ...

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


When your project is installed (e.g., using :pypi:`pip`), all of the dependencies not
already installed will be located (via `PyPI`_), downloaded, built (if necessary),
and installed and 2) Any scripts in your project will be installed with wrappers
that verify the availability of the specified dependencies at runtime.


.. _environment-markers:

Platform specific dependencies
------------------------------
Setuptools offers the capability to evaluate certain conditions before blindly
installing everything listed in ``install_requires``. This is great for platform
specific dependencies. For example, the ``enum`` package was added in Python
3.4, therefore, package that depends on it can elect to install it only when
the Python version is older than 3.4. To accomplish this

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        # ...
        dependencies = [
            "enum34; python_version<'3.4'",
        ]
        # ...

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

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        # ...
        dependencies = [
            "enum34; python_version<'3.4'",
            "pywin32 >= 1.0; platform_system=='Windows'",
        ]
        # ...

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
detailed in :pep:`508`.

.. seealso::
   If  environment markers are not enough an specific use case,
   you can also consider creating a :ref:`backend wrapper <backend-wrapper>`
   to implement custom detection logic.


Direct URL dependencies
-----------------------

.. attention::
   `PyPI`_ and other standards-conformant package indices **do not** accept
   packages that declare dependencies using direct URLs. ``pip`` will accept them
   when installing packages from the local filesystem or from another URL,
   however.

Dependencies that are not available on a package index but can be downloaded
elsewhere in the form of a source repository or archive may be specified
using a variant of :pep:`PEP 440's direct references <440#direct-references>`:

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        # ...
        dependencies = [
            "Package-A @ git+https://example.net/package-a.git@main",
            "Package-B @ https://example.net/archives/package-b.whl",
        ]

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        install_requires =
            Package-A @ git+https://example.net/package-a.git@main
            Package-B @ https://example.net/archives/package-b.whl

.. tab:: setup.py

    .. code-block:: python

        setup(
            install_requires=[
               "Package-A @ git+https://example.net/package-a.git@main",
               "Package-B @ https://example.net/archives/package-b.whl",
            ],
            ...,
        )

For source repository URLs, a list of supported protocols and VCS-specific
features such as selecting certain branches or tags can be found in pip's
documentation on `VCS support <https://pip.pypa.io/en/latest/topics/vcs-support/>`_.
Supported formats for archive URLs are sdists and wheels.


Optional dependencies
=====================
Setuptools allows you to declare dependencies that are not installed by default.
This effectively means that you can create a "variant" of your package with a
set of extra functionalities.

For example, let's consider a ``Package-A`` that offers
optional PDF support and requires two other dependencies for it to work:

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        name = "Package-A"
        # ...
        [project.optional-dependencies]
        PDF = ["ReportLab>=1.2", "RXP"]

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Package-A

        [options.extras_require]
        PDF =
            ReportLab>=1.2
            RXP


.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Package-A",
            ...,
            extras_require={
                "PDF": ["ReportLab>=1.2", "RXP"],
            },
        )

.. sidebar::

   .. tip::
      It is also convenient to declare optional requirements for
      ancillary tasks such as running tests and or building docs.

The name ``PDF`` is an arbitrary :pep:`identifier <685>` of such a list of dependencies, to
which other components can refer and have them installed.

A use case for this approach is that other package can use this "extra" for their
own dependencies. For example, if ``Package-B`` needs ``Package-A`` with PDF support
installed, it might declare the dependency like this:

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        name = "Package-B"
        # ...
        dependencies = [
            "Package-A[PDF]"
        ]

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Package-B
        #...

        [options]
        #...
        install_requires =
            Package-A[PDF]

.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Package-B",
            install_requires=["Package-A[PDF]"],
            ...,
        )

This will cause ``ReportLab`` to be installed along with ``Package-A``, if ``Package-B`` is
installed -- even if ``Package-A`` was already installed.  In this way, a project
can encapsulate groups of optional "downstream dependencies" under a feature
name, so that packages that depend on it don't have to know what the downstream
dependencies are.  If a later version of ``Package-A`` builds in PDF support and
no longer needs ``ReportLab``, or if it ends up needing other dependencies besides
``ReportLab`` in order to provide PDF support, ``Package-B``'s setup information does
not need to change, but the right packages will still be installed if needed.

.. tip::
    Best practice: if a project ends up no longer needing any other packages to
    support a feature, it should keep an empty requirements list for that feature
    in its ``extras_require`` argument, so that packages depending on that feature
    don't break (due to an invalid feature name).

.. warning::
    Historically ``setuptools`` also used to support extra dependencies in console
    scripts, for example:

    .. tab:: setup.cfg

        .. code-block:: ini

            [metadata]
            name = Package-A
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
                name="Package-A",
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
    (e.g., omit the console script, provide a warning when attempting to load
    the entry point, assume the extras are present and let the implementation
    fail later).

    **However**, ``pip`` and other tools might not support this use case for extra
    dependencies, therefore this practice is considered **deprecated**.
    See :doc:`PyPUG:specifications/entry-points`.


Python requirement
==================
In some cases, you might need to specify the minimum required python version.
This can be configured as shown in the example below.

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        name = "Package-B"
        requires-python = ">=3.6"
        # ...

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = Package-B
        #...

        [options]
        #...
        python_requires = >=3.6

.. tab:: setup.py

    .. code-block:: python

        setup(
            name="Package-B",
            python_requires=">=3.6",
            ...,
        )


.. _PyPI: https://pypi.org
