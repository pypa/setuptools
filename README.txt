===============================
Installing and Using Distribute
===============================

.. contents:: **Table of Contents**

-----------
Disclaimers
-----------

About the fork
==============

`Distribute` is a friendly fork of the `Setuptools` project. The `Setuptools`
maintainer, Phillip J. Eby is not responsible of any aspect of this fork.

If you install `Distribute` and want to switch back for any reason to 
`Setuptools`, get to the `Uninstallation instructions`_ section.

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

It can be installed using easy_install or pip, with the source tarball, with the
eggs distribution, or using the ``distribute_setup.py`` script provided online.

``distribute_setup.py`` is the simplest and preferred way on all systems.

distribute_setup.py
===================

Download ``distribute_setup.py`` and execute it, using the Python interpreter of
your choice.

If your shell has the `wget` program you can do::

    $ wget http://nightly.ziade.org/distribute_setup.py
    $ python distribute_setup.py

easy_install or pip
===================

Run easy_install or pip::

    $ easy_install Distribute
    $ pip install Distribute

Source installation
===================

Download the source tarball, and uncompress it, then run the install command::

    $ wget http://pypi.python.org/packages/source/d/distribute/distribute-0.6.1.tar.gz
    $ tar -xzvf distribute-0.6.1.tar.gz
    $ cd distribute-0.6
    $ python setup.py install

---------------------------
Uninstallation Instructions
---------------------------

Like other distutils-based distributions, Distribute doesn't provide an 
uninstaller yet. It's all manual !

Distribute is installed in three steps:

1- it gets out of the way an existing installation of Setuptools
2- it installs a `fake` setuptools installation 
3- it installs distribute

Distribute can be removed like this:

- run `easy_install -m Distribute`. This will remove the Distribute reference
  from `easy-install.pth` *or* edit the file and remove it yourself.
- remove the distribute*.egg file located in your site-packages directory
- remove the setuptools.pth file located in you site-packages directory
- remove the easy_install script located in you sys.prefix/bin directory
- remove the setuptools*.egg directory located in your site-packages directory
  if any.

If you want to get back to setuptools:

- reinstall setuptools using its instruction.

Last:

- remove the *.OLD.* directory located in your site-packages directory if any,
  **once you have checked everything was working correctly again**.

-----------
Install FAQ
-----------

- **Why Distribute turn my Setuptools installation into an fake one ?**

   Since Distribute is a fork, and since it provides the same package and modules,
   it fakes that the Setuptools installation is still present, so all the programs
   that where using Setuptools still work.

   If it wasn't doing it, a program that would try to install Setuptools 
   would overwrite in turn Distribute.

- **How does Distribute interacts with virtualenv ?**

  Everytime you create a virtualenv it will install setuptools, so you need to
  re-install Distribute in it right after. The Distribute project will not
  attempt to patch virtualenv so it uses it when globally installed.

  Once installed, your virtualenv will use Distribute transparently.

  Although, if you have Setuptools installed in your system-wide Python,
  and if the virtualenv you are in was generated without the `--no-site-packages`
  option, the Distribute installation will stop.

  You need in this case to build a virtualenv with the --no-site-packages option
  or to install `Distribute` globally.

- **How does Distribute interacts with zc.buildout ?**

  Like virtualenv, Distribute has to be installed after setuptools. The simplest
  way is to add it in a `zc.recipe.egg` section so the job is done when you 
  build your buildout.

  If you are combining zc.buildout and virtualenv, you might fail in the 
  problem described in the previous FAQ entry.

  Last, you will need to use the provided special `bootstrap.py` file,
  located in the buildout directory.

-------
Credits
-------

* Tarek Ziadé
* Hanno Schlichting
* Many other people that helped on Distutils-SIG (please add your name here)
* Phillip Eby for the Setuptools project. 

 
