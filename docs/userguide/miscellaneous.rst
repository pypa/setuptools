.. _Controlling files in the distribution:

Controlling files in the distribution
=====================================

For the most common use cases, ``setuptools`` will automatically find out which
files are necessary for distributing the package.
This includes all :term:`pure Python modules <Pure Module>` in the
``py_modules`` or ``packages`` configuration, and the C sources (but not C
headers) listed as part of extensions when creating a :term:`Source
Distribution (or "sdist")`.

However, when building more complex packages (e.g. packages that include
non-Python files, or that need to use custom C headers), you might find that
not all files present in your project folder are included in package
:term:`distribution archive <Distribution Package>`.

In these situations you can use a ``setuptools``
:ref:`plugin <Adding Support for Revision Control Systems>`,
such as :pypi:`setuptools-scm` or :pypi:`setuptools-svn` to automatically
include all files tracked by your Revision Control System into the ``sdist``.

.. _Using MANIFEST.in:

Alternatively, if you need finer control, you can add a ``MANIFEST.in`` file at
the root of your project.
This file contains instructions that tell ``setuptools`` which files exactly
should be part of the ``sdist`` (or not).
A comprehensive guide to ``MANIFEST.in`` syntax is available at the
:doc:`PyPA's Packaging User Guide <PyPUG:guides/using-manifest-in>`.

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
