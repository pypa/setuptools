-------------------------
Development on Setuptools
-------------------------

Setuptools is maintained by the Python community under the Python Packaging
Authority (PyPA) and led by Jason R. Coombs.

This document describes the process by which Setuptools is developed.
This document assumes the reader has some passing familiarity with
*using* setuptools, the ``pkg_resources`` module, and pip.  It
does not attempt to explain basic concepts like inter-project
dependencies, nor does it contain detailed lexical syntax for most
file formats.  Neither does it explain concepts like "namespace
packages" or "resources" in any detail, as all of these subjects are
covered at length in the setuptools developer's guide and the
``pkg_resources`` reference manual.

Instead, this is **internal** documentation for how those concepts and
features are *implemented* in concrete terms.  It is intended for people
who are working on the setuptools code base, who want to be able to
troubleshoot setuptools problems, want to write code that reads the file
formats involved, or want to otherwise tinker with setuptools-generated
files and directories.

Note, however, that these are all internal implementation details and
are therefore subject to change; stick to the published API if you don't
want to be responsible for keeping your code from breaking when
setuptools changes.  You have been warned.

.. toctree::
   :maxdepth: 1

   developer-guide
   formats
   releases
