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
defined thus::

    project_root_directory
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── timmins
            ├── __init__.py
            └── ...

with ``__init__.py`` as:

.. code-block:: python

    def hello_world():
        print("Hello world")

Now, suppose that we would like to provide some way of executing the
function ``hello_world()`` from the command-line. One way to do this
is to create a file ``src/timmins/__main__.py`` providing a hook as
follows:

.. code-block:: python

    from . import hello_world

    if __name__ == '__main__':
        hello_world()

Then, after installing the package ``timmins``, we may invoke the ``hello_world()``
function as follows, through the `runpy <https://docs.python.org/3/library/runpy.html>`_
module:

.. code-block:: bash

    $ python -m timmins
    Hello world

Instead of this approach using ``__main__.py``, you can also create a
user-friendly CLI executable that can be called directly without ``python -m``.
In the above example, to create a command ``hello-world`` that invokes
``timmins.hello_world``, add a console script entry point to your
configuration:

.. tab:: setup.cfg

	.. code-block:: ini

		[options.entry_points]
		console_scripts =
			hello-world = timmins:hello_world

.. tab:: setup.py

    .. code-block:: python
	
        from setuptools import setup

        setup(
            # ...,
            entry_points={
                'console_scripts': [
                    'hello-world=timmins:hello_world',
                ]
            }
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [project.scripts]
        hello-world = "timmins:hello_world"


After installing the package, a user may invoke that function by simply calling
``hello-world`` on the command line:

.. code-block:: bash

   $ hello-world
   Hello world

Note that any function configured as a console script, i.e. ``hello_world()`` in
this example, should not accept any arguments. If your function requires any input
from the user, you can use regular command-line argument parsing utilities like
`argparse <https://docs.python.org/3/library/argparse.html>`_ within the body of
the function to parse user input given via :obj:`sys.argv`.

The syntax for entry points is specified as follows:

.. code-block:: ini

    <name> = [<package>.[<subpackage>.]]<module>[:<object>.<object>]

where ``name`` is the name for the script you want to create, the left hand
side of ``:`` is the module that contains your function and the right hand
side is the object you want to invoke (e.g. a function).

GUI Scripts
===========

In addition to ``console_scripts``, Setuptools supports ``gui_scripts``, which
will launch a GUI application without running in a terminal window.

For example, if we have a project with the same directory structure as before,
with an ``__init__.py`` file containing the following:

.. code-block:: python

    import PySimpleGUI as sg

    def hello_world():
        sg.Window(title="Hello world", layout=[[]], margins=(100, 50)).read()

Then, we can add a GUI script entry point:

.. tab:: setup.cfg

    .. code-block:: ini

        [options.entry_points]
        gui_scripts =
            hello-world = timmins:hello_world

.. tab:: setup.py

    .. code-block:: python
	
        from setuptools import setup

        setup(
            # ...,
            entry_points={
                'gui_scripts': [
                    'hello-world=timmins:hello_world',
                ]
            }
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [project.gui-scripts]
        hello-world = "timmins:hello_world"

.. note::
   To be able to import ``PySimpleGUI``, you need to add ``pysimplegui`` to your package dependencies.
   See :doc:`/userguide/dependency_management` for more information.

Now, running:

.. code-block:: bash

   $ hello-world

will open a small application window with the title 'Hello world'.

Note that just as with console scripts, any function configured as a GUI script
should not accept any arguments, and any user input can be parsed within the
body of the function.

.. note::

    The difference between ``console_scripts`` and ``gui_scripts`` only affects
    Windows systems. [#use_for_scripts]_ ``console_scripts`` are wrapped in a console
    executable, so they are attached to a console and can use ``sys.stdin``,
    ``sys.stdout`` and ``sys.stderr`` for input and output. ``gui_scripts`` are
    wrapped in a GUI executable, so they can be started without a console, but
    cannot use standard streams unless application code redirects them. Other
    platforms do not have the same distinction.

.. note::

    Console and GUI scripts work because behind the scenes, installers like :pypi:`pip`
    create wrapper scripts around the function(s) being invoked. For example,
    the ``hello-world`` entry point in the above two examples would create a
    command ``hello-world`` launching a script like this: [#use_for_scripts]_

    .. code-block:: python

        import sys
        from timmins import hello_world
        sys.exit(hello_world())

.. _dynamic discovery of services and plugins:

Advertising Behavior
====================

Console/GUI scripts are one use of the more general concept of entry points. Entry
points more generally allow a packager to advertise behavior for discovery by
other libraries and applications. This feature enables "plug-in"-like
functionality, where one library solicits entry points and any number of other
libraries provide those entry points.

A good example of this plug-in behavior can be seen in
`pytest plugins <https://docs.pytest.org/en/latest/writing_plugins.html>`_,
where pytest is a test framework that allows other libraries to extend
or modify its functionality through the ``pytest11`` entry point.

The console/GUI scripts work similarly, where libraries advertise their commands
and tools like ``pip`` create wrapper scripts that invoke those commands.

Entry Points for Plugins
========================

Let us consider a simple example to understand how we can implement entry points
corresponding to plugins. Say we have a package ``timmins`` with the following
directory structure::

    timmins
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── timmins
            └── __init__.py

and in ``src/timmins/__init__.py`` we have the following code:

.. code-block:: python

   def hello_world():
       print('Hello world')

Basically, we have defined a ``hello_world()`` function which will print the text
'Hello world'. Now, let us say we want to print the text 'Hello world' in different
ways. The current function just prints the text as it is - let us say we want another
style in which the text is enclosed within exclamation marks::

    !!! Hello world !!!

Let us see how this can be done using plugins. First, let us separate the style of
printing the text from the text itself. In other words, we can change the code in
``src/timmins/__init__.py`` to something like this:

.. code-block:: python

   def display(text):
       print(text)

   def hello_world():
       display('Hello world')

Here, the ``display()`` function controls the style of printing the text, and the
``hello_world()`` function calls the ``display()`` function to print the text 'Hello
world`.

Right now the ``display()`` function just prints the text as it is. In order to be able
to customize it, we can do the following. Let us introduce a new *group* of entry points
named ``timmins.display``, and expect plugin packages implementing this entry point
to supply a ``display()``-like function. Next, to be able to automatically discover plugin
packages that implement this entry point, we can use the
:mod:`importlib.metadata` module,
as follows:

.. code-block:: python

   from importlib.metadata import entry_points
   display_eps = entry_points(group='timmins.display')

.. note::
   Each ``importlib.metadata.EntryPoint`` object is an object containing a ``name``, a
   ``group``, and a ``value``. For example, after setting up the plugin package as
   described below, ``display_eps`` in the above code will look like this: [#package_metadata]_

    .. code-block:: python

        (
            EntryPoint(name='excl', value='timmins_plugin_fancy:excl_display', group='timmins.display'),
            ...,
        )

``display_eps`` will now be a list of ``EntryPoint`` objects, each referring to ``display()``-like
functions defined by one or more installed plugin packages. Then, to import a specific
``display()``-like function - let us choose the one corresponding to the first discovered
entry point - we can use the ``load()`` method as follows:

.. code-block:: python

   display = display_eps[0].load()

Finally, a sensible behaviour would be that if we cannot find any plugin packages customizing
the ``display()`` function, we should fall back to our default implementation which prints
the text as it is. With this behaviour included, the code in ``src/timmins/__init__.py``
finally becomes:

.. code-block:: python

   from importlib.metadata import entry_points
   display_eps = entry_points(group='timmins.display')
   try:
       display = display_eps[0].load()
   except IndexError:
       def display(text):
           print(text)

   def hello_world():
       display('Hello world')

That finishes the setup on ``timmins``'s side. Next, we need to implement a plugin
which implements the entry point ``timmins.display``. Let us name this plugin
``timmins-plugin-fancy``, and set it up with the following directory structure::

    timmins-plugin-fancy
    ├── setup.py        # and/or setup.cfg, pyproject.toml
    └── src
        └── timmins_plugin_fancy
            └── __init__.py

And then, inside ``src/timmins_plugin_fancy/__init__.py``, we can put a function
named ``excl_display()`` that prints the given text surrounded by exclamation marks:

.. code-block:: python

   def excl_display(text):
       print('!!!', text, '!!!')

This is the ``display()``-like function that we are looking to supply to the
``timmins`` package. We can do that by adding the following in the configuration
of ``timmins-plugin-fancy``:

.. tab:: setup.cfg

   .. code-block:: ini

        [options.entry_points]
        timmins.display =
                excl = timmins_plugin_fancy:excl_display

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup

        setup(
            # ...,
            entry_points = {
                'timmins.display' = [
                    'excl=timmins_plugin_fancy:excl_display'
                ]
            }
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [project.entry-points."timmins.display"]
        excl = "timmins_plugin_fancy:excl_display"

Basically, this configuration states that we are a supplying an entry point
under the group ``timmins.display``. The entry point is named ``excl`` and it
refers to the function ``excl_display`` defined by the package ``timmins_plugin_fancy``.

Now, if we install both ``timmins`` and ``timmins_plugin_fancy``, we should get
the following:

.. code-block:: pycon

   >>> from timmins import hello_world
   >>> hello_world()
   !!! Hello world !!!

whereas if we only install ``timmins`` and not ``timmins_plugin_fancy``, we should
get the following:

.. code-block:: pycon

   >>> from timmins import hello_world
   >>> hello_world()
   Hello world

Therefore, our plugin works.

Our plugin could have also defined multiple entry points under the group ``timmins.display``.
For example, in ``src/timmins_plugin_fancy/__init__.py`` we could have two ``display()``-like
functions, as follows:

.. code-block:: python

   def excl_display(text):
       print('!!!', text, '!!!')

   def lined_display(text):
       print(''.join(['-' for _ in text]))
       print(text)
       print(''.join(['-' for _ in text]))

The configuration of ``timmins-plugin-fancy`` would then change to:

.. tab:: setup.cfg

   .. code-block:: ini

        [options.entry_points]
        timmins.display =
                excl = timmins_plugin_fancy:excl_display
                lined = timmins_plugin_fancy:lined_display

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup

        setup(
            # ...,
            entry_points = {
                'timmins.display' = [
                    'excl=timmins_plugin_fancy:excl_display',
                    'lined=timmins_plugin_fancy:lined_display',
                ]
            }
        )

.. tab:: pyproject.toml (**EXPERIMENTAL**) [#experimental]_

   .. code-block:: toml

        [project.entry-points."timmins.display"]
        excl = "timmins_plugin_fancy:excl_display"
        lined = "timmins_plugin_fancy:lined_display"

On the ``timmins`` side, we can also use a different strategy of loading entry
points. For example, we can search for a specific display style:

.. code-block:: python

   display_eps = entry_points(group='timmins.display')
   try:
       display = display_eps['lined'].load()
   except KeyError:
       # if the 'lined' display is not available, use something else
       ...

Or we can also load all plugins under the given group. Though this might not
be of much use in our current example, there are several scenarios in which this
is useful:

.. code-block:: python

   display_eps = entry_points(group='timmins.display')
   for ep in display_eps:
       display = ep.load()
       # do something with display
       ...

importlib.metadata
------------------

The recommended approach for loading and importing entry points is the
:mod:`importlib.metadata` module,
which is a part of the standard library since Python 3.8. For older versions of
Python, its backport :pypi:`importlib_metadata` should be used. While using the
backport, the only change that has to be made is to replace ``importlib.metadata``
with ``importlib_metadata``, i.e.

.. code-block:: python

   from importlib_metadata import entry_points
   ...

Summary
-------

In summary, entry points allow a package to open its functionalities for
customization via plugins.
The package soliciting the entry points need not have any dependency
or prior knowledge about the plugins implementing the entry points, and
downstream users are able to compose functionality by pulling together
plugins implementing the entry points.


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

----

.. [#experimental]
   Support for specifying package metadata and build configuration options via
   ``pyproject.toml`` is experimental and might change
   in the future. See :doc:`/userguide/pyproject_config`.

.. [#use_for_scripts]
   Reference: https://packaging.python.org/en/latest/specifications/entry-points/#use-for-scripts

.. [#package_metadata]
   Reference: https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-package-metadata
