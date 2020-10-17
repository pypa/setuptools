.. _Creating ``distutils`` Extensions:

Creating ``distutils`` Extensions
=================================

It can be hard to add new commands or setup arguments to the distutils.  But
the ``setuptools`` package makes it a bit easier, by allowing you to distribute
a distutils extension as a separate project, and then have projects that need
the extension just refer to it in their ``setup_requires`` argument.

With ``setuptools``, your distutils extension projects can hook in new
commands and ``setup()`` arguments just by defining "entry points".  These
are mappings from command or argument names to a specification of where to
import a handler from.  (See the section on :ref:`Dynamic Discovery of
Services and Plugins` above for some more background on entry points.)


Adding Commands
---------------

You can add new ``setup`` commands by defining entry points in the
``distutils.commands`` group.  For example, if you wanted to add a ``foo``
command, you might add something like this to your distutils extension
project's setup script::

    setup(
        # ...
        entry_points={
            "distutils.commands": [
                "foo = mypackage.some_module:foo",
            ],
        },
    )

(Assuming, of course, that the ``foo`` class in ``mypackage.some_module`` is
a ``setuptools.Command`` subclass.)

Once a project containing such entry points has been activated on ``sys.path``,
(e.g. by running "install" or "develop" with a site-packages installation
directory) the command(s) will be available to any ``setuptools``-based setup
scripts.  It is not necessary to use the ``--command-packages`` option or
to monkeypatch the ``distutils.command`` package to install your commands;
``setuptools`` automatically adds a wrapper to the distutils to search for
entry points in the active distributions on ``sys.path``.  In fact, this is
how setuptools' own commands are installed: the setuptools project's setup
script defines entry points for them!

Adding ``setup()`` Arguments
----------------------------

.. warning:: Adding arguments to setup is discouraged as such arguments
   are only supported through imperative execution and not supported through
   declarative config.

Sometimes, your commands may need additional arguments to the ``setup()``
call.  You can enable this by defining entry points in the
``distutils.setup_keywords`` group.  For example, if you wanted a ``setup()``
argument called ``bar_baz``, you might add something like this to your
distutils extension project's setup script::

    setup(
        # ...
        entry_points={
            "distutils.commands": [
                "foo = mypackage.some_module:foo",
            ],
            "distutils.setup_keywords": [
                "bar_baz = mypackage.some_module:validate_bar_baz",
            ],
        },
    )

The idea here is that the entry point defines a function that will be called
to validate the ``setup()`` argument, if it's supplied.  The ``Distribution``
object will have the initial value of the attribute set to ``None``, and the
validation function will only be called if the ``setup()`` call sets it to
a non-None value.  Here's an example validation function::

    def assert_bool(dist, attr, value):
        """Verify that value is True, False, 0, or 1"""
        if bool(value) != value:
            raise DistutilsSetupError(
                "%r must be a boolean value (got %r)" % (attr,value)
            )

Your function should accept three arguments: the ``Distribution`` object,
the attribute name, and the attribute value.  It should raise a
``DistutilsSetupError`` (from the ``distutils.errors`` module) if the argument
is invalid.  Remember, your function will only be called with non-None values,
and the default value of arguments defined this way is always None.  So, your
commands should always be prepared for the possibility that the attribute will
be ``None`` when they access it later.

If more than one active distribution defines an entry point for the same
``setup()`` argument, *all* of them will be called.  This allows multiple
distutils extensions to define a common argument, as long as they agree on
what values of that argument are valid.

Also note that as with commands, it is not necessary to subclass or monkeypatch
the distutils ``Distribution`` class in order to add your arguments; it is
sufficient to define the entry points in your extension, as long as any setup
script using your extension lists your project in its ``setup_requires``
argument.


Customizing Distribution Options
--------------------------------

Plugins may wish to extend or alter the options on a Distribution object to
suit the purposes of that project. For example, a tool that infers the
``Distribution.version`` from SCM-metadata may need to hook into the
option finalization. To enable this feature, Setuptools offers an entry
point "setuptools.finalize_distribution_options". That entry point must
be a callable taking one argument (the Distribution instance).

If the callable has an ``.order`` property, that value will be used to
determine the order in which the hook is called. Lower numbers are called
first and the default is zero (0).

Plugins may read, alter, and set properties on the distribution, but each
plugin is encouraged to load the configuration/settings for their behavior
independently.


.. _Adding new EGG-INFO Files:

Adding new EGG-INFO Files
-------------------------

Some extensible applications or frameworks may want to allow third parties to
develop plugins with application or framework-specific metadata included in
the plugins' EGG-INFO directory, for easy access via the ``pkg_resources``
metadata API.  The easiest way to allow this is to create a distutils extension
to be used from the plugin projects' setup scripts (via ``setup_requires``)
that defines a new setup keyword, and then uses that data to write an EGG-INFO
file when the ``egg_info`` command is run.

The ``egg_info`` command looks for extension points in an ``egg_info.writers``
group, and calls them to write the files.  Here's a simple example of a
distutils extension defining a setup argument ``foo_bar``, which is a list of
lines that will be written to ``foo_bar.txt`` in the EGG-INFO directory of any
project that uses the argument::

    setup(
        # ...
        entry_points={
            "distutils.setup_keywords": [
                "foo_bar = setuptools.dist:assert_string_list",
            ],
            "egg_info.writers": [
                "foo_bar.txt = setuptools.command.egg_info:write_arg",
            ],
        },
    )

This simple example makes use of two utility functions defined by setuptools
for its own use: a routine to validate that a setup keyword is a sequence of
strings, and another one that looks up a setup argument and writes it to
a file.  Here's what the writer utility looks like::

    def write_arg(cmd, basename, filename):
        argname = os.path.splitext(basename)[0]
        value = getattr(cmd.distribution, argname, None)
        if value is not None:
            value = "\n".join(value) + "\n"
        cmd.write_or_delete_file(argname, filename, value)

As you can see, ``egg_info.writers`` entry points must be a function taking
three arguments: a ``egg_info`` command instance, the basename of the file to
write (e.g. ``foo_bar.txt``), and the actual full filename that should be
written to.

In general, writer functions should honor the command object's ``dry_run``
setting when writing files, and use the ``distutils.log`` object to do any
console output.  The easiest way to conform to this requirement is to use
the ``cmd`` object's ``write_file()``, ``delete_file()``, and
``write_or_delete_file()`` methods exclusively for your file operations.  See
those methods' docstrings for more details.


.. _Adding Support for Revision Control Systems:

Adding Support for Revision Control Systems
-------------------------------------------------

If the files you want to include in the source distribution are tracked using
Git, Mercurial or SVN, you can use the following packages to achieve that:

- Git and Mercurial: `setuptools_scm <https://pypi.org/project/setuptools_scm/>`_
- SVN: `setuptools_svn <https://pypi.org/project/setuptools_svn/>`_

If you would like to create a plugin for ``setuptools`` to find files tracked
by another revision control system, you can do so by adding an entry point to
the ``setuptools.file_finders`` group.  The entry point should be a function
accepting a single directory name, and should yield all the filenames within
that directory (and any subdirectories thereof) that are under revision
control.

For example, if you were going to create a plugin for a revision control system
called "foobar", you would write a function something like this:

.. code-block:: python

    def find_files_for_foobar(dirname):
        # loop to yield paths that start with `dirname`

And you would register it in a setup script using something like this::

    entry_points={
        "setuptools.file_finders": [
            "foobar = my_foobar_module:find_files_for_foobar",
        ]
    }

Then, anyone who wants to use your plugin can simply install it, and their
local setuptools installation will be able to find the necessary files.

It is not necessary to distribute source control plugins with projects that
simply use the other source control system, or to specify the plugins in
``setup_requires``.  When you create a source distribution with the ``sdist``
command, setuptools automatically records what files were found in the
``SOURCES.txt`` file.  That way, recipients of source distributions don't need
to have revision control at all.  However, if someone is working on a package
by checking out with that system, they will need the same plugin(s) that the
original author is using.

A few important points for writing revision control file finders:

* Your finder function MUST return relative paths, created by appending to the
  passed-in directory name.  Absolute paths are NOT allowed, nor are relative
  paths that reference a parent directory of the passed-in directory.

* Your finder function MUST accept an empty string as the directory name,
  meaning the current directory.  You MUST NOT convert this to a dot; just
  yield relative paths.  So, yielding a subdirectory named ``some/dir`` under
  the current directory should NOT be rendered as ``./some/dir`` or
  ``/somewhere/some/dir``, but *always* as simply ``some/dir``

* Your finder function SHOULD NOT raise any errors, and SHOULD deal gracefully
  with the absence of needed programs (i.e., ones belonging to the revision
  control system itself.  It *may*, however, use ``distutils.log.warn()`` to
  inform the user of the missing program(s).
