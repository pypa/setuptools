=======================================
Build System Support
=======================================

What is it?
-------------

Python packaging has come `a long way <https://bernat.tech/posts/pep-517-518/>`_.

The traditional ``setuptools`` way of packaging Python modules
uses a ``setup()`` function within the ``setup.py`` script. Commands such as
``python setup.py bdist`` or ``python setup.py bdist_wheel`` generate a
distribution bundle and ``python setup.py install`` installs the distribution.
This interface makes it difficult to choose other packaging tools without an
overhaul. Because ``setup.py`` scripts allow for arbitrary execution, it
is difficult to provide a reliable user experience across environments
and history.

:pep:`517` came to
the rescue and specified a new standard for packaging and distributing Python
modules. Under PEP 517:

    A ``pyproject.toml`` file is used to specify which program to use
    to generate the distribution.

    Two functions provided by the program, ``build_wheel(directory: str)``
    and ``build_sdist(directory: str)``, create the distribution bundle in the
    specified ``directory``.

    The program may use its own configuration file or extend the ``.toml`` file.

    The actual installation is done with ``pip install *.whl`` or
    ``pip install *.tar.gz``. If ``*.whl`` is available, ``pip`` will go ahead and copy
    its files into the ``site-packages`` directory. If not, ``pip`` will look at
    ``pyproject.toml`` and decide which program to use to 'build from source'.
    (Note that if there is no ``pyproject.toml`` file or the ``build-backend``
    parameter is not defined, then the fall-back behaviour is to use ``setuptools``.)

With this standard, switching between packaging tools is a lot easier.

How to use it?
--------------

Start with a package that you want to distribute. You will need your source
files, a ``pyproject.toml`` file and a ``setup.cfg`` file::

    ~/meowpkg/
        pyproject.toml
        setup.cfg
        meowpkg/
            __init__.py
            module.py

The ``pyproject.toml`` file specifies the build system (i.e. what is
being used to package your scripts and install from source). To use it with
``setuptools`` the content would be::

    [build-system]
    requires = ["setuptools"]
    build-backend = "setuptools.build_meta"

``build_meta`` implements ``setuptools``' build system support.
The ``setuptools`` package implements the ``build_sdist``
command and the ``wheel`` package implements the ``build_wheel``
command; the latter is a dependency of the former
exposed via :pep:`517` hooks.

Use ``setuptools``' :ref:`declarative config <declarative config>` to
specify the package information in ``setup.cfg``::

    [metadata]
    name = meowpkg
    version = 0.0.1
    description = a package that meows

    [options]
    packages = find:

.. _building:

Now generate the distribution. To build the package, use
`PyPA build <https://pypa-build.readthedocs.io/en/latest/>`_::

    $ pip install -q build
    $ python -m build

And now it's done! The ``.whl`` file  and ``.tar.gz`` can then be distributed
and installed::

    dist/
        meowpkg-0.0.1.whl
        meowpkg-0.0.1.tar.gz

    $ pip install dist/meowpkg-0.0.1.whl

or::

    $ pip install dist/meowpkg-0.0.1.tar.gz


.. _backend-wrapper:

Dynamic build dependencies and other ``build_meta`` tweaks
----------------------------------------------------------

With the changes introduced by :pep:`517` and :pep:`518`, the
``setup_requires`` configuration field was deprecated in ``setup.cfg`` and
``setup.py``, in favour of directly listing build dependencies in the
``requires`` field of the ``build-system`` table of ``pyproject.toml``.
This approach has a series of advantages and gives package managers and
installers the ability to inspect the build requirements in advance and
perform a series of optimisations.

However, some package authors might still need to dynamically inspect the final
user's machine before deciding these requirements. One way of doing that, as
specified by :pep:`517`, is to "tweak" ``setuptools.build_meta`` by using an
:pep:`in-tree backend <517#in-tree-build-backends>`.

.. tip:: Before implementing an *in-tree* backend, have a look at
   :pep:`PEP 508 <508#environment-markers>`. Most of the time, dependencies
   with **environment markers** are enough to differentiate operating systems
   and platforms.

If you put the following configuration in your ``pyproject.toml``:

.. code-block:: toml

    [build-system]
    requires = ["setuptools"]
    build-backend = "backend"
    backend-path = ["_custom_build"]


then you can implement a thin wrapper around ``build_meta`` in
the ``_custom_build/backend.py`` file, as shown in the following example:

.. code-block:: python

    from setuptools import build_meta as _orig
    from setuptools.build_meta import *


    def get_requires_for_build_wheel(config_settings=None):
        return _orig.get_requires_for_build_wheel(config_settings) + [...]


    def get_requires_for_build_sdist(config_settings=None):
        return _orig.get_requires_for_build_sdist(config_settings) + [...]


.. note::

   You can override any of the functions specified in :pep:`PEP 517
   <517#build-backend-interface>`, not only the ones responsible for gathering
   requirements. It is important to ``import *`` so that the hooks that you
   choose not to reimplement would be inherited from the setuptools' backend
   automatically. This will also cover hooks that might be added in the future
   like the ones that :pep:`660` declares.


.. important:: Make sure your backend script is included in the :doc:`source
   distribution </userguide/distribution>`, otherwise the build will fail.
   This can be done by using a SCM_/VCS_ plugin (like :pypi:`setuptools-scm`
   and :pypi:`setuptools-svn`), or by correctly setting up :ref:`MANIFEST.in
   <manifest>`.

   The generated ``.tar.gz`` and ``.whl`` files are compressed archives that
   can be inspected as follows:
   On POSIX systems, this can be done with ``tar -tf dist/*.tar.gz``
   and ``unzip -l dist/*.whl``.
   On Windows systems, you can rename the ``.whl`` to ``.zip`` to be able to
   inspect it from File Explorer. You can also use the above ``tar`` command in a
   command prompt to inspect the ``.tar.gz`` file. Alternatively, there are GUI programs
   like `7-zip`_ that handle ``.tar.gz`` and ``.whl`` files.

   In general, the backend script should be present in the ``.tar.gz`` (so the
   project can be built from the source) but not in the ``.whl`` (otherwise the
   backend script would end up being distributed alongside your package).
   See ":doc:`/userguide/package_discovery`" for more details about package
   files.


.. _SCM: https://en.wikipedia.org/wiki/Software_configuration_management
.. _VCS: https://en.wikipedia.org/wiki/Version_control
.. _7-zip: https://www.7-zip.org
