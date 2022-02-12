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
overhaul. Because ``setup.py`` scripts allowed for arbitrary execution, it
proved difficult to provide a reliable user experience across environments
and history.

`PEP 517 <https://www.python.org/dev/peps/pep-0517/>`_ therefore came to
rescue and specified a new standard to
package and distribute Python modules. Under PEP 517:

    a ``pyproject.toml`` file is used to specify what program to use
    for generating distribution.

    Then, two functions provided by the program, ``build_wheel(directory: str)``
    and ``build_sdist(directory: str)`` create the distribution bundle at the
    specified ``directory``. The program is free to use its own configuration
    script or extend the ``.toml`` file.

    Lastly, ``pip install *.whl`` or ``pip install *.tar.gz`` does the actual
    installation. If ``*.whl`` is available, ``pip`` will go ahead and copy
    the files into ``site-packages`` directory. If not, ``pip`` will look at
    ``pyproject.toml`` and decide what program to use to 'build from source'
    (the default is ``setuptools``)

With this standard, switching between packaging tools becomes a lot easier. ``build_meta``
implements ``setuptools``' build system support.

How to use it?
--------------

Starting with a package that you want to distribute. You will need your source
scripts, a ``pyproject.toml`` file and a ``setup.cfg`` file::

    ~/meowpkg/
        pyproject.toml
        setup.cfg
        meowpkg/__init__.py

The pyproject.toml file is required to specify the build system (i.e. what is
being used to package your scripts and install from source). To use it with
setuptools, the content would be::

    [build-system]
    requires = ["setuptools"]
    build-backend = "setuptools.build_meta"

The ``setuptools`` package implements the ``build_sdist``
command and the ``wheel`` package implements the ``build_wheel``
command; the latter is a dependency of the former
exposed via :pep:`517` hooks.

Use ``setuptools``' :ref:`declarative config <declarative config>` to
specify the package information::

    [metadata]
    name = meowpkg
    version = 0.0.1
    description = a package that meows

    [options]
    packages = find:

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

Dynamic build dependencies and other ``build_meta`` tweaks
----------------------------------------------------------

With the changes introduced by :pep:`517` and :pep:`518`, the
``setup_requires`` configuration field was made deprecated in ``setup.cfg`` and
``setup.py``, in favour of directly listing build dependencies in the
``requires`` field of the ``build-system`` table of ``pyproject.toml``.
This approach has a series of advantages and gives package managers and
installers the ability to inspect in advance the build requirements and
perform a series of optimisations.

However some package authors might still need to dynamically inspect the final
users machine before deciding these requirements. One way of doing that, as
specified by :pep:`517`, is to "tweak" ``setuptools.build_meta`` by using a
:pep:`in-tree backend <517#in-tree-build-backends>`.

.. tip:: Before implementing a *in-tree* backend, have a look on
   :pep:`PEP 508 <508#environment-markers>`. Most of the times, dependencies
   with **environment markers** are enough to differentiate operating systems
   and platforms.

If you add the following configuration to your ``pyprojec.toml``:


.. code-block:: toml

    [build-system]
    requires = ["setuptools", "wheel"]
    build-backend = "backend"
    backend-path = ["_custom_build"]


then you should be able to implement a thin wrapper around ``build_meta`` in
the ``_custom_build/backend.py`` file, as shown in the following example:

.. code-block:: python

    from setuptools import build_meta as _orig

    prepare_metadata_for_build_wheel = _orig.prepare_metadata_for_build_wheel
    build_wheel = _orig.build_wheel
    build_sdist = _orig.build_sdist


    def get_requires_for_build_wheel(self, config_settings=None):
        return _orig.get_requires_for_build_wheel(config_settings) + [...]


    def get_requires_for_build_sdist(self, config_settings=None):
        return _orig.get_requires_for_build_sdist(config_settings) + [...]


Note that you can override any of the functions specified in :pep:`PEP 517
<517#build-backend-interface>`, not only the ones responsible for gathering
requirements.

.. important:: Make sure your backend script is included in the :doc:`source
   distribution </userguide/distribution>`, otherwise the build will fail.
   This can be done by using a SCM_/VCS_ plugin (like :pypi:`setuptools-scm`
   and :pypi:`setuptools-svn`), or by correctly setting up :ref:`MANIFEST.in
   <manifest>`.

   If this is the first time you are using a customised backend, please have a
   look on the generated ``.tar.gz`` and ``.whl``.
   On POSIX systems that can be done with ``tar -tf dist/*.tar.gz``
   and ``unzip -l dist/*.whl``.
   On Windows systems you can rename the ``.whl`` to ``.zip`` to be able to
   inspect it on the file explorer, and use the same ``tar`` command in a
   command prompt (alternativelly there are GUI programs like `7-zip`_ that
   handle ``.tar.gz``).

   In general the backend script should be present in the ``.tar.gz`` (so the
   project can be build from the source) but not in the ``.whl`` (otherwise the
   backend script would end up being distributed alongside your package).
   See ":doc:`/userguide/package_discovery`" for more details about package
   files.


.. _SCM: https://en.wikipedia.org/wiki/Software_configuration_management
.. _VCS: https://en.wikipedia.org/wiki/Version_control
.. _7-zip: https://www.7-zip.org
