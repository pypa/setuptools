===============================
Running ``setuptools`` commands
===============================

Historically, ``setuptools`` allowed running commands via a ``setup.py`` script
at the root of a Python project, as indicated in the examples below::

    python setup.py --help
    python setup.py --help-commands
    python setup.py --version
    python setup.py sdist
    python setup.py bdist_wheel

You could also run commands in other circumstances:

* ``setuptools`` projects without ``setup.py`` (e.g., ``setup.cfg``-only)::

   python -c "from setuptools import setup; setup()" --help

* ``distutils`` projects (with a ``setup.py`` importing ``distutils``)::

   python -c "import setuptools; with open('setup.py') as f: exec(compile(f.read(), 'setup.py', 'exec'))" develop

That is, you can simply list the normal setup commands and options following the quoted part.

.. warning::
   While it is perfectly fine that users write ``setup.py`` files to configure
   a package build (e.g. to specify binary extensions or customize commands),
   on recent versions of ``setuptools``, running ``python setup.py`` directly
   as a script is considered **deprecated**. This also means that users should
   avoid running commands directly via ``python setup.py <command>``.

   If you want to create :term:`sdist <Source Distribution (or "sdist")>` or :term:`wheel`
   distributions the recommendation is to use the command line tool provided by :pypi:`build`::

       pip install build  # needs to be installed first

       python -m build  # builds both sdist and wheel
       python -m build --sdist
       python -m build --wheel

   Build will automatically download ``setuptools`` and build the package in an
   isolated environment. You can also specify specific versions of
   ``setuptools``, by setting the :doc:`build requirements in pyproject.toml
   </build_meta>`.

   If you want to install a package, you can use :pypi:`pip` or :pypi:`installer`::

      pip install /path/to/wheel/file.whl
      pip install /path/to/sdist/file.tar.gz
      pip install .  # replacement for python setup.py install
      pip install --editable .  # replacement for python setup.py develop

      pip install installer  # needs to be installed first
      python -m installer /path/to/wheel/file.whl

-----------------
Command Reference
-----------------

.. _alias:

``alias`` - Define shortcuts for commonly used commands
=======================================================

Sometimes, you need to use the same commands over and over, but you can't
necessarily set them as defaults.  For example, if you produce both development
snapshot releases and "stable" releases of a project, you may want to put
the distributions in different places, or use different ``egg_info`` tagging
options, etc.  In these cases, it doesn't make sense to set the options in
a distutils configuration file, because the values of the options changed based
on what you're trying to do.

Setuptools therefore allows you to define "aliases" - shortcut names for
an arbitrary string of commands and options, using ``setup.py alias aliasname
expansion``, where aliasname is the name of the new alias, and the remainder of
the command line supplies its expansion.  For example, this command defines
a sitewide alias called "daily", that sets various ``egg_info`` tagging
options::

    setup.py alias --global-config daily egg_info --tag-build=development

Once the alias is defined, it can then be used with other setup commands,
e.g.::

    setup.py daily bdist_egg        # generate a daily-build .egg file
    setup.py daily sdist            # generate a daily-build source distro
    setup.py daily sdist bdist_egg  # generate both

The above commands are interpreted as if the word ``daily`` were replaced with
``egg_info --tag-build=development``.

Note that setuptools will expand each alias *at most once* in a given command
line.  This serves two purposes.  First, if you accidentally create an alias
loop, it will have no effect; you'll instead get an error message about an
unknown command.  Second, it allows you to define an alias for a command, that
uses that command.  For example, this (project-local) alias::

    setup.py alias bdist_egg bdist_egg rotate -k1 -m.egg

redefines the ``bdist_egg`` command so that it always runs the ``rotate``
command afterwards to delete all but the newest egg file.  It doesn't loop
indefinitely on ``bdist_egg`` because the alias is only expanded once when
used.

You can remove a defined alias with the ``--remove`` (or ``-r``) option, e.g.::

    setup.py alias --global-config --remove daily

would delete the "daily" alias we defined above.

Aliases can be defined on a project-specific, per-user, or sitewide basis.  The
default is to define or remove a project-specific alias, but you can use any of
the `configuration file options`_ (listed under the `saveopts`_ command, below)
to determine which distutils configuration file an aliases will be added to
(or removed from).

Note that if you omit the "expansion" argument to the ``alias`` command,
you'll get output showing that alias' current definition (and what
configuration file it's defined in).  If you omit the alias name as well,
you'll get a listing of all current aliases along with their configuration
file locations.


``bdist_egg`` - Create a Python Egg for the project
===================================================

.. warning::
    **eggs** are deprecated in favor of wheels, and not supported by pip.

This command generates a Python Egg (``.egg`` file) for the project.  Python
Eggs are the preferred binary distribution format for EasyInstall, because they
are cross-platform (for "pure" packages), directly importable, and contain
project metadata including scripts and information about the project's
dependencies.  They can be simply downloaded and added to ``sys.path``
directly, or they can be placed in a directory on ``sys.path`` and then
automatically discovered by the egg runtime system.

This command runs the `egg_info`_ command (if it hasn't already run) to update
the project's metadata (``.egg-info``) directory.  If you have added any extra
metadata files to the ``.egg-info`` directory, those files will be included in
the new egg file's metadata directory, for use by the egg runtime system or by
any applications or frameworks that use that metadata.

You won't usually need to specify any special options for this command; just
use ``bdist_egg`` and you're done.  But there are a few options that may
be occasionally useful:

``--dist-dir=DIR, -d DIR``
    Set the directory where the ``.egg`` file will be placed.  If you don't
    supply this, then the ``--dist-dir`` setting of the ``bdist`` command
    will be used, which is usually a directory named ``dist`` in the project
    directory.

``--plat-name=PLATFORM, -p PLATFORM``
    Set the platform name string that will be embedded in the egg's filename
    (assuming the egg contains C extensions).  This can be used to override
    the distutils default platform name with something more meaningful.  Keep
    in mind, however, that the egg runtime system expects to see eggs with
    distutils platform names, so it may ignore or reject eggs with non-standard
    platform names.  Similarly, the EasyInstall program may ignore them when
    searching web pages for download links.  However, if you are
    cross-compiling or doing some other unusual things, you might find a use
    for this option.

``--exclude-source-files``
    Don't include any modules' ``.py`` files in the egg, just compiled Python,
    C, and data files.  (Note that this doesn't affect any ``.py`` files in the
    EGG-INFO directory or its subdirectories, since for example there may be
    scripts with a ``.py`` extension which must still be retained.)  We don't
    recommend that you use this option except for packages that are being
    bundled for proprietary end-user applications, or for "embedded" scenarios
    where space is at an absolute premium.  On the other hand, if your package
    is going to be installed and used in compressed form, you might as well
    exclude the source because Python's ``traceback`` module doesn't currently
    understand how to display zipped source code anyway, or how to deal with
    files that are in a different place from where their code was compiled.

There are also some options you will probably never need, but which are there
because they were copied from similar ``bdist`` commands used as an example for
creating this one.  They may be useful for testing and debugging, however,
which is why we kept them:

``--keep-temp, -k``
    Keep the contents of the ``--bdist-dir`` tree around after creating the
    ``.egg`` file.

``--bdist-dir=DIR, -b DIR``
    Set the temporary directory for creating the distribution.  The entire
    contents of this directory are zipped to create the ``.egg`` file, after
    running various installation commands to copy the package's modules, data,
    and extensions here.

``--skip-build``
    Skip doing any "build" commands; just go straight to the
    install-and-compress phases.


.. _develop:

``develop`` - Deploy the project source in "Development Mode"
=============================================================

This command allows you to deploy your project's source for use in one or more
"staging areas" where it will be available for importing.  This deployment is
done in such a way that changes to the project source are immediately available
in the staging area(s), without needing to run a build or install step after
each change.

The ``develop`` command works by creating an ``.egg-link`` file (named for the
project) in the given staging area.  If the staging area is Python's
``site-packages`` directory, it also updates an ``easy-install.pth`` file so
that the project is on ``sys.path`` by default for all programs run using that
Python installation.

The ``develop`` command also installs wrapper scripts in the staging area (or
a separate directory, as specified) that will ensure the project's dependencies
are available on ``sys.path`` before running the project's source scripts.
And, it ensures that any missing project dependencies are available in the
staging area, by downloading and installing them if necessary.

Last, but not least, the ``develop`` command invokes the ``build_ext -i``
command to ensure any C extensions in the project have been built and are
up-to-date, and the ``egg_info`` command to ensure the project's metadata is
updated (so that the runtime and wrappers know what the project's dependencies
are).  If you make any changes to the project's setup script or C extensions,
you should rerun the ``develop`` command against all relevant staging areas to
keep the project's scripts, metadata and extensions up-to-date.  Most other
kinds of changes to your project should not require any build operations or
rerunning ``develop``, but keep in mind that even minor changes to the setup
script (e.g. changing an entry point definition) require you to re-run the
``develop`` or ``test`` commands to keep the distribution updated.

Here are some of the options that the ``develop`` command accepts.  Note that
they affect the project's dependencies as well as the project itself, so if you
have dependencies that need to be installed and you use ``--exclude-scripts``
(for example), the dependencies' scripts will not be installed either!  For
this reason, you may want to use pip to install the project's dependencies
before using the ``develop`` command, if you need finer control over the
installation options for dependencies.

``--uninstall, -u``
    Un-deploy the current project.  You may use the ``--install-dir`` or ``-d``
    option to designate the staging area.  The created ``.egg-link`` file will
    be removed, if present and it is still pointing to the project directory.
    The project directory will be removed from ``easy-install.pth`` if the
    staging area is Python's ``site-packages`` directory.

    Note that this option currently does *not* uninstall script wrappers!  You
    must uninstall them yourself, or overwrite them by using pip to install a
    different version of the package.  You can also avoid installing script
    wrappers in the first place, if you use the ``--exclude-scripts`` (aka
    ``-x``) option when you run ``develop`` to deploy the project.

``--multi-version, -m``
    "Multi-version" mode. Specifying this option prevents ``develop`` from
    adding an ``easy-install.pth`` entry for the project(s) being deployed, and
    if an entry for any version of a project already exists, the entry will be
    removed upon successful deployment.  In multi-version mode, no specific
    version of the package is available for importing, unless you use
    ``pkg_resources.require()`` to put it on ``sys.path``, or you are running
    a wrapper script generated by ``setuptools``.  (In which case the wrapper
    script calls ``require()`` for you.)

    Note that if you install to a directory other than ``site-packages``,
    this option is automatically in effect, because ``.pth`` files can only be
    used in ``site-packages`` (at least in Python 2.3 and 2.4). So, if you use
    the ``--install-dir`` or ``-d`` option (or they are set via configuration
    file(s)) your project and its dependencies will be deployed in multi-
    version mode.

``--install-dir=DIR, -d DIR``
    Set the installation directory (staging area).  If this option is not
    directly specified on the command line or in a distutils configuration
    file, the distutils default installation location is used.  Normally, this
    will be the ``site-packages`` directory, but if you are using distutils
    configuration files, setting things like ``prefix`` or ``install_lib``,
    then those settings are taken into account when computing the default
    staging area.

``--script-dir=DIR, -s DIR``
    Set the script installation directory.  If you don't supply this option
    (via the command line or a configuration file), but you *have* supplied
    an ``--install-dir`` (via command line or config file), then this option
    defaults to the same directory, so that the scripts will be able to find
    their associated package installation.  Otherwise, this setting defaults
    to the location where the distutils would normally install scripts, taking
    any distutils configuration file settings into account.

``--exclude-scripts, -x``
    Don't deploy script wrappers.  This is useful if you don't want to disturb
    existing versions of the scripts in the staging area.

``--always-copy, -a``
    Copy all needed distributions to the staging area, even if they
    are already present in another directory on ``sys.path``.  By default, if
    a requirement can be met using a distribution that is already available in
    a directory on ``sys.path``, it will not be copied to the staging area.

``--egg-path=DIR``
    Force the generated ``.egg-link`` file to use a specified relative path
    to the source directory.  This can be useful in circumstances where your
    installation directory is being shared by code running under multiple
    platforms (e.g. Mac and Windows) which have different absolute locations
    for the code under development, but the same *relative* locations with
    respect to the installation directory.  If you use this option when
    installing, you must supply the same relative path when uninstalling.

In addition to the above options, the ``develop`` command also accepts all of
the same options accepted by ``easy_install``.  If you've configured any
``easy_install`` settings in your ``setup.cfg`` (or other distutils config
files), the ``develop`` command will use them as defaults, unless you override
them in a ``[develop]`` section or on the command line.


.. _egg_info:

``egg_info`` - Create egg metadata and set build tags
=====================================================

This command performs two operations: it updates a project's ``.egg-info``
metadata directory (used by the ``bdist_egg``, ``develop``, and ``test``
commands), and it allows you to temporarily change a project's version string,
to support "daily builds" or "snapshot" releases.  It is run automatically by
the ``sdist``, ``bdist_egg``, ``develop``, and ``test`` commands in order to
update the project's metadata, but you can also specify it explicitly in order
to temporarily change the project's version string while executing other
commands.  (It also generates the ``.egg-info/SOURCES.txt`` manifest file, which
is used when you are building source distributions.)

In addition to writing the core egg metadata defined by ``setuptools`` and
required by ``pkg_resources``, this command can be extended to write other
metadata files as well, by defining entry points in the ``egg_info.writers``
group.  See the section on :ref:`Adding new EGG-INFO Files` below for more details.
Note that using additional metadata writers may require you to include a
``setup_requires`` argument to ``setup()`` in order to ensure that the desired
writers are available on ``sys.path``.


Release Tagging Options
-----------------------

The following options can be used to modify the project's version string for
all remaining commands on the setup command line.  The options are processed
in the order shown, so if you use more than one, the requested tags will be
added in the following order:

``--tag-build=NAME, -b NAME``
    Append NAME to the project's version string.  Due to the way setuptools
    processes "pre-release" version suffixes beginning with the letters "a"
    through "e" (like "alpha", "beta", and "candidate"), you will usually want
    to use a tag like ".build" or ".dev", as this will cause the version number
    to be considered *lower* than the project's default version.  (If you
    want to make the version number *higher* than the default version, you can
    always leave off --tag-build and then use one or both of the following
    options.)

    If you have a default build tag set in your ``setup.cfg``, you can suppress
    it on the command line using ``-b ""`` or ``--tag-build=""`` as an argument
    to the ``egg_info`` command.

``--tag-date, -d``
    Add a date stamp of the form "-YYYYMMDD" (e.g. "-20050528") to the
    project's version number.

``--no-date, -D``
    Don't include a date stamp in the version number.  This option is included
    so you can override a default setting in ``setup.cfg``.


(Note: Because these options modify the version number used for source and
binary distributions of your project, you should first make sure that you know
how the resulting version numbers will be interpreted by automated tools
like pip.  See the section above on :ref:`Specifying Your Project's Version` for an
explanation of pre- and post-release tags, as well as tips on how to choose and
verify a versioning scheme for your project.)

For advanced uses, there is one other option that can be set, to change the
location of the project's ``.egg-info`` directory.  Commands that need to find
the project's source directory or metadata should get it from this setting:


Other ``egg_info`` Options
--------------------------

``--egg-base=SOURCEDIR, -e SOURCEDIR``
    Specify the directory that should contain the .egg-info directory.  This
    should normally be the root of your project's source tree (which is not
    necessarily the same as your project directory; some projects use a ``src``
    or ``lib`` subdirectory as the source root).  You should not normally need
    to specify this directory, as it is normally determined from the
    ``package_dir`` argument to the ``setup()`` function, if any.  If there is
    no ``package_dir`` set, this option defaults to the current directory.


``egg_info`` Examples
---------------------

Creating a dated "nightly build" snapshot egg::

    setup.py egg_info --tag-date --tag-build=DEV bdist_egg

Creating a release with no version tags, even if some default tags are
specified in ``setup.cfg``::

    setup.py egg_info -RDb "" sdist bdist_egg

(Notice that ``egg_info`` must always appear on the command line *before* any
commands that you want the version changes to apply to.)

.. _rotate:

``rotate`` - Delete outdated distribution files
===============================================

As you develop new versions of your project, your distribution (``dist``)
directory will gradually fill up with older source and/or binary distribution
files.  The ``rotate`` command lets you automatically clean these up, keeping
only the N most-recently modified files matching a given pattern.

``--match=PATTERNLIST, -m PATTERNLIST``
    Comma-separated list of glob patterns to match.  This option is *required*.
    The project name and ``-*`` is prepended to the supplied patterns, in order
    to match only distributions belonging to the current project (in case you
    have a shared distribution directory for multiple projects).  Typically,
    you will use a glob pattern like ``.zip`` or ``.egg`` to match files of
    the specified type.  Note that each supplied pattern is treated as a
    distinct group of files for purposes of selecting files to delete.

``--keep=COUNT, -k COUNT``
    Number of matching distributions to keep.  For each group of files
    identified by a pattern specified with the ``--match`` option, delete all
    but the COUNT most-recently-modified files in that group.  This option is
    *required*.

``--dist-dir=DIR, -d DIR``
    Directory where the distributions are.  This defaults to the value of the
    ``bdist`` command's ``--dist-dir`` option, which will usually be the
    project's ``dist`` subdirectory.

**Example 1**: Delete all .tar.gz files from the distribution directory, except
for the 3 most recently modified ones::

    setup.py rotate --match=.tar.gz --keep=3

**Example 2**: Delete all Python 2.3 or Python 2.4 eggs from the distribution
directory, except the most recently modified one for each Python version::

    setup.py rotate --match=-py2.3*.egg,-py2.4*.egg --keep=1


.. _saveopts:

``saveopts`` - Save used options to a configuration file
========================================================

Finding and editing ``distutils`` configuration files can be a pain, especially
since you also have to translate the configuration options from command-line
form to the proper configuration file format.  You can avoid these hassles by
using the ``saveopts`` command.  Just add it to the command line to save the
options you used.  For example, this command builds the project using
the ``mingw32`` C compiler, then saves the --compiler setting as the default
for future builds (even those run implicitly by the ``install`` command)::

    setup.py build --compiler=mingw32 saveopts

The ``saveopts`` command saves all options for every command specified on the
command line to the project's local ``setup.cfg`` file, unless you use one of
the `configuration file options`_ to change where the options are saved.  For
example, this command does the same as above, but saves the compiler setting
to the site-wide (global) distutils configuration::

    setup.py build --compiler=mingw32 saveopts -g

Note that it doesn't matter where you place the ``saveopts`` command on the
command line; it will still save all the options specified for all commands.
For example, this is another valid way to spell the last example::

    setup.py saveopts -g build --compiler=mingw32

Note, however, that all of the commands specified are always run, regardless of
where ``saveopts`` is placed on the command line.


Configuration File Options
--------------------------

Normally, settings such as options and aliases are saved to the project's
local ``setup.cfg`` file.  But you can override this and save them to the
global or per-user configuration files, or to a manually-specified filename.

``--global-config, -g``
    Save settings to the global ``distutils.cfg`` file inside the ``distutils``
    package directory.  You must have write access to that directory to use
    this option.  You also can't combine this option with ``-u`` or ``-f``.

``--user-config, -u``
    Save settings to the current user's ``~/.pydistutils.cfg`` (POSIX) or
    ``$HOME/pydistutils.cfg`` (Windows) file.  You can't combine this option
    with ``-g`` or ``-f``.

``--filename=FILENAME, -f FILENAME``
    Save settings to the specified configuration file to use.  You can't
    combine this option with ``-g`` or ``-u``.  Note that if you specify a
    non-standard filename, the ``distutils`` and ``setuptools`` will not
    use the file's contents.  This option is mainly included for use in
    testing.

These options are used by other ``setuptools`` commands that modify
configuration files, such as the `alias`_ and `setopt`_ commands.


.. _setopt:

``setopt`` - Set a distutils or setuptools option in a config file
==================================================================

This command is mainly for use by scripts, but it can also be used as a quick
and dirty way to change a distutils configuration option without having to
remember what file the options are in and then open an editor.

**Example 1**.  Set the default C compiler to ``mingw32`` (using long option
names)::

    setup.py setopt --command=build --option=compiler --set-value=mingw32

**Example 2**.  Remove any setting for the distutils default package
installation directory (short option names)::

    setup.py setopt -c install -o install_lib -r


Options for the ``setopt`` command:

``--command=COMMAND, -c COMMAND``
    Command to set the option for.  This option is required.

``--option=OPTION, -o OPTION``
    The name of the option to set.  This option is required.

``--set-value=VALUE, -s VALUE``
    The value to set the option to.  Not needed if ``-r`` or ``--remove`` is
    set.

``--remove, -r``
    Remove (unset) the option, instead of setting it.

In addition to the above options, you may use any of the `configuration file
options`_ (listed under the `saveopts`_ command, above) to determine which
distutils configuration file the option will be added to (or removed from).


.. _test:

``test`` - Build package and run a unittest suite
=================================================

.. warning::
    ``test`` is deprecated and will be removed in a future version. Users
    looking for a generic test entry point independent of test runner are
    encouraged to use `tox <https://tox.readthedocs.io>`_.

When doing test-driven development, or running automated builds that need
testing before they are deployed for downloading or use, it's often useful
to be able to run a project's unit tests without actually deploying the project
anywhere, even using the ``develop`` command.  The ``test`` command runs a
project's unit tests without actually deploying it, by temporarily putting the
project's source on ``sys.path``, after first running ``build_ext -i`` and
``egg_info`` to ensure that any C extensions and project metadata are
up-to-date.

To use this command, your project's tests must be wrapped in a ``unittest``
test suite by either a function, a ``TestCase`` class or method, or a module
or package containing ``TestCase`` classes.  If the named suite is a module,
and the module has an ``additional_tests()`` function, it is called and the
result (which must be a ``unittest.TestSuite``) is added to the tests to be
run.  If the named suite is a package, any submodules and subpackages are
recursively added to the overall test suite.  (Note: if your project specifies
a ``test_loader``, the rules for processing the chosen ``test_suite`` may
differ; see the :ref:`test_loader <test_loader>` documentation for more details.)

Note that many test systems including ``doctest`` support wrapping their
non-``unittest`` tests in ``TestSuite`` objects.  So, if you are using a test
package that does not support this, we suggest you encourage its developers to
implement test suite support, as this is a convenient and standard way to
aggregate a collection of tests to be run under a common test harness.

By default, tests will be run in the "verbose" mode of the ``unittest``
package's text test runner, but you can get the "quiet" mode (just dots) if
you supply the ``-q`` or ``--quiet`` option, either as a global option to
the setup script (e.g. ``setup.py -q test``) or as an option for the ``test``
command itself (e.g. ``setup.py test -q``).  There is one other option
available:

``--test-suite=NAME, -s NAME``
    Specify the test suite (or module, class, or method) to be run
    (e.g. ``some_module.test_suite``).  The default for this option can be
    set by giving a ``test_suite`` argument to the ``setup()`` function, e.g.::

        setup(
            # ...
            test_suite="my_package.tests.test_all"
        )

    If you did not set a ``test_suite`` in your ``setup()`` call, and do not
    provide a ``--test-suite`` option, an error will occur.

New in 41.5.0: Deprecated the test command.


.. _upload:

``upload`` - Upload source and/or egg distributions to PyPI
===========================================================

The ``upload`` command was deprecated in version 40.0 and removed in version
42.0. Use `twine <https://pypi.org/p/twine>`_ instead.

For  more information on the current best practices in uploading your packages
to PyPI, see the Python Packaging User Guide's "Packaging Python Projects"
tutorial specifically the section on `uploading the distribution archives
<https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives>`_.
