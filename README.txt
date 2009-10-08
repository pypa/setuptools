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

  This work is done in the 0.6.x series

  Starting with version 0.6.2, Distribute supports Python 3. 
  Installing and using distribute for Python 3 code works exactly 
  the same as for Python 2 code, but Distribute also helps you to support 
  Python 2 and Python 3 from the same source code by letting you run 2to3 
  on the code as a part of the build process, by setting the keyword parameter 
  ``use_2to3`` to True. See docs/python3.txt for more information.

- Refactoring the code, and releasing it in several distributions.
  This work is being done in the 0.7.x series but not yet released.

If you install `Distribute` and want to switch back for any reason to
`Setuptools`, get to the `Uninstallation instructions`_ section.

More documentation
==================

You can get more information in the Sphinx-based documentation, located
in the archive in `docs`. This documentation includes the old Setuptools
documentation that is slowly replaced, and brand new content.

About the installation process
==============================

The `Distribute` installer modifies your installation by de-activating an
existing installation of `Setuptools` in a bootstrap process. This process 
has been tested in various installation schemes and contexts but in case of a 
bug during this process your Python installation might be left in a broken
state. Since all modified files and directories are copied before the 
installation, you will be able to get back to a normal state by reading
the instructions in the `Uninstallation instructions`_ section.

In any case, it is recommended to save you `site-packages` directory before 
you start the installation of `Distribute`.

-------------------------
Installation Instructions
-------------------------

Distribute is only released as a source distribution.

It can be installed using easy_install or pip, and can be done so with the source
tarball, the eggs distribution, or by using the ``distribute_setup.py`` script
provided online.

``distribute_setup.py`` is the simplest and preferred way on all systems.

distribute_setup.py
===================

Download ``distribute_setup.py`` and execute it, using the Python interpreter of
your choice. 

If your shell has the ``wget`` program you can do::

    $ wget http://nightly.ziade.org/distribute_setup.py
    $ python distribute_setup.py

If you are under Python 3, use ``distribute_setup_3k.py``::

    $ wget http://nightly.ziade.org/distribute_setup_3k.py
    $ python distribute_setup_3k.py

Notice that both files are provided in the source release.

easy_install or pip
===================

Run easy_install or pip::

    $ easy_install Distribute
    $ pip install Distribute

Source installation
===================

Download the source tarball, uncompress it, then run the install command::

    $ wget http://pypi.python.org/packages/source/d/distribute/distribute-0.6.4.tar.gz
    $ tar -xzvf distribute-0.6.4.tar.gz
    $ cd distribute-0.6
    $ python setup.py install

---------------------------
Uninstallation Instructions
---------------------------

Like other distutils-based distributions, Distribute doesn't provide an 
uninstaller yet. It's all done manually!

Distribute is installed in three steps:

1. it gets out of the way an existing installation of Setuptools
2. it installs a `fake` setuptools installation 
3. it installs distribute

Distribute can be removed like this:

- run ``easy_install -m Distribute``. This will remove the Distribute reference
  from ``easy-install.pth``. Otherwise, edit the file and remove it yourself.
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

-----------
Install FAQ
-----------

- **Why Distribute turn my Setuptools installation into an fake one?**

   Since Distribute is a fork, and since it provides the same package and modules,
   it fakes that the Setuptools installation is still present, so all the programs
   that where using Setuptools still work.

   If it wasn't doing it, a program that would try to install Setuptools 
   would overwrite in turn Distribute.

- **How does Distribute interacts with virtualenv?**

  Everytime you create a virtualenv it will install setuptools, so you need to
  re-install Distribute in it right after. The Distribute project will not
  attempt to patch virtualenv so it uses it when globally installed.

  Once installed, your virtualenv will use Distribute transparently.

  Although, if you have Setuptools installed in your system-wide Python,
  and if the virtualenv you are in was generated without the `--no-site-packages`
  option, the Distribute installation will stop.

  You need in this case to build a virtualenv with the --no-site-packages option
  or to install `Distribute` globally.

- **How does Distribute interacts with zc.buildout?**

  Some work is being done on zc.buildout side to make its bootstrap
  work with Distribute. Until then, using Distribute in zc.buildout is a bit
  tricky because the bootstrap process of zc.buildout hardcodes the
  installation of Setuptools.

  The plan is to come with a custom bootstrap.py for zc.buildout for the
  0.6.4 release, together with some small changes on zc.buildout side.


-----------------------------
Feedback and getting involved
-----------------------------

- Mailing list: http://mail.python.org/mailman/listinfo/distutils-sig
- Issue tracker: http://bitbucket.org/tarek/distribute/issues/
- Code Repository: http://bitbucket.org/tarek/distribute

