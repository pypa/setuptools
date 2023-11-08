.. _Controlling files in the distribution:

Controlling files in the distribution
=====================================

For the most common use cases, ``setuptools`` will automatically find out which
files are necessary for distributing the package.
These include all :term:`pure Python modules <Pure Module>` in the
``py_modules`` or ``packages`` configuration, and the C sources (but not C
headers) listed as part of extensions when creating a :term:`source
distribution (or "sdist")`.

.. note::
   .. versionadded:: v68.3.0
      ``setuptools`` will attempt to include type information files
      by default in the distribution
      (``.pyi`` and ``py.typed``, as specified in :pep:`561`).

    *Please note however that this feature is* **EXPERIMENTAL** *and may change in
    the future.*

    If you have ``.pyi`` and ``py.typed`` files in your project, but do not
    wish to distribute them, you can opt out by setting
    :doc:`exclude-package-data </userguide/datafiles>` to remove them.

However, when building more complex packages (e.g. packages that include
non-Python files, or that need to use custom C headers), you might find that
not all files present in your project folder are included in package
:term:`distribution archive <Distribution Package>`.

If you are using a :wiki:`Revision Control System`, such as git_ or mercurial_,
and your source distributions only need to include files that you're
tracking in revision control, you can use a ``setuptools`` :ref:`plugin <Adding
Support for Revision Control Systems>`, such as :pypi:`setuptools-scm` or
:pypi:`setuptools-svn` to automatically include all tracked files into the ``sdist``.

.. _Using MANIFEST.in:

Alternatively, if you need finer control over the files (e.g. you don't want to
distribute :wiki:`CI/CD`-related files) or you need automatically generated files,
you can add a ``MANIFEST.in`` file at the root of your project,
to specify any files that the default file location algorithm doesn't catch.

This file contains instructions that tell ``setuptools`` which files exactly
should be part of the ``sdist`` (or not).
A comprehensive guide to ``MANIFEST.in`` syntax is available at the
:doc:`PyPA's Packaging User Guide <PyPUG:guides/using-manifest-in>`.

.. attention::
   Please note that ``setuptools`` supports the ``MANIFEST.in``,
   and not ``MANIFEST`` (no extension). Any documentation, tutorial or example
   that recommends using ``MANIFEST`` (no extension) is likely outdated.

.. tip::
   The ``MANIFEST.in`` file contains commands that allow you to discover and
   manipulate lists of files. There are many commands that can be used with
   different objectives, but you should try to not make your ``MANIFEST.in``
   file too fine grained.

   A good idea is to start with a ``graft`` command (to add all
   files inside a set of directories) and then fine tune the file selection
   by removing the excess or adding isolated files.

An example of ``MANIFEST.in`` for a simple project that organized according to a
:ref:`src-layout` is:

.. code-block:: bash

   # MANIFEST.in -- just for illustration
   graft src
   graft tests
   graft docs
   # `-> adds all files inside a directory

   include tox.ini
   # `-> matches file paths relative to the root of the project

   global-exclude *~ *.py[cod] *.so
   # `-> matches file names (regardless of directory)

Once the correct files are present in the ``sdist``, they can then be used by
binary extensions during the build process, or included in the final
:term:`wheel <Wheel>` [#build-process]_ if you configure ``setuptools`` with
``include_package_data=True``.

.. important::
   Please note that, when using ``include_package_data=True``, only files **inside
   the package directory** are included in the final ``wheel``, by default.

   So for example, if you create a :term:`Python project <Project>` that uses
   :pypi:`setuptools-scm` and have a ``tests`` directory outside of the package
   folder, the ``tests`` directory will be present in the ``sdist`` but not in the
   ``wheel`` [#wheel-vs-sdist]_.

   See :doc:`/userguide/datafiles` for more information.

----

.. [#build-process]
   You can think about the build process as two stages: first the ``sdist``
   will be created and then the ``wheel`` will be produced from that ``sdist``.

.. [#wheel-vs-sdist]
   This happens because the ``sdist`` can contain files that are useful during
   development or the build process itself, but not in runtime (e.g. tests,
   docs, examples, etc...).
   The ``wheel``, on the other hand, is a file format that has been optimized
   and is ready to be unpacked into a running installation of Python or
   :term:`Virtual Environment`.
   Therefore it only contains items that are required during runtime.

.. _git: https://git-scm.com
.. _mercurial: https://www.mercurial-scm.org
