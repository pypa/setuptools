.. image:: images/banner-640x320.svg
   :align: center

About
=============

Setuptools is a fully-featured, actively-maintained, and stable library designed for
packaging Python projects. It helps developers to easily share Python/Cython libraries,
tools and and applications in standard formats (sdist, bdist, wheel..) that can be
uploaded to `PyPI <http://pypi.org>`_ and installed with :pypi:`pip`.

For a long time it was the semi-official replacement for distutils, and de facto
specification for package management/bundling/installation, using *setup.py*/*setup.cfg*.
In the build system/model established by PEP 517/518, it is a **build backend**, and since
:pep:`621` the files *setup.py/setup.cfg* are deprecated and are being replaced by configuration
with ``pyproject.toml``


Documentation
=============

To begin using setuptools, see the :doc:`User Guide <userguide/index>`.

To begin contributing to setuptools, see the :doc:`Developer Guide <development/index>`.



Forum and Bug Tracker
=====================

Please use `GitHub Discussions`_ for questions and discussion about
setuptools, and the `setuptools bug tracker`_ ONLY for issues you have
confirmed via the forum are actual bugs, and which you have reduced to a minimal
set of steps to reproduce.

.. _GitHub Discussions: https://github.com/pypa/setuptools/discussions
.. _setuptools bug tracker: https://github.com/pypa/setuptools/




.. toctree::
   :maxdepth: 1
   :hidden:

   User guide <userguide/index>
   build_meta
   pkg_resources
   references/keywords

.. toctree::
   :caption: Project
   :maxdepth: 1
   :hidden:

   roadmap
   Development guide <development/index>
   Backward compatibility & deprecated practice <deprecated/index>
   Changelog <history>
   artwork

.. tidelift-referral-banner::
