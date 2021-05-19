:tocdepth: 2

.. _changes:

History
*******

.. towncrier-draft-entries:: DRAFT, unreleased as on |today|

.. include:: ../CHANGES (links).rst

Credits
*******

* The original design for the ``.egg`` format and the ``pkg_resources`` API was
  co-created by Phillip Eby and Bob Ippolito. Bob also implemented the first
  version of ``pkg_resources``, and supplied the macOS operating system version
  compatibility algorithm.

* Ian Bicking implemented many early "creature comfort" features of
  easy_install, including support for downloading via Sourceforge and
  Subversion repositories. Ian's comments on the Web-SIG about WSGI
  application deployment also inspired the concept of "entry points" in eggs,
  and he has given talks at PyCon and elsewhere to inform and educate the
  community about eggs and setuptools.

* Jim Fulton contributed time and effort to build automated tests of various
  aspects of ``easy_install``, and supplied the doctests for the command-line
  ``.exe`` wrappers on Windows.

* Phillip J. Eby is the seminal author of setuptools, and
  first proposed the idea of an importable binary distribution format for
  Python application plug-ins.

* Significant parts of the implementation of setuptools were funded by the Open
  Source Applications Foundation, to provide a plug-in infrastructure for the
  Chandler PIM application. In addition, many OSAF staffers (such as Mike
  "Code Bear" Taylor) contributed their time and stress as guinea pigs for the
  use of eggs and setuptools, even before eggs were "cool".  (Thanks, guys!)

* Tarek Ziadé is the principal author of the Distribute fork, which
  re-invigorated the community on the project, encouraged renewed innovation,
  and addressed many defects.

* Jason R. Coombs performed the merge with Distribute, maintaining the
  project for several years in coordination with the Python Packaging
  Authority (PyPA).
