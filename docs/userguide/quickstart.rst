==========
Quickstart
==========

Installation
============

You can install the latest version of ``setuptools`` using :pypi:`pip`::

    pip install --upgrade setuptools

Most of the times, however, you don't have to...

Instead, when creating new Python packages, it is recommended to use
a command line tool called :pypi:`build`. This tool will automatically download
``setuptools`` and any other build-time dependencies that your project might
have. You just need to specify them in a ``pyproject.toml`` file at the root of
your package, as indicated in the :ref:`following section <basic-use>`.

.. _install-build:

You can also :doc:`install build <build:installation>` using :pypi:`pip`::

    pip install --upgrade build

This will allow you to run the command: ``python -m build``.

.. important::
   Please note that some operating systems might be equipped with
   the ``python3`` and ``pip3`` commands instead of ``python`` and ``pip``
   (but they should be equivalent).
   If you don't have ``pip`` or ``pip3`` available in your system, please
   check out :doc:`pip installation docs <pip:installation>`.


Every python package must provide a ``pyproject.toml`` and specify
the backend (build system) it wants to use. The distribution can then
be generated with whatever tool that provides a ``build sdist``-like
functionality.


.. _basic-use:

Basic Use
=========

When creating a Python package, you must provide a ``pyproject.toml`` file
containing a ``build-system`` section similar to the example below:

.. code-block:: toml

    [build-system]
    requires = ["setuptools"]
    build-backend = "setuptools.build_meta"

This section declares what are your build system dependencies, and which
library will be used to actually do the packaging.

.. note::

   Historically this documentation has unnecessarily listed ``wheel``
   in the ``requires`` list, and many projects still do that. This is
   not recommended. The backend automatically adds ``wheel`` dependency
   when it is required, and listing it explicitly causes it to be
   unnecessarily required for source distribution builds.
   You should only include ``wheel`` in ``requires`` if you need to explicitly
   access it during build time (e.g. if your project needs a ``setup.py``
   script that imports ``wheel``).

In addition to specifying a build system, you also will need to add
some package information such as metadata, contents, dependencies, etc.
This can be done in the same ``pyproject.toml`` file,
or in a separated one: ``setup.cfg`` or ``setup.py`` [#setup.py]_.

The following example demonstrates a minimum configuration
(which assumes the project depends on :pypi:`requests` and
:pypi:`importlib-metadata` to be able to run):

.. tab:: pyproject.toml

    .. code-block:: toml

       [project]
       name = "mypackage"
       version = "0.0.1"
       dependencies = [
           "requests",
           'importlib-metadata; python_version<"3.10"',
       ]

    See :doc:`/userguide/pyproject_config` for more information.

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = mypackage
        version = 0.0.1

        [options]
        install_requires =
            requests
            importlib-metadata; python_version<"3.10"


    See :doc:`/userguide/declarative_config` for more information.

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        from setuptools import setup

        setup(
            name='mypackage',
            version='0.0.1',
            install_requires=[
                'requests',
                'importlib-metadata; python_version<"3.10"',
            ],
        )

    See :doc:`/references/keywords` for more information.

Finally, you will need to organize your Python code to make it ready for
distributing into something that looks like the following
(optional files marked with ``#``)::

    mypackage
    ├── pyproject.toml  # and/or setup.cfg/setup.py (depending on the configuration method)
    |   # README.rst or README.md (a nice description of your package)
    |   # LICENCE (properly chosen license information, e.g. MIT, BSD-3, GPL-3, MPL-2, etc...)
    └── mypackage
        ├── __init__.py
        └── ... (other Python files)

With :ref:`build installed in your system <install-build>`, you can then run::

    python -m build

You now have your distribution ready (e.g. a ``tar.gz`` file and a ``.whl`` file
in the ``dist`` directory), which you can :doc:`upload <twine:index>` to PyPI_!

Of course, before you release your project to PyPI_, you'll want to add a bit
more information to help people find or learn about your project.
And maybe your project will have grown by then to include a few
dependencies, and perhaps some data files and scripts. In the next few sections,
we will walk through the additional but essential information you need
to specify to properly package your project.


..
   TODO: A previous generation of this document included a section called
   "Python packaging at a glance". This is a nice title, but the content
   removed because it assumed the reader had familiarity with the history of
   setuptools and PEP 517. We should take advantage of this nice title and add
   this section back, but use it to explain important concepts of the
   ecosystem, such as "sdist", "wheel", "index". It would also be nice if we
   could have a diagram for that (explaining for example that "wheels" are
   built from "sdists" not the source tree).

.. _setuppy_discouraged:
.. admonition:: Info: Using ``setup.py``
  :class: seealso

  Setuptools offers first class support for ``setup.py`` files as a configuration
  mechanism.

  It is important to remember, however, that running this file as a
  script (e.g. ``python setup.py sdist``) is strongly **discouraged**, and
  that the majority of the command line interfaces are (or will be) **deprecated**
  (e.g. ``python setup.py install``, ``python setup.py bdist_wininst``, ...).

  We also recommend users to expose as much as possible configuration in a
  more *declarative* way via the :doc:`pyproject.toml <pyproject_config>` or
  :doc:`setup.cfg <declarative_config>`, and keep the ``setup.py`` minimal
  with only the dynamic parts (or even omit it completely if applicable).

  See `Why you shouldn't invoke setup.py directly`_ for more background.

.. _Why you shouldn't invoke setup.py directly: https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html


Overview
========

Package discovery
-----------------
For projects that follow a simple directory structure, ``setuptools`` should be
able to automatically detect all :term:`packages <package>` and
:term:`namespaces <namespace>`. However, complex projects might include
additional folders and supporting files that not necessarily should be
distributed (or that can confuse ``setuptools`` auto discovery algorithm).

Therefore, ``setuptools`` provides a convenient way to customize
which packages should be distributed and in which directory they should be
found, as shown in the example below:

.. tab:: pyproject.toml

    .. code-block:: toml

        # ...
        [tool.setuptools.packages]
        find = {}  # Scan the project directory with the default parameters

        # OR
        [tool.setuptools.packages.find]
        # All the following settings are optional:
        where = ["src"]  # ["."] by default
        include = ["mypackage*"]  # ["*"] by default
        exclude = ["mypackage.tests*"]  # empty by default
        namespaces = false  # true by default

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        packages = find: # OR `find_namespace:` if you want to use namespaces

        [options.packages.find]  # (always `find` even if `find_namespace:` was used before)
        # This section is optional as well as each of the following options:
        where=src  # . by default
        include=mypackage*  # * by default
        exclude=mypackage.tests*  # empty by default

.. tab:: setup.py [#setup.py]_

    .. code-block:: python

        from setuptools import setup, find_packages  # or find_namespace_packages

        setup(
            # ...
            packages=find_packages(
                # All keyword arguments below are optional:
                where='src',  # '.' by default
                include=['mypackage*'],  # ['*'] by default
                exclude=['mypackage.tests'],  # empty by default
            ),
            # ...
        )

When you pass the above information, alongside other necessary information,
``setuptools`` walks through the directory specified in ``where`` (defaults to ``.``) and filters the packages
it can find following the ``include`` patterns (defaults to ``*``), then it removes
those that match the ``exclude`` patterns (defaults to empty) and returns a list of Python packages.

For more details and advanced use, go to :ref:`package_discovery`.

.. tip::
   Starting with version 61.0.0, setuptools' automatic discovery capabilities
   have been improved to detect popular project layouts (such as the
   :ref:`flat-layout` and :ref:`src-layout`) without requiring any
   special configuration. Check out our :ref:`reference docs <package_discovery>`
   for more information.


Entry points and automatic script creation
-------------------------------------------
Setuptools supports automatic creation of scripts upon installation, that run
code within your package if you specify them as :doc:`entry points
<PyPUG:specifications/entry-points>`.
An example of how this feature can be used in ``pip``:
it allows you to run commands like ``pip install`` instead of having
to type ``python -m pip install``.

The following configuration examples show how to accomplish this:


.. tab:: pyproject.toml

    .. code-block:: toml

       [project.scripts]
       cli-name = "mypkg.mymodule:some_func"

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

When this project is installed, a ``cli-name`` executable will be created.
``cli-name`` will invoke the function ``some_func`` in the
``mypkg/mymodule.py`` file when called by the user.
Note that you can also use the ``entry-points`` mechanism to advertise
components between installed packages and implement plugin systems.
For detailed usage, go to :doc:`entry_point`.


Dependency management
---------------------
Packages built with ``setuptools`` can specify dependencies to be automatically
installed when the package itself is installed.
The example below shows how to configure this kind of dependencies:

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        # ...
        dependencies = [
            "docutils",
            "requests <= 0.4",
        ]
        # ...

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
--------------------
Setuptools offers three ways to specify data files to be included in your packages.
For the simplest use, you can simply use the ``include_package_data`` keyword:

.. tab:: pyproject.toml

    .. code-block:: toml

        [tool.setuptools]
        include-package-data = true
        # This is already the default behaviour if you are using
        # pyproject.toml to configure your build.
        # You can deactivate that with `include-package-data = false`

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

This tells setuptools to install any data files it finds in your packages.
The data files must be specified via the :ref:`MANIFEST.in <Using MANIFEST.in>`
file or automatically added by a :ref:`Revision Control System plugin
<Adding Support for Revision Control Systems>`.
For more details, see :doc:`datafiles`.


Development mode
----------------

``setuptools`` allows you to install a package without copying any files
to your interpreter directory (e.g. the ``site-packages`` directory).
This allows you to modify your source code and have the changes take
effect without you having to rebuild and reinstall.
Here's how to do it::

    pip install --editable .

See :doc:`development_mode` for more information.

.. tip::

    Prior to :ref:`pip v21.1 <pip:v21-1>`, a ``setup.py`` script was
    required to be compatible with development mode. With late
    versions of pip, projects without ``setup.py`` may be installed in this mode.

    If you have a version of ``pip`` older than v21.1 or is using a different
    packaging-related tool that does not support :pep:`660`, you might need to keep a
    ``setup.py`` file in your repository if you want to use editable
    installs.

    A simple script will suffice, for example:

    .. code-block:: python

        from setuptools import setup

        setup()

    You can still keep all the configuration in
    :doc:`pyproject.toml </userguide/pyproject_config>` and/or
    :doc:`setup.cfg </userguide/declarative_config>`

.. note::

    When building from source code (for example, by ``python -m build``
    or ``pip install -e .``)
    some directories hosting build artefacts and cache files may be
    created, such as ``build``, ``dist``, ``*.egg-info`` [#cache]_.
    You can configure your version control system to ignore them
    (see `GitHub's .gitignore template
    <https://github.com/github/gitignore/blob/main/Python.gitignore>`_
    for an example).


Uploading your package to PyPI
------------------------------
After generating the distribution files, the next step would be to upload your
distribution so others can use it. This functionality is provided by
:pypi:`twine` and is documented in the :doc:`Python packaging tutorial
<PyPUG:tutorials/packaging-projects>`.


Transitioning from ``setup.py`` to declarative config
-----------------------------------------------------
To avoid executing arbitrary scripts and boilerplate code, we are transitioning
from defining all your package information by running ``setup()`` to doing this
declaratively - by using ``pyproject.toml`` (or older ``setup.cfg``).

To ease the challenges of transitioning, we provide a quick
:doc:`guide </userguide/pyproject_config>` to understanding how ``pyproject.toml``
is parsed by ``setuptools``. (Alternatively, here is the
:doc:`guide </userguide/declarative_config>` for ``setup.cfg``).

.. note::

    The approach ``setuptools`` would like to take is to eventually use a single
    declarative format (``pyproject.toml``) instead of maintaining 2
    (``pyproject.toml`` / ``setup.cfg``). Yet, chances are, ``setup.cfg`` will
    continue to be maintained for a long time.

.. _packaging-resources:

Resources on Python packaging
=============================
Packaging in Python can be hard and is constantly evolving.
`Python Packaging User Guide <https://packaging.python.org>`_ has tutorials and
up-to-date references that can help you when it is time to distribute your work.



----

.. rubric:: Notes

.. [#setup.py]
   New projects are advised to avoid ``setup.py`` configurations (beyond the minimal stub)
   when custom scripting during the build is not necessary.
   Examples are kept in this document to help people interested in maintaining or
   contributing to existing packages that use ``setup.py``.
   Note that you can still keep most of configuration declarative in
   :doc:`setup.cfg <declarative_config>` or :doc:`pyproject.toml
   <pyproject_config>` and use ``setup.py`` only for the parts not
   supported in those files (e.g. C extensions).
   See :ref:`note <setuppy_discouraged>`.

.. [#cache]
   If you feel that caching is causing problems to your build, specially after changes in the
   configuration files, consider removing ``build``, ``dist``, ``*.egg-info`` before
   rebuilding or installing your project.

.. _PyPI: https://pypi.org
