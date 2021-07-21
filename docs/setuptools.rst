==================================================
Building and Distributing Packages with Setuptools
==================================================

``Setuptools`` is a collection of enhancements to the Python ``distutils``
that allow developers to more easily build and
distribute Python packages, especially ones that have dependencies on other
packages.

Packages built and distributed using ``setuptools`` look to the user like
ordinary Python packages based on the ``distutils``.

Feature Highlights:

* Create `Python Eggs <http://peak.telecommunity.com/DevCenter/PythonEggs>`_ -
  a single-file importable distribution format

* Enhanced support for accessing data files hosted in zipped packages.

* Automatically include all packages in your source tree, without listing them
  individually in setup.py

* Automatically include all relevant files in your source distributions,
  without needing to create a ``MANIFEST.in`` file, and without having to force
  regeneration of the ``MANIFEST`` file when your source tree changes.

* Automatically generate wrapper scripts or Windows (console and GUI) .exe
  files for any number of "main" functions in your project.  (Note: this is not
  a py2exe replacement; the .exe files rely on the local Python installation.)

* Transparent Cython support, so that your setup.py can list ``.pyx`` files and
  still work even when the end-user doesn't have Cython installed (as long as
  you include the Cython-generated C in your source distribution)

* Command aliases - create project-specific, per-user, or site-wide shortcut
  names for commonly used commands and options

* Deploy your project in "development mode", such that it's available on
  ``sys.path``, yet can still be edited directly from its source checkout.

* Easily extend the distutils with new commands or ``setup()`` arguments, and
  distribute/reuse your extensions for multiple projects, without copying code.

* Create extensible applications and frameworks that automatically discover
  extensions, using simple "entry points" declared in a project's setup script.

* Full support for PEP 420 via ``find_namespace_packages()``, which is also backwards
  compatible to the existing ``find_packages()`` for Python >= 3.3.

-----------------
Developer's Guide
-----------------

The developer's guide has been updated. See the :doc:`most recent version <userguide/index>`.































TRANSITIONAL NOTE
~~~~~~~~~~~~~~~~~

Setuptools automatically calls ``declare_namespace()`` for you at runtime,
but future versions may *not*.  This is because the automatic declaration
feature has some negative side effects, such as needing to import all namespace
packages during the initialization of the ``pkg_resources`` runtime, and also
the need for ``pkg_resources`` to be explicitly imported before any namespace
packages work at all.  In some future releases, you'll be responsible
for including your own declaration lines, and the automatic declaration feature
will be dropped to get rid of the negative side effects.

During the remainder of the current development cycle, therefore, setuptools
will warn you about missing ``declare_namespace()`` calls in your
``__init__.py`` files, and you should correct these as soon as possible
before the compatibility support is removed.
Namespace packages without declaration lines will not work
correctly once a user has upgraded to a later version, so it's important that
you make this change now in order to avoid having your code break in the field.
Our apologies for the inconvenience, and thank you for your patience.

















setup.cfg-only projects
=======================

.. versionadded:: 40.9.0

If ``setup.py`` is missing from the project directory when a :pep:`517`
build is invoked, ``setuptools`` emulates a dummy ``setup.py`` file containing
only a ``setuptools.setup()`` call.

.. note::

    :pep:`517` doesn't support editable installs so this is currently
    incompatible with ``pip install -e .``.

This means that you can have a Python project with all build configuration
specified in ``setup.cfg``, without a ``setup.py`` file, if you **can rely
on** your project always being built by a :pep:`517`/:pep:`518` compatible
frontend.

To use this feature:

* Specify build requirements and :pep:`517` build backend in
  ``pyproject.toml``.
  For example:

  .. code-block:: toml

      [build-system]
      requires = [
        "setuptools >= 40.9.0",
        "wheel",
      ]
      build-backend = "setuptools.build_meta"

* Use a :pep:`517` compatible build frontend, such as ``pip >= 19`` or ``build``.

  .. warning::

      As :pep:`517` is new, support is not universal, and frontends that
      do support it may still have bugs. For compatibility, you may want to
      put a ``setup.py`` file containing only a ``setuptools.setup()``
      invocation.


Configuration API
=================

Some automation tools may wish to access data from a configuration file.

``Setuptools`` exposes a ``read_configuration()`` function for
parsing ``metadata`` and ``options`` sections into a dictionary.


.. code-block:: python

    from setuptools.config import read_configuration

    conf_dict = read_configuration("/home/user/dev/package/setup.cfg")


By default, ``read_configuration()`` will read only the file provided
in the first argument. To include values from other configuration files
which could be in various places, set the ``find_others`` keyword argument
to ``True``.

If you have only a configuration file but not the whole package, you can still
try to get data out of it with the help of the ``ignore_option_errors`` keyword
argument. When it is set to ``True``, all options with errors possibly produced
by directives, such as ``attr:`` and others, will be silently ignored.
As a consequence, the resulting dictionary will include no such options.











Mailing List and Bug Tracker
============================

Please use the `distutils-sig mailing list`_ for questions and discussion about
setuptools, and the `setuptools bug tracker`_ ONLY for issues you have
confirmed via the list are actual bugs, and which you have reduced to a minimal
set of steps to reproduce.

.. _distutils-sig mailing list: http://mail.python.org/pipermail/distutils-sig/
.. _setuptools bug tracker: https://github.com/pypa/setuptools/
