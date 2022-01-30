==================================================
Building and Distributing Packages with Setuptools
==================================================

``Setuptools`` is a collection of enhancements to the Python ``distutils``
that allow developers to more easily build and
distribute Python packages, especially ones that have dependencies on other
packages.

Packages built and distributed using ``setuptools`` look to the user like
ordinary Python packages based on the ``distutils``.

Transition to PEP517
====================

Since setuptools no longer serves as the default build tool, one must explicitly
opt in (by providing a :file:`pyproject.toml` file) to use this library. The user
facing part is provided by tools such as pip and
backend interface is described :doc:`in this document <../build_meta>`. The
quickstart provides an overview of the new workflow.

.. toctree::
    :maxdepth: 1

    quickstart
    package_discovery
    entry_point
    dependency_management
    datafiles
    development_mode
    distribution
    extension
    declarative_config
    keywords
    commands
    functionalities_rewrite
    miscellaneous
