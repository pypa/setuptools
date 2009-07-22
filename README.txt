===============================
Installing and Using Distribute
===============================

.. contents:: **Table of Contents**

----------
Disclaimer
----------

`Distribute` is a friendly fork of the `Setuptools` project. The `Setuptools`
maintainer, Phillip J. Eby is not responsible of any aspect of this fork.

If you install `Distribute` and want to switch back for any reason to 
`Setuptools`, get to the `Uninstallation instructions`_ section.

-------------------------
Installation Instructions
-------------------------

Distribute comes in two flavors: in eggs or as a source distribution. Archives
are available at the PyPI page and here : 
http://bitbucket.org/tarek/distribute/downloads.

It can be installed using easy_install or pip, with the source tarball, with the
eggs distribution, or using the ``bootstrap.py`` script provided online.

``bootstrap.py`` is the simplest and preferred way on all systems.

bootstrap.py
============

Download ``bootstrap.py`` and execute it, using the Python interpreter of
your choice.

If your shell has the `wget` programm you can do::

    $ wget http://bitbucket.org/tarek/distribute/downloads/bootstrap.py
    $ python bootstrap.py

easy_install or pip
===================

Run easy_install or pip::

    $ easy_install Distribute
    $ pip Distribute

Source installation
===================

Download the source tarball, and uncompress it, then run the install command::

    $ wget http://bitbucket.org/tarek/distribute/downloads/distribute-0.6.tar.gz
    $ tar -xzvf distribute-0.6.tar.gz
    $ cd distribute-0.6
    $ python setup.py install

Egg installation
================

An Egg is a zip file with a `sh` script inserted in its head so it can be 
`executed` in the shell.

Cygwin, Linux anc Mac OS/X
--------------------------

1. Download the appropriate egg for your version of Python (e.g.
   ``distribute-0.6-py2.4.egg``).  Do NOT rename it.

2. Run it as if it were a shell script, e.g. ``sh distribute-0.6-py2.4.egg``.
   Distutils will install itself using the matching version of Python (e.g.
   ``python2.4``), and will place the ``easy_install`` executable in the
   default location for installing Python scripts (as determined by the
   standard distutils configuration files, or by the Python installation).

If you want to install distribute to somewhere other than ``site-packages`` or
your default distutils installation locations for libraries and scripts, you
may include EasyInstall command-line options such as ``--prefix``,
``--install-dir``, and so on, following the ``.egg`` filename on the same
command line.  For example::

    sh distribute-0.6-py2.4.egg --prefix=~

Cygwin Note
-----------

If you are trying to install Distribute for the **Windows** version of Python
(as opposed to the Cygwin version that lives in ``/usr/bin``), you must make
sure that an appropriate executable (``python2.3``, ``python2.4``, or
``python2.5``) is on your **Cygwin** ``PATH`` when invoking the egg.  For
example, doing the following at a Cygwin bash prompt will install Distribute
for the **Windows** Python found at ``C:\\Python24``::

    ln -s /cygdrive/c/Python24/python.exe python2.4
    PATH=.:$PATH sh distribute-0.6-py2.4.egg
    rm python2.4

Windows
-------

Don't install Distribute trying to execute the egg, because it's aimed to 
sh-based shells. Instead, use the ``bootstrap.py`` method, that will 
download the egg for you, then install the egg.

---------------------------
Uninstallation Instructions
---------------------------

Like other distutils-based distributions, Distribute doesn't provide an 
uninstaller yet. It's all manual !

Distribute can be removed like this:

- run `easy_install -m Distribute`. This will remove the Distribute reference
  from `easy-install.pth` *or* edit the file and remove it yourself.
- remove the distribute*.egg file located in your site-packages directory
- remove the setuptools.pth file located in you site-packages directory
- remove the easy_install script located in you sys.prefix/bin directory

If Setuptools was installed before you installed Distribute:

- remove the setuptools*.egg directory located in your site-packages directory
- remove the setuptools*.egg.OLD.* directory located in your site-packages directory
- reinstall setuptools using its instruction.

-----------
Install FAQ
-----------

- **Why Distribute turn my Setuptools egg installation into an empty egg ?**

   Since Distribute is a fork, and since it provides the same package and modules,
   it fakes that the setuptools installation is still present, so all the programs
   that where using setuptools still work.

- **How does Distribute interacts with virtualenv ?**

  Everytime you create a virtualenv it will install setuptools, so you need to
  re-install Distribute in it right after. The Distribute project will not
  attempt to patch virtualenv so it uses it when globally installed.

  Once installed, your virtualenv will use Distribute transparently.

- **How does in interacts with zc.buildout ?**

  Like virtualenv, Distribute has to be installed after setuptools. The simplest
  way is to add it in a `zc.recipe.egg` section so the job is done when you 
  build your buildout.

-------------
Documentation
-------------

XXX will point to setuptools doc.

-------
Credits
-------

* More to add here I need to list (Hanno, me, other guys..)
* Phillip Eby for the Setuptools project. 
 
