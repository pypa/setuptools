.. _`entry_points`:

============
Entry Points
============

Packages may provide commands to be run at the console (console scripts),
such as the ``pip`` command. These commands are defined for a package
as a specific kind of entry point in the ``setup.cfg`` or
``setup.py``.


Console Scripts
===============

First consider an example without entry points. Imagine a package
defined thus:

.. code-block:: bash

    timmins/
        timmins/__init__.py
        timmins/__main__.py
        setup.cfg # or setup.py
        #other necessary files

with ``__init__.py`` as:

.. code-block:: python

    def hello_world():
        print("Hello world")

and ``__main__.py`` providing a hook:

.. code-block:: python

    from . import hello_world

    if __name__ == '__main__':
        hello_world()

After installing the package, the function may be invoked through the
`runpy <https://docs.python.org/3/library/runpy.html>`_ module:

.. code-block:: bash

    python -m timmins

Adding a console script entry point allows the package to define a
user-friendly name for installers of the package to execute. Installers
like pip will create wrapper scripts to execute a function. In the
above example, to create a command ``hello-world`` that invokes
``timmins.hello_world``, add a console script entry point to
``setup.cfg``:

.. code-block:: ini

    [options.entry_points]
    console_scripts =
        hello-world = timmins:hello_world

After installing the package, a user may invoke that function by simply calling
``hello-world`` on the command line.

The syntax for entry points is specified as follows:

.. code-block:: ini

    <name> = [<package>.[<subpackage>.]]<module>[:<object>.<object>]

where ``name`` is the name for the script you want to create, the left hand
side of ``:`` is the module that contains your function and the right hand
side is the object you want to invoke (e.g. a function).

In addition to ``console_scripts``, Setuptools supports ``gui_scripts``, which
will launch a GUI application without running in a terminal window.


.. _dynamic discovery of services and plugins:

Advertising Behavior
====================

Console scripts are one use of the more general concept of entry points. Entry
points more generally allow a packager to advertise behavior for discovery by
other libraries and applications. This feature enables "plug-in"-like
functionality, where one library solicits entry points and any number of other
libraries provide those entry points.

A good example of this plug-in behavior can be seen in
`pytest plugins <https://docs.pytest.org/en/latest/writing_plugins.html>`_,
where pytest is a test framework that allows other libraries to extend
or modify its functionality through the ``pytest11`` entry point.

The console scripts work similarly, where libraries advertise their commands
and tools like ``pip`` create wrapper scripts that invoke those commands.

For a project wishing to solicit entry points, Setuptools recommends the
`importlib.metadata <https://docs.python.org/3/library/importlib.metadata.html>`_
module (part of stdlib since Python 3.8) or its backport,
`importlib_metadata <https://pypi.org/project/importlib_metadata>`_.

For example, to find the console script entry points from the example above:

.. code-block:: pycon

    >>> from importlib import metadata
    >>> eps = metadata.entry_points()['console_scripts']

``eps`` is now a list of ``EntryPoint`` objects, one of which corresponds
to the ``hello-world = timmins:hello_world`` defined above. Each ``EntryPoint``
contains the ``name``, ``group``, and ``value``. It also supplies a ``.load()``
method to import and load that entry point (module or object).

.. code-block:: ini

    [options.entry_points]
    my.plugins =
        hello-world = timmins:hello_world

Then, a different project wishing to load 'my.plugins' plugins could run
the following routine to load (and invoke) such plugins:

.. code-block:: pycon

    >>> from importlib import metadata
    >>> eps = metadata.entry_points()['my.plugins']
    >>> for ep in eps:
    ...     plugin = ep.load()
    ...     plugin()
    ...

The project soliciting the entry points needs not to have any dependency
or prior knowledge about the libraries implementing the entry points, and
downstream users are able to compose functionality by pulling together
libraries implementing the entry points.


Dependency Management
=====================

Some entry points may require additional dependencies to properly function.
For such an entry point, declare in square brackets any number of dependency
``extras`` following the entry point definition. Such entry points will only
be viable if their extras were declared and installed. See the
:doc:`guide on dependencies management <dependency_management>` for
more information on defining extra requirements. Consider from the
above example:

.. code-block:: ini

    [options.entry_points]
    console_scripts =
        hello-world = timmins:hello_world [pretty-printer]

In this case, the ``hello-world`` script is only viable if the ``pretty-printer``
extra is indicated, and so a plugin host might exclude that entry point
(i.e. not install a console script) if the relevant extra dependencies are not
installed.
