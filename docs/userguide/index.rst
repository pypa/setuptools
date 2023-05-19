==================================================
Building and Distributing Packages with Setuptools
==================================================

The first step towards sharing a Python library or program is to build a
distribution package [#package-overload]_. This includes adding a set of
additional files containing metadata and configuration to not only instruct
``setuptools`` on how the distribution should be built but also
to help installer (such as :pypi:`pip`) during the installation process.

This document contains information to help Python developers through this
process. Please check the :doc:`/userguide/quickstart` for an overview of
the workflow.

Also note that ``setuptools`` is what is known in the community as :pep:`build
backend <517#terminology-and-goals>`, user facing interfaces are provided by tools
such as :pypi:`pip` and :pypi:`build`. To use ``setuptools``, one must
explicitly create a ``pyproject.toml`` file as described :doc:`/build_meta`.


Contents
========

.. toctree::
    :maxdepth: 1

    quickstart
    package_discovery
    dependency_management
    development_mode
    entry_point
    datafiles
    ext_modules
    distribution
    miscellaneous
    extension
    declarative_config
    pyproject_config

---

.. rubric:: Notes

.. [#package-overload]
   A :term:`Distribution Package` is also referred in the Python community simply as "package"
   Unfortunately, this jargon might be a bit confusing for new users because the term package
   can also to refer any :term:`directory <package>` (or sub directory) used to organize
   :term:`modules <module>` and auxiliary files.
