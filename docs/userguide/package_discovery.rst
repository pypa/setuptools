.. _`package_discovery`:

========================================
Package Discovery and Namespace Package
========================================

.. note::
    a full specification for the keyword supplied to ``setup.cfg`` or
    ``setup.py`` can be found at :doc:`keywords reference <keywords>`

.. note::
    the examples provided here are only to demonstrate the functionality
    introduced. More metadata and options arguments need to be supplied
    if you want to replicate them on your system. If you are completely
    new to setuptools, the :doc:`quickstart section <quickstart>` is a good
    place to start.

``Setuptools`` provide powerful tools to handle package discovery, including
support for namespace package. Normally, you would specify the package to be
included manually in the following manner:

.. code-block:: ini

    [options]
    #...
    packages =
        mypkg1
        mypkg2

.. code-block:: python

    setup(
        #...
        packages = ['mypkg1', 'mypkg2']
    )

This can get tiresome reallly quickly. To speed things up, we introduce two
functions provided by setuptools:

.. code-block:: ini

    [options]
    packages = find:
    #or
    packages = find_namespace:

.. code-block:: python

    from setuptools import find_packages
    #or
    from setuptools import find_namespace_packages


Using ``find:`` or ``find_packages``
====================================
Let's start with the first tool. ``find:`` (``find_packages``) takes a source
directory and two lists of package name patterns to exclude and include, and
then return a list of ``str`` representing the packages it could find. To use
it, consider the following directory

.. code-block:: bash

    mypkg/
        src/
            pkg1/__init__.py
            pkg2/__init__.py
            additional/__init__.py

        setup.cfg #or setup.py

To have your setup.cfg or setup.py to automatically include packages found
in ``src`` that starts with the name ``pkg`` and not ``additional``:

.. code-block:: ini

    [options]
    packages = find:
    package_dir =
        =src

    [options.packages.find]
    where = src
    include = pkg*
    exclude = additional

.. code-block:: python

    setup(
        #...
        packages = find_packages(
            where = 'src',
            include = ['pkg*',],
            exclude = ['additional',]
        ),
        package_dir = {"":"src"}
        #...
    )


.. _Namespace Packages:

Using ``find_namespace:`` or ``find_namespace_packages``
========================================================
``setuptools``  provides the ``find_namespace:`` (``find_namespace_packages``)
which behaves similarly to ``find:`` but works with namespace package. Before
diving in, it is important to have a good understanding of what namespace
packages are. Here is a quick recap:

Suppose you have two packages named as follows:

.. code-block:: bash

    /Users/Desktop/timmins/foo/__init__.py
    /Library/timmins/bar/__init__.py

If both ``Desktop`` and ``Library`` are on your ``PYTHONPATH``, then a
namespace package called ``timmins`` will be created automatically for you when
you invoke the import mechanism, allowing you to accomplish the following

.. code-block:: python

    >>> import timmins.foo
    >>> import timmins.bar

as if there is only one ``timmins`` on your system. The two packages can then
be distributed separately and installed individually without affecting the
other one. Suppose you are packaging the ``foo`` part:

.. code-block:: bash

    foo/
        src/
            timmins/foo/__init__.py
        setup.cfg # or setup.py

and you want the ``foo`` to be automatically included, ``find:`` won't work
because timmins doesn't contain ``__init__.py`` directly, instead, you have
to use ``find_namespace:``:

.. code-block:: ini

    [options]
    package_dir =
        =src
    packages = find_namespace:

    [options.packages.find_namespace]
    where = src

When you install the zipped distribution, ``timmins.foo`` would become
available to your interpreter.

You can think of ``find_namespace:`` as identical to ``find:`` except it
would count a directory as a package even if it doesn't contain ``__init__.py``
file directly. As a result, this creates an interesting side effect. If you
organize your package like this:

.. code-block:: bash

    foo/
        timmins/
            foo/__init__.py
        setup.cfg # or setup.py
        tests/
            test_foo/__init__.py

a naive ``find_namespace:`` would include tests as part of your package to
be installed. A simple way to fix it is to adopt the aforementioned
``src`` layout.


Legacy Namespace Packages
=========================
The fact you can create namespace package so effortlessly above is credited
to `PEP 420 <https://www.python.org/dev/peps/pep-0420/>`_. It use to be more
cumbersome to accomplish the same result. Historically, there were two methods
to create namespace packages. One is the ``pkg_resources`` style supported by
``setuptools`` and the other one being ``pkgutils`` style offered by
``pkgutils`` module in Python. Both are now considered deprecated despite the
fact they still linger in many existing packages. These two differ in many
subtle yet significant aspects and you can find out more on `Python packaging
user guide <https://packaging.python.org/guides/packaging-namespace-packages/>`_


``pkg_resource`` style namespace package
----------------------------------------
This is the method ``setuptools`` directly supports. Starting with the same
layout, there are two pieces you need to add to it. First, an ``__init__.py``
file directly under your namespace package directory that contains the
following:

.. code-block:: python

    __import__("pkg_resources").declare_namespace(__name__)

And the ``namespace_packages`` keyword in your ``setup.cfg`` or ``setup.py``:

.. code-block:: ini

    [options]
    namespace_packages = timmins

.. code-block:: python

    setup(
        # ...
        namespace_packages = ['timmins']
    )

And your directory should look like this

.. code-block:: bash

    /foo/
        src/
            timmins/
                __init__.py
                foo/__init__.py
        setup.cfg #or setup.py

Repeat the same for other packages and you can achieve the same result as
the previous section.

``pkgutil`` style namespace package
-----------------------------------
This method is almost identical to the ``pkg_resource`` except that the
``namespace_packages`` declaration is omitted and the ``__init__.py``
file contains the following:

.. code-block:: python

    __path__ = __import__('pkgutil').extend_path(__path__, __name__)

The project layout remains the same and ``setup.cfg`` remains the same.
