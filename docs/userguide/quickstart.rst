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
the market. All python package must provide a ``pyproject.toml`` and specify
the backend (build system) it wants to use. The distribution can then
be generated with whatever tools that provides a ``build sdist``-alike
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
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta"

Then, you will need a ``setup.cfg`` or ``setup.py`` to specify your package
information, such as metadata, contents, dependencies, etc. Here we demonstrate
the minimum

.. tab:: setup.cfg

    .. code-block:: ini

        [metadata]
        name = mypackage
        version = 0.0.1

        [options]
        packages = mypackage
        install_requires =
            requests
            importlib; python_version == "2.6"

.. tab:: setup.py

    .. code-block:: python

        from setuptools import setup

        setup(
            name='mypackage',
            version='0.0.1',
            packages=['mypackage'],
            install_requires=[
                'requests',
                'importlib; python_version == "2.6"',
            ],
        )

This is what your project would look like::

    ~/mypackage/
        pyproject.toml
        setup.cfg # or setup.py
        mypackage/__init__.py

Then, you need an builder, such as :std:doc:`PyPA build <pypa-build:index>`
which you can obtain via ``pip install build``. After downloading it, invoke
the builder::

    python -m build

You now have your distribution ready (e.g. a ``tar.gz`` file and a ``.whl``
file in the ``dist`` directory), which you can upload to PyPI!

Of course, before you release your project to PyPI, you'll want to add a bit
more information to your setup script to help people find or learn about your
project.  And maybe your project will have grown by then to include a few
dependencies, and perhaps some data files and scripts. In the next few sections,
we will walk through those additional but essential information you need
to specify to properly package your project.


Automatic package discovery
===========================
For simple projects, it's usually easy enough to manually add packages to
the ``packages`` keyword in ``setup.cfg``.  However, for very large projects
, it can be a big burden to keep the package list updated. ``setuptools``
therefore provides two convenient tools to ease the burden: :literal:`find:\ ` and
:literal:`find_namespace:\ `. To use it in your project:

.. code-block:: ini

    [options]
    packages = find:

    [options.packages.find] #optional
    include=pkg1, pkg2
    exclude=pk3, pk4

When you pass the above information, alongside other necessary ones,
``setuptools`` walks through the directory specified in ``where`` (omitted
here as the package reside in current directory) and filters the packages
it can find following the ``include``  (default to none), then remove
those that match the ``exclude`` and return a list of Python packages. Note
that each entry in the ``[options.packages.find]`` is optional. The above
setup also allows you to adopt a ``src/`` layout. For more details and advanced
use, go to :ref:`package_discovery`


Entry points and automatic script creation
===========================================
Setuptools support automatic creation of scripts upon installation, that runs
code within your package if you specify them with the ``entry_points`` keyword.
This is what allows you to run commands like ``pip install`` instead of having
to type ``python -m pip install``. To accomplish this, add the entry_points
keyword in your ``setup.cfg``:

.. code-block:: ini

    [options.entry_points]
    console_scripts =
        main = mypkg:some_func

When this project is installed, a ``main`` script will be installed and will
invoke the ``some_func`` in the ``__init__.py`` file when called by the user.
For detailed usage, including managing the additional or optional dependencies,
go to :doc:`entry_point`.


Dependency management
=====================
``setuptools`` supports automatically installing dependencies when a package is
installed. The simplest way to include requirement specifiers is to use the
``install_requires`` argument to ``setup.cfg``.  It takes a string or list of
strings containing requirement specifiers (A version specifier is one of the
operators <, >, <=, >=, == or !=, followed by a version identifier):

.. code-block:: ini

    [options]
    install_requires =
        docutils >= 0.3
        requests <= 0.4

When your project is installed, all of the dependencies not already installed
will be located (via PyPI), downloaded, built (if necessary), and installed.
This, of course, is a simplified scenarios. ``setuptools`` also provide
additional keywords such as ``setup_requires`` that allows you to install
dependencies before running the script, and ``extras_requires`` that take
care of those needed by automatically generated scripts. It also provides
mechanisms to handle dependencies that are not in PyPI. For more advanced use,
see :doc:`dependency_management`


.. _Including Data Files:

Including Data Files
====================
The distutils have traditionally allowed installation of "data files", which
are placed in a platform-specific location. Setuptools offers three ways to
specify data files to be included in your packages. For the simplest use, you
can simply use the ``include_package_data`` keyword:

.. code-block:: ini

    [options]
    include_package_data = True

This tells setuptools to install any data files it finds in your packages.
The data files must be specified via the distutils' ``MANIFEST.in`` file.
For more details, see :doc:`datafiles`


Development mode
================

.. tip::

	Prior to :ref:`pip v21.1 <pip:v21-1>`, a ``setup.py`` script was
	required to be compatible with development mode. With late
	versions of pip, any project may be installed in this mode.

``setuptools`` allows you to install a package without copying any files
to your interpreter directory (e.g. the ``site-packages`` directory).
This allows you to modify your source code and have the changes take
effect without you having to rebuild and reinstall.
Here's how to do it::

    pip install --editable .

This creates a link file in your interpreter site package directory which
associate with your source code. For more information, see :doc:`development_mode`.


Uploading your package to PyPI
==============================
After generating the distribution files, next step would be to upload your
distribution so others can use it. This functionality is provided by
`twine <https://pypi.org/project/twine/>`_ and we will only demonstrate the
basic use here.


Transitioning from ``setup.py`` to ``setup.cfg``
================================================
To avoid executing arbitrary scripts and boilerplate code, we are transitioning
into a full-fledged ``setup.cfg`` to declare your package information instead
of running ``setup()``. This inevitably brings challenges due to a different
syntax. Here we provide a quick guide to understanding how ``setup.cfg`` is
parsed by ``setuptool`` to ease the pain of transition.

.. _packaging-resources:

Resources on Python packaging
=============================
Packaging in Python is hard. Here we provide a list of links for those that
want to learn more.
