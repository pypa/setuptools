=======================================
Build System Support
=======================================

What is it?
-------------

Python packaging has come `a long way <https://www.bernat.tech/pep-517-518/>`_.

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
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta" 

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
