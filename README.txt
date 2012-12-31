===============================
Installing and Using Distribute
===============================

.. contents:: **Table of Contents**

-----------
Disclaimers
-----------

About the fork
==============

`Distribute` is a fork of the `Setuptools` project.

Distribute is intended to replace Setuptools as the standard method
for working with Python module distributions.

The fork has two goals:

- Providing a backward compatible version to replace Setuptools
  and make all distributions that depend on Setuptools work as
  before, but with less bugs and behaviorial issues.

  This work is done in the 0.6.x series.

  Starting with version 0.6.2, Distribute supports Python 3.
  Installing and using distribute for Python 3 code works exactly
  the same as for Python 2 code, but Distribute also helps you to support
  Python 2 and Python 3 from the same source code by letting you run 2to3
  on the code as a part of the build process, by setting the keyword parameter
  ``use_2to3`` to True. See http://packages.python.org/distribute for more
  information.

- Refactoring the code, and releasing it in several distributions.
  This work is being done in the 0.7.x series but not yet released.

The roadmap is still evolving, and the page that is up-to-date is
located at : `http://packages.python.org/distribute/roadmap`.

If you install `Distribute` and want to switch back for any reason to
`Setuptools`, get to the `Uninstallation instructions`_ section.

More documentation
==================

You can get more information in the Sphinx-based documentation, located
at http://packages.python.org/distribute. This documentation includes the old
Setuptools documentation that is slowly replaced, and brand new content.

About the installation process
==============================

The `Distribute` installer modifies your installation by de-activating an
existing installation of `Setuptools` in a bootstrap process. This process
has been tested in various installation schemes and contexts but in case of a
bug during this process your Python installation might be left in a broken
state. Since all modified files and directories are copied before the
installation starts, you will be able to get back to a normal state by reading
the instructions in the `Uninstallation instructions`_ section.

In any case, it is recommended to save you `site-packages` directory before
you start the installation of `Distribute`.

-------------------------
Installation Instructions
-------------------------

Distribute is only released as a source distribution.

It can be installed using pip, and can be done so with the source tarball,
or by using the ``distribute_setup.py`` script provided online.

``distribute_setup.py`` is the simplest and preferred way on all systems.

distribute_setup.py
===================

Download
`distribute_setup.py <http://python-distribute.org/distribute_setup.py>`_
and execute it, using the Python interpreter of your choice.

If your shell has the ``curl`` program you can do::

    $ curl -O http://python-distribute.org/distribute_setup.py
    $ python distribute_setup.py

Notice this file is also provided in the source release.

pip
===

Run easy_install or pip::

    $ pip install distribute

Source installation
===================

Download the source tarball, uncompress it, then run the install command::

    $ curl -O http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz
    $ tar -xzvf distribute-0.6.35.tar.gz
    $ cd distribute-0.6.35
    $ python setup.py install

---------------------------
Uninstallation Instructions
---------------------------

Like other distutils-based distributions, Distribute doesn't provide an
uninstaller yet. It's all done manually! We are all waiting for PEP 376
support in Python.

Distribute is installed in three steps:

1. it gets out of the way an existing installation of Setuptools
2. it installs a `fake` setuptools installation
3. it installs distribute

Distribute can be removed like this:

- remove the ``distribute*.egg`` file located in your site-packages directory
- remove the ``setuptools.pth`` file located in you site-packages directory
- remove the easy_install script located in you ``sys.prefix/bin`` directory
- remove the ``setuptools*.egg`` directory located in your site-packages directory,
  if any.

If you want to get back to setuptools:

- reinstall setuptools using its instruction.

Lastly:

- remove the *.OLD.* directory located in your site-packages directory if any,
  **once you have checked everything was working correctly again**.

-------------------------
Quick help for developers
-------------------------

To create an egg which is compatible with Distribute, use the same
practice as with Setuptools, e.g.::

    from setuptools import setup

    setup(...
    )

To use `pkg_resources` to access data files in the egg, you should
require the Setuptools distribution explicitly::

    from setuptools import setup

    setup(...
        install_requires=['setuptools']
    )

Only if you need Distribute-specific functionality should you depend
on it explicitly. In this case, replace the Setuptools dependency::

    from setuptools import setup

    setup(...
        install_requires=['distribute']
    )

-----------
Install FAQ
-----------

- **Why is Distribute wrapping my Setuptools installation?**

   Since Distribute is a fork, and since it provides the same package
   and modules, it renames the existing Setuptools egg and inserts a
   new one which merely wraps the Distribute code. This way, full
   backwards compatibility is kept for packages which rely on the
   Setuptools modules.

   At the same time, packages can meet their dependency on Setuptools
   without actually installing it (which would disable Distribute).

- **How does Distribute interact with virtualenv?**

  Everytime you create a virtualenv it will install setuptools by default.
  You either need to re-install Distribute in it right after or pass the
  ``--distribute`` option when creating it.

  Once installed, your virtualenv will use Distribute transparently.

  Although, if you have Setuptools installed in your system-wide Python,
  and if the virtualenv you are in was generated without the `--no-site-packages`
  option, the Distribute installation will stop.

  You need in this case to build a virtualenv with the `--no-site-packages`
  option or to install `Distribute` globally.

- **How does Distribute interacts with zc.buildout?**

  You can use Distribute in your zc.buildout, with the --distribute option,
  starting at zc.buildout 1.4.2::

  $ python bootstrap.py --distribute

  For previous zc.buildout versions, *the only thing* you need to do
  is use the bootstrap at `http://python-distribute.org/bootstrap.py`.  Run
  that bootstrap and ``bin/buildout`` (and all other buildout-generated
  scripts) will transparently use distribute instead of setuptools.  You do
  not need a specific buildout release.

  A shared eggs directory is no problem (since 0.6.6): the setuptools egg is
  left in place unmodified.  So other buildouts that do not yet use the new
  bootstrap continue to work just fine.  And there is no need to list
  ``distribute`` somewhere in your eggs: using the bootstrap is enough.

  The source code for the bootstrap script is located at
  `http://bitbucket.org/tarek/buildout-distribute`.



-----------------------------
Feedback and getting involved
-----------------------------

- Mailing list: http://mail.python.org/mailman/listinfo/distutils-sig
- Issue tracker: http://bitbucket.org/tarek/distribute/issues/
- Code Repository: http://bitbucket.org/tarek/distribute

