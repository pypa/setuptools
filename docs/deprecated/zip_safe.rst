Understanding the ``zip_safe`` flag
===================================

The ``zip_safe`` flag is a ``setuptools`` configuration mainly associated
with the ``egg`` distribution format
(which got replaced in the ecosystem by the newer ``wheel`` format) and the
``easy_install`` command (deprecated in ``setuptools`` v58.3.0).

It is very unlikely that the values of ``zip_safe`` will affect modern
deployments that use :pypi:`pip` for installing packages.
Moreover, new users of ``setuptools`` should not attempt to create egg files
using the deprecated ``build_egg`` command.
Therefore, this flag is considered **obsolete**.

This document, however, describes what was the historical motivation behind
this flag, and how it was used.

Historical Motivation
---------------------

For some use cases (such as bundling as part of a larger application), Python
packages may be run directly from a zip file.
Not all packages, however, are capable of running in compressed form, because
they may expect to be able to access either source code or data files as
normal operating system files.

In the past, ``setuptools`` would install a project distributed
as a zipfile or a directory (via the ``easy_install`` command or
``python setup.py install``),
the default choice being determined by the project's ``zip_safe`` flag.

How the ``zip_safe`` flag was used?
-----------------------------------

To set this flag, a developer would pass a boolean value for the ``zip_safe`` argument to the
``setup()`` function, or omit it.  When omitted, the ``bdist_egg``
command would analyze the project's contents to see if it could detect any
conditions that preventing the project from working in a zipfile.

This was extremely conservative: ``bdist_egg`` would consider the
project unsafe if it contained any C extensions or datafiles whatsoever.  This
does *not* mean that the project couldn't or wouldn't work as a zipfile!  It just
means that the ``bdist_egg`` authors were not yet comfortable asserting that
the project *would* work.  If the project did not contain any C or data files, and did not
attempt to perform ``__file__`` or ``__path__`` introspection or source code manipulation, then
there was an extremely solid chance the project will work when installed as a
zipfile.  (And if the project used ``pkg_resources`` for all its data file
access, then C extensions and other data files shouldn't be a problem at all.
See the :ref:`Accessing Data Files at Runtime` section for more information.)

The developer could manually set ``zip_safe`` to ``True`` to perform tests,
or to override the default behaviour (after checking all the warnings and
understanding the implications), this would allow ``setuptools`` to install the
project as a zip file. Alternatively, by setting ``zip_safe`` to ``False``,
developers could force ``setuptools`` to always install the project as a
directory.

Modern ways of loading packages from zip files
----------------------------------------------

Currently, popular Python package installers (such as :pypi:`pip`) and package
indexes (such as PyPI_) consider that distribution packages are always
installed as a directory.
It is however still possible to load packages from zip files added to
:obj:`sys.path`, thanks to the :mod:`zipimport` module
and the :mod:`importlib` machinery provided by Python standard library.

When working with modules loaded from a zip file, it is important to keep in
mind that values of ``__file__`` and ``__path__`` might not work as expected.
Please check the documentation for :mod:`importlib.resources`, if file
locations are important for your use case.


.. _PyPI: https://pypi.org
