==========================
``setuptools`` Quickstart
==========================

Installation
============

To install the latest version of setuptools, use::

    pip install --upgrade setuptools


Python packaging at a glance
============================
The landscape of Python packaging is shifting and ``Setuptools`` has evolved to
only provide backend support, no longer being the de-facto packaging tool in
the market. Every python package must provide a ``pyproject.toml`` and specify
the backend (build system) it wants to use. The distribution can then
be generated with whatever tool that provides a ``build sdist``-like
functionality. While this may appear cumbersome, given the added pieces,
it in fact tremendously enhances the portability of your package. The
change is driven under :pep:`PEP 517 <517#build-requirements>`. To learn more about Python packaging in general,
navigate to the :ref:`bottom <packaging-resources>` of this page.


Basic Use
=========
For basic use of setuptools, you will need a ``pyproject.toml`` with the
exact following info, which declares you want to use ``setuptools`` to
package your project:

.. code-block:: toml

    [build-system]
    requires = ["setuptools"]
    build-backend = "setuptools.build_meta"

Then, you will need to specify your package information such as metadata,
contents, dependencies, etc.

Setuptools currently supports configurations from either ``setup.cfg``,
``setup.py`` or ``pyproject.toml`` [#experimental]_ files, however, configuring new
projects via ``setup.py`` is discouraged [#setup.py]_.

The following example demonstrates a minimum configuration:

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = mypackage
        version = 0.0.1

        [options]
        packages = mypackage
        install_requires =
            requests
            importlib-metadata; python_version < "3.8"

    See :doc:`/userguide/declarative_config` for more information.

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        from setuptools import setup

        setup(
            name='mypackage',
            version='0.0.1',
            packages=['mypackage'],
            install_requires=[
                'requests',
                'importlib-metadata; python_version == "3.8"',
            ],
        )

    See :doc:`/references/keywords` for more information.

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

    .. code-block:: toml

       [project]
       name = "mypackage"
       version = "0.0.1"
       dependencies = [
           "requests",
           'importlib-metadata; python_version<"3.8"',
       ]

    See :doc:`/userguide/pyproject_config` for more information.

This is what your project would look like::

    ~/mypackage/
        pyproject.toml
        setup.cfg # or setup.py
        mypackage/__init__.py

Then, you need a builder, such as :std:doc:`PyPA build <pypa-build:index>`
which you can obtain via ``pip install build``. After downloading it, invoke
the builder::

    python -m build

You now have your distribution ready (e.g. a ``tar.gz`` file and a ``.whl``
file in the ``dist`` directory), which you can upload to PyPI!

Of course, before you release your project to PyPI, you'll want to add a bit
more information to your setup script to help people find or learn about your
project.  And maybe your project will have grown by then to include a few
dependencies, and perhaps some data files and scripts. In the next few sections,
we will walk through the additional but essential information you need
to specify to properly package your project.


Automatic package discovery
===========================
For simple projects, it's usually easy enough to manually add packages to
the ``packages`` keyword in ``setup.cfg``.  However, for very large projects,
it can be a big burden to keep the package list updated.
Therefore, ``setuptoops`` provides a convenient way to automatically list all
the packages in your project directory:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        packages = find: # OR `find_namespaces:` if you want to use namespaces

        [options.packages.find] (always `find` even if `find_namespaces:` was used before)
        # This section is optional
        # Each entry in this section is optional, and if not specified, the default values are:
        # `where=.`, `include=*` and `exclude=` (empty).
        include=mypackage*
        exclude=mypackage.tests*

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        from setuptools import find_packages  # or find_namespace_packages

        setup(
            # ...
            packages=find_packages(
                where='.',
                include=['mypackage*'],  # ["*"] by default
                exclude=['mypackage.tests'],  # empty by default
            ),
            # ...
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

    .. code-block:: toml

        # ...
        [tool.setuptools.packages]
        find = {}  # Scan the project directory with the default parameters

        # OR
        [tool.setuptools.packages.find]
        where = ["src"]  # ["."] by default
        include = ["mypackage*"]  # ["*"] by default
        exclude = ["mypackage.tests*"]  # empty by default
        namespaces = false  # true by default

When you pass the above information, alongside other necessary information,
``setuptools`` walks through the directory specified in ``where`` (omitted
here as the package resides in the current directory) and filters the packages
it can find following the ``include``  (defaults to none), then removes
those that match the ``exclude`` and returns a list of Python packages. The above
setup also allows you to adopt a ``src/`` layout. For more details and advanced
use, go to :ref:`package_discovery`.

.. tip::
   Starting with version 61.0.0, setuptools' automatic discovery capabilities
   have been improved to detect popular project layouts (such as the
   :ref:`flat-layout` and :ref:`src-layout`) without requiring any
   special configuration. Check out our :ref:`reference docs <package_discovery>`
   for more information, but please keep in mind that this functionality is
   still considered **experimental** and might change (or even be removed) in
   future releases.


Entry points and automatic script creation
===========================================
Setuptools supports automatic creation of scripts upon installation, that runs
code within your package if you specify them as :doc:`entry points
<PyPUG:specifications/entry-points>`.
This is what allows you to run commands like ``pip install`` instead of having
to type ``python -m pip install``.
The following configuration examples show how to accomplish this:

.. tab:: setup.cfg

    .. code-block:: ini

        [options.entry_points]
        console_scripts =
            cli-name = mypkg.mymodule:some_func

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        setup(
            # ...
            entry_points={
                'console_scripts': [
                    'cli-name = mypkg.mymodule:some_func',
                ]
            }
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

    .. code-block:: toml

       [project.scripts]
       cli-name = "mypkg.mymodule:some_func"

When this project is installed, a ``cli-name`` executable will be created.
``cli-name`` will invoke the function ``some_func`` in the
``mypkg/mymodule.py`` file when called by the user.
Note that you can also use the ``entry-points`` mechanism to advertise
components between installed packages and implement plugin systems.
For detailed usage, go to :doc:`entry_point`.


Dependency management
=====================
Packages built with ``setuptools`` can specify dependencies to be automatically
installed when the package itself is installed.
The example below show how to configure this kind of dependencies:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        install_requires =
            docutils
            requests <= 0.4

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        setup(
            # ...
            install_requires=["docutils", "requests <= 0.4"],
            # ...
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

    .. code-block:: toml

        [project]
        # ...
        dependencies = [
            "docutils",
            "requires <= 0.4",
        ]
        # ...

Each dependency is represented by a string that can optionally contain version requirements
(e.g. one of the operators <, >, <=, >=, == or !=, followed by a version identifier),
and/or conditional environment markers, e.g. ``sys_platform == "win32"``
(see :doc:`PyPUG:specifications/version-specifiers` for more information).

When your project is installed, all of the dependencies not already installed
will be located (via PyPI), downloaded, built (if necessary), and installed.
This, of course, is a simplified scenario. You can also specify groups of
extra dependencies that are not strictly required by your package to work, but
that will provide additional functionalities.
For more advanced use, see :doc:`dependency_management`.


.. _Including Data Files:

Including Data Files
====================
The distutils have traditionally allowed installation of "data files", which
are placed in a platform-specific location. Setuptools offers three ways to
specify data files to be included in your packages. For the simplest use, you
can simply use the ``include_package_data`` keyword:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        include_package_data = True

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        setup(
            # ...
            include_package_data=True,
            # ...
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

    .. code-block:: toml

        [tool.setuptools]
        include-package-data = true
        # This is already the default behaviour if your are using
        # pyproject.toml to configure your build.
        # You can deactivate that with `include-package-data = false`

This tells setuptools to install any data files it finds in your packages.
The data files must be specified via the distutils' |MANIFEST.in|_ file
or automatically added by a :ref:`Revision Control System plugin
<Adding Support for Revision Control Systems>`.
For more details, see :doc:`datafiles`.


Development mode
================

``setuptools`` allows you to install a package without copying any files
to your interpreter directory (e.g. the ``site-packages`` directory).
This allows you to modify your source code and have the changes take
effect without you having to rebuild and reinstall.
Here's how to do it::

    pip install --editable .

This creates a link file in your interpreter site package directory which
associate with your source code. For more information, see :doc:`development_mode`.

.. tip::

    Prior to :ref:`pip v21.1 <pip:v21-1>`, a ``setup.py`` script was
    required to be compatible with development mode. With late
    versions of pip, ``setup.cfg``-only projects may be installed in this mode.

    If you are experimenting with :doc:`configuration using <pyproject_config>`,
    or have version of ``pip`` older than v21.1, you might need to keep a
    ``setup.py`` file in file in your repository if you want to use editable
    installs (for the time being).

    A simple script will suffice, for example:

    .. code-block:: python

        from setuptools import setup

        setup()

    You can still keep all the configuration in :doc:`setup.cfg </userguide/declarative_config>`
    (or :doc:`pyproject.toml </userguide/pyproject_config>`).


Uploading your package to PyPI
==============================
After generating the distribution files, the next step would be to upload your
distribution so others can use it. This functionality is provided by
:pypi:`twine` and is documented in the :doc:`Python packaging tutorial
<PyPUG:tutorials/packaging-projects>`.


Transitioning from ``setup.py`` to ``setup.cfg``
================================================
To avoid executing arbitrary scripts and boilerplate code, we are transitioning
into a full-fledged ``setup.cfg`` to declare your package information instead
of running ``setup()``. This inevitably brings challenges due to a different
syntax. :doc:`Here </userguide/declarative_config>` we provide a quick guide to
understanding how ``setup.cfg`` is parsed by ``setuptools`` to ease the pain of
transition.

.. _packaging-resources:

Resources on Python packaging
=============================
Packaging in Python can be hard and is constantly evolving.
`Python Packaging User Guide <https://packaging.python.org>`_ has tutorials and
up-to-date references that can help you when it is time to distribute your work.


.. |MANIFEST.in| replace:: ``MANIFEST.in``
.. _MANIFEST.in: https://packaging.python.org/en/latest/guides/using-manifest-in/


----

.. rubric:: Notes

.. [#setup.py]
   The ``setup.py`` file should be used only when custom scripting during the
   build is necessary.
   Examples are kept in this document to help people interested in maintaining or
   contributing to existing packages that use ``setup.py``.
   Note that you can still keep most of configuration declarative in
   :doc:`setup.cfg <declarative_config>` or :doc:`pyproject.toml
   <pyproject_config>` and use ``setup.py`` only for the parts not
   supported in those files (e.g. C extensions).

.. [#experimental]
   While the ``[build-system]`` table should always be specified in the
   ``pyproject.toml`` file, support for adding package metadata and build configuration
   options via the ``[project]`` and ``[tool.setuptools]`` tables is still
   experimental and might change (or be completely removed) in future releases.
   See :doc:`/userguide/pyproject_config`.
