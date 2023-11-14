.. _Controlling files in the distribution:

Controlling files in the distribution
=====================================

For the most common use cases, ``setuptools`` will automatically find out which
files are necessary for distributing the package. More precisely, the following
files are included in a source distribution by default:

- :term:`pure Python module <Pure Module>` files implied by the ``py-modules`` and ``packages``
  configuration parameters in ``pyproject.toml`` and/or equivalent
  in ``setup.cfg``/``setup.py``;
- C source files mentioned in the ``ext_modules`` or ``libraries``
  ``setup()`` arguments;
- Files that match the following glob patterns: ``tests/test*.py``,
  ``test/test*.py``;
- Scripts specified by the ``scripts-files`` configuration parameter
  in ``pyproject.toml`` or ``scripts`` in ``setup.py``/``setup.cfg``;
- All files specified by the ``package-data`` and ``data-files``
  configuration parameters in ``pyproject.toml`` and/or equivalent
  in ``setup.cfg``/``setup.py``;
- The file specified by the ``license_file`` option in ``setup.cfg``;
- All files specified by the ``license-files`` configuration parameter
  in ``pyproject.toml`` and/or equivalent in ``setup.cfg``/``setup.py``;
  note that if you don't explicitly set this parameter, ``setuptools``
  will include any files that match the following glob patterns:
  ``LICENSE*``, ``LICENCE*``, ``COPYING*``, ``NOTICE*``, ``AUTHORS**``;
- ``pyproject.toml``;
- ``setup.cfg``;
- ``setup.py``;
- ``README``, ``README.txt``, ``README.rst`` or ``README.md``;
- ``MANIFEST.in``

Please note that the list above is guaranteed to work with the last stable version
of ``setuptools``. The behavior of older versions might differ.

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


A :file:`MANIFEST.in` file consists of commands, one per line, instructing
setuptools to add or remove some set of files from the sdist.  The commands
are:

=========================================================  ==================================================================================================
Command                                                    Description
=========================================================  ==================================================================================================
:samp:`include {pat1} {pat2} ...`                          Add all files matching any of the listed patterns
                                                           (Files must be given as paths relative to the root of the project)
:samp:`exclude {pat1} {pat2} ...`                          Remove all files matching any of the listed patterns
                                                           (Files must be given as paths relative to the root of the project)
:samp:`recursive-include {dir-pattern} {pat1} {pat2} ...`  Add all files under directories matching ``dir-pattern`` that match any of the listed patterns
:samp:`recursive-exclude {dir-pattern} {pat1} {pat2} ...`  Remove all files under directories matching ``dir-pattern`` that match any of the listed patterns
:samp:`global-include {pat1} {pat2} ...`                   Add all files anywhere in the source tree matching any of the listed patterns
:samp:`global-exclude {pat1} {pat2} ...`                   Remove all files anywhere in the source tree matching any of the listed patterns
:samp:`graft {dir-pattern}`                                Add all files under directories matching ``dir-pattern``
:samp:`prune {dir-pattern}`                                Remove all files under directories matching ``dir-pattern``
=========================================================  ==================================================================================================

The patterns here are glob-style patterns: ``*`` matches zero or more regular
filename characters (on Unix, everything except forward slash; on Windows,
everything except backslash and colon); ``?`` matches a single regular filename
character, and ``[chars]`` matches any one of the characters between the square
brackets (which may contain character ranges, e.g., ``[a-z]`` or
``[a-fA-F0-9]``).  Setuptools also has support for ``**`` matching
zero or more characters including forward slash, backslash, and colon.

Directory patterns are relative to the root of the project directory; e.g.,
``graft example*`` will include a directory named :file:`examples` in the
project root but will not include :file:`docs/examples/`.

File & directory names in :file:`MANIFEST.in` should be ``/``-separated;
setuptools will automatically convert the slashes to the local platform's
appropriate directory separator.

Commands are processed in the order they appear in the :file:`MANIFEST.in`
file.  For example, given the commands:

.. code-block:: bash

    graft tests
    global-exclude *.py[cod]

the contents of the directory tree :file:`tests` will first be added to the
sdist, and then after that all files in the sdist with a ``.pyc``, ``.pyo``, or
``.pyd`` extension will be removed from the sdist.  If the commands were in the
opposite order, then ``*.pyc`` files etc. would be only be removed from what
was already in the sdist before adding :file:`tests`, and if :file:`tests`
happened to contain any ``*.pyc`` files, they would end up included in the
sdist because the exclusion happened before they were included.

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
