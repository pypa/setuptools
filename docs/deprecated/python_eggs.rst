=====================================
The Internal Structure of Python Eggs
=====================================

STOP! This is not the first document you should read!



----------------------
Eggs and their Formats
----------------------

A "Python egg" is a logical structure embodying the release of a
specific version of a Python project, comprising its code, resources,
and metadata. There are multiple formats that can be used to physically
encode a Python egg, and others can be developed. However, a key
principle of Python eggs is that they should be discoverable and
importable. That is, it should be possible for a Python application to
easily and efficiently find out what eggs are present on a system, and
to ensure that the desired eggs' contents are importable.

There are two basic formats currently implemented for Python eggs:

1. ``.egg`` format: a directory or zipfile *containing* the project's
   code and resources, along with an ``EGG-INFO`` subdirectory that
   contains the project's metadata

2. ``.egg-info`` format: a file or directory placed *adjacent* to the
   project's code and resources, that directly contains the project's
   metadata.

Both formats can include arbitrary Python code and resources, including
static data files, package and non-package directories, Python
modules, C extension modules, and so on.  But each format is optimized
for different purposes.

The ``.egg`` format is well-suited to distribution and the easy
uninstallation or upgrades of code, since the project is essentially
self-contained within a single directory or file, unmingled with any
other projects' code or resources.  It also makes it possible to have
multiple versions of a project simultaneously installed, such that
individual programs can select the versions they wish to use.

The ``.egg-info`` format, on the other hand, was created to support
backward-compatibility, performance, and ease of installation for system
packaging tools that expect to install all projects' code and resources
to a single directory (e.g. ``site-packages``).  Placing the metadata
in that same directory simplifies the installation process, since it
isn't necessary to create ``.pth`` files or otherwise modify
``sys.path`` to include each installed egg.

Its disadvantage, however, is that it provides no support for clean
uninstallation or upgrades, and of course only a single version of a
project can be installed to a given directory. Thus, support from a
package management tool is required. (This is why setuptools' "install"
command refers to this type of egg installation as "single-version,
externally managed".)  Also, they lack sufficient data to allow them to
be copied from their installation source.  easy_install can "ship" an
application by copying ``.egg`` files or directories to a target
location, but it cannot do this for ``.egg-info`` installs, because
there is no way to tell what code and resources belong to a particular
egg -- there may be several eggs "scrambled" together in a single
installation location, and the ``.egg-info`` format does not currently
include a way to list the files that were installed.  (This may change
in a future version.)


Code and Resources
==================

The layout of the code and resources is dictated by Python's normal
import layout, relative to the egg's "base location".

For the ``.egg`` format, the base location is the ``.egg`` itself. That
is, adding the ``.egg`` filename or directory name to ``sys.path``
makes its contents importable.

For the ``.egg-info`` format, however, the base location is the
directory that *contains* the ``.egg-info``, and thus it is the
directory that must be added to ``sys.path`` to make the egg importable.
(Note that this means that the "normal" installation of a package to a
``sys.path`` directory is sufficient to make it an "egg" if it has an
``.egg-info`` file or directory installed alongside of it.)


Project Metadata
=================

If eggs contained only code and resources, there would of course be
no difference between them and any other directory or zip file on
``sys.path``.  Thus, metadata must also be included, using a metadata
file or directory.

For the ``.egg`` format, the metadata is placed in an ``EGG-INFO``
subdirectory, directly within the ``.egg`` file or directory.  For the
``.egg-info`` format, metadata is stored directly within the
``.egg-info`` directory itself.

The minimum project metadata that all eggs must have is a standard
Python ``PKG-INFO`` file, named ``PKG-INFO`` and placed within the
metadata directory appropriate to the format.  Because it's possible for
this to be the only metadata file included, ``.egg-info`` format eggs
are not required to be a directory; they can just be a ``.egg-info``
file that directly contains the ``PKG-INFO`` metadata.  This eliminates
the need to create a directory just to store one file.  This option is
*not* available for ``.egg`` formats, since setuptools always includes
other metadata.  (In fact, setuptools itself never generates
``.egg-info`` files, either; the support for using files was added so
that the requirement could easily be satisfied by other tools, such
as distutils).

In addition to the ``PKG-INFO`` file, an egg's metadata directory may
also include files and directories representing various forms of
optional standard metadata (see the section on `Standard Metadata`_,
below) or user-defined metadata required by the project.  For example,
some projects may define a metadata format to describe their application
plugins, and metadata in this format would then be included by plugin
creators in their projects' metadata directories.


Filename-Embedded Metadata
==========================

To allow introspection of installed projects and runtime resolution of
inter-project dependencies, a certain amount of information is embedded
in egg filenames.  At a minimum, this includes the project name, and
ideally will also include the project version number.  Optionally, it
can also include the target Python version and required runtime
platform if platform-specific C code is included.  The syntax of an
egg filename is as follows::

    name ["-" version ["-py" pyver ["-" required_platform]]] "." ext

The "name" and "version" should be escaped using ``pkg_resources`` functions
``safe_name()`` and ``safe_version()`` respectively then using
``to_filename()``. Note that the escaping is irreversible and the original
name can only be retrieved from the distribution metadata. For a detailed
description of these transformations, please see the "Parsing Utilities"
section of the ``pkg_resources`` manual.

The "pyver" string is the Python major version, as found in the first
3 characters of ``sys.version``.  "required_platform" is essentially
a distutils ``get_platform()`` string, but with enhancements to properly
distinguish Mac OS versions.  (See the ``get_build_platform()``
documentation in the "Platform Utilities" section of the
``pkg_resources`` manual for more details.)

Finally, the "ext" is either ``.egg`` or ``.egg-info``, as appropriate
for the egg's format.

Normally, an egg's filename should include at least the project name and
version, as this allows the runtime system to find desired project
versions without having to read the egg's PKG-INFO to determine its
version number.

Setuptools, however, only includes the version number in the filename
when an ``.egg`` file is built using the ``bdist_egg`` command, or when
an ``.egg-info`` directory is being installed by the
``install_egg_info`` command. When generating metadata for use with the
original source tree, it only includes the project name, so that the
directory will not have to be renamed each time the project's version
changes.

This is especially important when version numbers change frequently, and
the source metadata directory is kept under version control with the
rest of the project.  (As would be the case when the project's source
includes project-defined metadata that is not generated from by
setuptools from data in the setup script.)


Egg Links
=========

In addition to the ``.egg`` and ``.egg-info`` formats, there is a third
egg-related extension that you may encounter on occasion: ``.egg-link``
files.

These files are not eggs, strictly speaking. They simply provide a way
to reference an egg that is not physically installed in the desired
location. They exist primarily as a cross-platform alternative to
symbolic links, to support "installing" code that is being developed in
a different location than the desired installation location. For
example, if a user is developing an application plugin in their home
directory, but the plugin needs to be "installed" in an application
plugin directory, running "setup.py develop -md /path/to/app/plugins"
will install an ``.egg-link`` file in ``/path/to/app/plugins``, that
tells the egg runtime system where to find the actual egg (the user's
project source directory and its ``.egg-info`` subdirectory).

``.egg-link`` files are named following the format for ``.egg`` and
``.egg-info`` names, but only the project name is included; no version,
Python version, or platform information is included.  When the runtime
searches for available eggs, ``.egg-link`` files are opened and the
actual egg file/directory name is read from them.

Note: Due to `pypa/setuptools#4167
<https://github.com/pypa/setuptools/issues/4167>`_, the name in the egg-link
filename does not match the filename components used in similar files, but
instead presents with dash separators instead of underscore separators. For
compatibility with pip prior to version 24.0, these dash separators are
retained. In a future release, pip 24 or later will be required and the
underscore separators will be used.

Each ``.egg-link`` file should contain a single file or directory name,
with no newlines.  This filename should be the base location of one or
more eggs.  That is, the name must either end in ``.egg``, or else it
should be the parent directory of one or more ``.egg-info`` format eggs.

As of setuptools 0.6c6, the path may be specified as a platform-independent
(i.e. ``/``-separated) relative path from the directory containing the
``.egg-link`` file, and a second line may appear in the file, specifying a
platform-independent relative path from the egg's base directory to its
setup script directory.  This allows installation tools such as EasyInstall
to find the project's setup directory and build eggs or perform other setup
commands on it.


-----------------
Standard Metadata
-----------------

In addition to the minimum required ``PKG-INFO`` metadata, projects can
include a variety of standard metadata files or directories, as
described below.  Except as otherwise noted, these files and directories
are automatically generated by setuptools, based on information supplied
in the setup script or through analysis of the project's code and
resources.

Most of these files and directories are generated via "egg-info
writers" during execution of the setuptools ``egg_info`` command, and
are listed in the ``egg_info.writers`` entry point group defined by
setuptools' own ``setup.py`` file.

Project authors can register their own metadata writers as entry points
in this group (as described in the setuptools manual under "Adding new
EGG-INFO Files") to cause setuptools to generate project-specific
metadata files or directories during execution of the ``egg_info``
command.  It is up to project authors to document these new metadata
formats, if they create any.


``.txt`` File Formats
=====================

Files described in this section that have ``.txt`` extensions have a
simple lexical format consisting of a sequence of text lines, each line
terminated by a linefeed character (regardless of platform).  Leading
and trailing whitespace on each line is ignored, as are blank lines and
lines whose first nonblank character is a ``#`` (comment symbol).  (This
is the parsing format defined by the ``yield_lines()`` function of
the ``pkg_resources`` module.)

All ``.txt`` files defined by this section follow this format, but some
are also "sectioned" files, meaning that their contents are divided into
sections, using square-bracketed section headers akin to Windows
``.ini`` format.  Note that this does *not* imply that the lines within
the sections follow an ``.ini`` format, however.  Please see an
individual metadata file's documentation for a description of what the
lines and section names mean in that particular file.

Sectioned files can be parsed using the ``split_sections()`` function;
see the "Parsing Utilities" section of the ``pkg_resources`` manual for
for details.


Dependency Metadata
===================


``requires.txt``
----------------

This is a "sectioned" text file.  Each section is a sequence of
"requirements", as parsed by the ``parse_requirements()`` function;
please see the ``pkg_resources`` manual for the complete requirement
parsing syntax.

The first, unnamed section (i.e., before the first section header) in
this file is the project's core requirements, which must be installed
for the project to function.  (Specified using the ``install_requires``
keyword to ``setup()``).

The remaining (named) sections describe the project's "extra"
requirements, as specified using the ``extras_require`` keyword to
``setup()``.  The section name is the name of the optional feature, and
the section body lists that feature's dependencies.

Note that it is not normally necessary to inspect this file directly;
``pkg_resources.Distribution`` objects have a ``requires()`` method
that can be used to obtain ``Requirement`` objects describing the
project's core and optional dependencies.


``setup_requires.txt``
----------------------

Much like ``requires.txt`` except represents the requirements
specified by the ``setup_requires`` parameter to the Distribution.


``dependency_links.txt``
------------------------

A list of dependency URLs, one per line, as specified using the
``dependency_links`` keyword to ``setup()``.  These may be direct
download URLs, or the URLs of web pages containing direct download
links. Please see the setuptools manual for more information on
specifying this option.


``depends.txt`` -- Obsolete, do not create!
-------------------------------------------

This file follows an identical format to ``requires.txt``, but is
obsolete and should not be used.  The earliest versions of setuptools
required users to manually create and maintain this file, so the runtime
still supports reading it, if it exists.  The new filename was created
so that it could be automatically generated from ``setup()`` information
without overwriting an existing hand-created ``depends.txt``, if one
was already present in the project's source ``.egg-info`` directory.


``namespace_packages.txt`` -- Namespace Package Metadata
========================================================

A list of namespace package names, one per line, as supplied to the
``namespace_packages`` keyword to ``setup()``.  Please see the manuals
for setuptools and ``pkg_resources`` for more information about
namespace packages.


``entry_points.txt`` -- "Entry Point"/Plugin Metadata
=====================================================

This is a "sectioned" text file, whose contents encode the
``entry_points`` keyword supplied to ``setup()``.  All sections are
named, as the section names specify the entry point groups in which the
corresponding section's entry points are registered.

Each section is a sequence of "entry point" lines, each parseable using
the ``EntryPoint.parse`` classmethod; please see the ``pkg_resources``
manual for the complete entry point parsing syntax.

Note that it is not necessary to parse this file directly; the
``pkg_resources`` module provides a variety of APIs to locate and load
entry points automatically.  Please see the setuptools and
``pkg_resources`` manuals for details on the nature and uses of entry
points.


The ``scripts`` Subdirectory
============================

This directory is currently only created for ``.egg`` files built by
the setuptools ``bdist_egg`` command.  It will contain copies of all
of the project's "traditional" scripts (i.e., those specified using the
``scripts`` keyword to ``setup()``).  This is so that they can be
reconstituted when an ``.egg`` file is installed.

The scripts are placed here using the distutils' standard
``install_scripts`` command, so any ``#!`` lines reflect the Python
installation where the egg was built.  But instead of copying the
scripts to the local script installation directory, EasyInstall writes
short wrapper scripts that invoke the original scripts from inside the
egg, after ensuring that sys.path includes the egg and any eggs it
depends on.  For more about `script wrappers`_, see the section below on
`Installation and Path Management Issues`_.


Zip Support Metadata
====================


``native_libs.txt``
-------------------

A list of C extensions and other dynamic link libraries contained in
the egg, one per line.  Paths are ``/``-separated and relative to the
egg's base location.

This file is generated as part of ``bdist_egg`` processing, and as such
only appears in ``.egg`` files (and ``.egg`` directories created by
unpacking them).  It is used to ensure that all libraries are extracted
from a zipped egg at the same time, in case there is any direct linkage
between them.  Please see the `Zip File Issues`_ section below for more
information on library and resource extraction from ``.egg`` files.


``eager_resources.txt``
-----------------------

A list of resource files and/or directories, one per line, as specified
via the ``eager_resources`` keyword to ``setup()``.  Paths are
``/``-separated and relative to the egg's base location.

Resource files or directories listed here will be extracted
simultaneously, if any of the named resources are extracted, or if any
native libraries listed in ``native_libs.txt`` are extracted.  Please
see the setuptools manual for details on what this feature is used for
and how it works, as well as the `Zip File Issues`_ section below.


``zip-safe`` and ``not-zip-safe``
---------------------------------

These are zero-length files, and either one or the other should exist.
If ``zip-safe`` exists, it means that the project will work properly
when installed as an ``.egg`` zipfile, and conversely the existence of
``not-zip-safe`` means the project should not be installed as an
``.egg`` file.  The ``zip_safe`` option to setuptools' ``setup()``
determines which file will be written. If the option isn't provided,
setuptools attempts to make its own assessment of whether the package
can work, based on code and content analysis.

If neither file is present at installation time, EasyInstall defaults
to assuming that the project should be unzipped.  (Command-line options
to EasyInstall, however, take precedence even over an existing
``zip-safe`` or ``not-zip-safe`` file.)

Note that these flag files appear only in ``.egg`` files generated by
``bdist_egg``, and in ``.egg`` directories created by unpacking such an
``.egg`` file.



``top_level.txt`` -- Conflict Management Metadata
=================================================

This file is a list of the top-level module or package names provided
by the project, one Python identifier per line.

Subpackages are not included; a project containing both a ``foo.bar``
and a ``foo.baz`` would include only one line, ``foo``, in its
``top_level.txt``.

This data is used by ``pkg_resources`` at runtime to issue a warning if
an egg is added to ``sys.path`` when its contained packages may have
already been imported.

(It was also once used to detect conflicts with non-egg packages at
installation time, but in more recent versions, setuptools installs eggs
in such a way that they always override non-egg packages, thus
preventing a problem from arising.)


``SOURCES.txt`` -- Source Files Manifest
========================================

This file is roughly equivalent to the distutils' ``MANIFEST`` file.
The differences are as follows:

* The filenames always use ``/`` as a path separator, which must be
  converted back to a platform-specific path whenever they are read.

* The file is automatically generated by setuptools whenever the
  ``egg_info`` or ``sdist`` commands are run, and it is *not*
  user-editable.

Although this metadata is included with distributed eggs, it is not
actually used at runtime for any purpose.  Its function is to ensure
that setuptools-built *source* distributions can correctly discover
what files are part of the project's source, even if the list had been
generated using revision control metadata on the original author's
system.

In other words, ``SOURCES.txt`` has little or no runtime value for being
included in distributed eggs, and it is possible that future versions of
the ``bdist_egg`` and ``install_egg_info`` commands will strip it before
installation or distribution.  Therefore, do not rely on its being
available outside of an original source directory or source
distribution.


------------------------------
Other Technical Considerations
------------------------------


Zip File Issues
===============

Although zip files resemble directories, they are not fully
substitutable for them.  Most platforms do not support loading dynamic
link libraries contained in zipfiles, so it is not possible to directly
import C extensions from ``.egg`` zipfiles.  Similarly, there are many
existing libraries -- whether in Python or C -- that require actual
operating system filenames, and do not work with arbitrary "file-like"
objects or in-memory strings, and thus cannot operate directly on the
contents of zip files.

To address these issues, the ``pkg_resources`` module provides a
"resource API" to support obtaining either the contents of a resource,
or a true operating system filename for the resource.  If the egg
containing the resource is a directory, the resource's real filename
is simply returned.  However, if the egg is a zipfile, then the
resource is first extracted to a cache directory, and the filename
within the cache is returned.

The cache directory is determined by the ``pkg_resources`` API; please
see the ``set_cache_path()`` and ``get_default_cache()`` documentation
for details.


The Extraction Process
----------------------

Resources are extracted to a cache subdirectory whose name is based
on the enclosing ``.egg`` filename and the path to the resource.  If
there is already a file of the correct name, size, and timestamp, its
filename is returned to the requester.  Otherwise, the desired file is
extracted first to a temporary name generated using
``mkstemp(".$extract",target_dir)``, and then its timestamp is set to
match the one in the zip file, before renaming it to its final name.
(Some collision detection and resolution code is used to handle the
fact that Windows doesn't overwrite files when renaming.)

If a resource directory is requested, all of its contents are
recursively extracted in this fashion, to ensure that the directory
name can be used as if it were valid all along.

If the resource requested for extraction is listed in the
``native_libs.txt`` or ``eager_resources.txt`` metadata files, then
*all* resources listed in *either* file will be extracted before the
requested resource's filename is returned, thus ensuring that all
C extensions and data used by them will be simultaneously available.


Extension Import Wrappers
-------------------------

Since Python's built-in zip import feature does not support loading
C extension modules from zipfiles, the setuptools ``bdist_egg`` command
generates special import wrappers to make it work.

The wrappers are ``.py`` files (along with corresponding ``.pyc``
and/or ``.pyo`` files) that have the same module name as the
corresponding C extension.  These wrappers are located in the same
package directory (or top-level directory) within the zipfile, so that
say, ``foomodule.so`` will get a corresponding ``foo.py``, while
``bar/baz.pyd`` will get a corresponding ``bar/baz.py``.

These wrapper files contain a short stanza of Python code that asks
``pkg_resources`` for the filename of the corresponding C extension,
then reloads the module using the obtained filename.  This will cause
``pkg_resources`` to first ensure that all of the egg's C extensions
(and any accompanying "eager resources") are extracted to the cache
before attempting to link to the C library.

Note, by the way, that ``.egg`` directories will also contain these
wrapper files.  However, Python's default import priority is such that
C extensions take precedence over same-named Python modules, so the
import wrappers are ignored unless the egg is a zipfile.


Installation and Path Management Issues
=======================================

Python's initial setup of ``sys.path`` is very dependent on the Python
version and installation platform, as well as how Python was started
(i.e., script vs. ``-c`` vs. ``-m`` vs. interactive interpreter).
In fact, Python also provides only two relatively robust ways to affect
``sys.path`` outside of direct manipulation in code: the ``PYTHONPATH``
environment variable, and ``.pth`` files.

However, with no cross-platform way to safely and persistently change
environment variables, this leaves ``.pth`` files as EasyInstall's only
real option for persistent configuration of ``sys.path``.

But ``.pth`` files are rather strictly limited in what they are allowed
to do normally.  They add directories only to the *end* of ``sys.path``,
after any locally-installed ``site-packages`` directory, and they are
only processed *in* the ``site-packages`` directory to start with.

This is a double whammy for users who lack write access to that
directory, because they can't create a ``.pth`` file that Python will
read, and even if a sympathetic system administrator adds one for them
that calls ``site.addsitedir()`` to allow some other directory to
contain ``.pth`` files, they won't be able to install newer versions of
anything that's installed in the systemwide ``site-packages``, because
their paths will still be added *after* ``site-packages``.

So EasyInstall applies two workarounds to solve these problems.

The first is that EasyInstall leverages ``.pth`` files' "import" feature
to manipulate ``sys.path`` and ensure that anything EasyInstall adds
to a ``.pth`` file will always appear before both the standard library
and the local ``site-packages`` directories.  Thus, it is always
possible for a user who can write a Python-read ``.pth`` file to ensure
that their packages come first in their own environment.

Second, when installing to a ``PYTHONPATH`` directory (as opposed to
a "site" directory like ``site-packages``) EasyInstall will also install
a special version of the ``site`` module.  Because it's in a
``PYTHONPATH`` directory, this module will get control before the
standard library version of ``site`` does.  It will record the state of
``sys.path`` before invoking the "real" ``site`` module, and then
afterwards it processes any ``.pth`` files found in ``PYTHONPATH``
directories, including all the fixups needed to ensure that eggs always
appear before the standard library in sys.path, but are in a relative
order to one another that is defined by their ``PYTHONPATH`` and
``.pth``-prescribed sequence.

The net result of these changes is that ``sys.path`` order will be
as follows at runtime:

1. The ``sys.argv[0]`` directory, or an empty string if no script
   is being executed.

2. All eggs installed by EasyInstall in any ``.pth`` file in each
   ``PYTHONPATH`` directory, in order first by ``PYTHONPATH`` order,
   then normal ``.pth`` processing order (which is to say alphabetical
   by ``.pth`` filename, then by the order of listing within each
   ``.pth`` file).

3. All eggs installed by EasyInstall in any ``.pth`` file in each "site"
   directory (such as ``site-packages``), following the same ordering
   rules as for the ones on ``PYTHONPATH``.

4. The ``PYTHONPATH`` directories themselves, in their original order

5. Any paths from ``.pth`` files found on ``PYTHONPATH`` that were *not*
   eggs installed by EasyInstall, again following the same relative
   ordering rules.

6. The standard library and "site" directories, along with the contents
   of any ``.pth`` files found in the "site" directories.

Notice that sections 1, 4, and 6 comprise the "normal" Python setup for
``sys.path``.  Sections 2 and 3 are inserted to support eggs, and
section 5 emulates what the "normal" semantics of ``.pth`` files on
``PYTHONPATH`` would be if Python natively supported them.

For further discussion of the tradeoffs that went into this design, as
well as notes on the actual magic inserted into ``.pth`` files to make
them do these things, please see also the following messages to the
distutils-SIG mailing list:

* http://mail.python.org/pipermail/distutils-sig/2006-February/006026.html
* http://mail.python.org/pipermail/distutils-sig/2006-March/006123.html


Script Wrappers
---------------

EasyInstall never directly installs a project's original scripts to
a script installation directory.  Instead, it writes short wrapper
scripts that first ensure that the project's dependencies are active
on sys.path, before invoking the original script.  These wrappers
have a #! line that points to the version of Python that was used to
install them, and their second line is always a comment that indicates
the type of script wrapper, the project version required for the script
to run, and information identifying the script to be invoked.

The format of this marker line is::

    "# EASY-INSTALL-" script_type ": " tuple_of_strings "\n"

The ``script_type`` is one of ``SCRIPT``, ``DEV-SCRIPT``, or
``ENTRY-SCRIPT``.  The ``tuple_of_strings`` is a comma-separated
sequence of Python string constants.  For ``SCRIPT`` and ``DEV-SCRIPT``
wrappers, there are two strings: the project version requirement, and
the script name (as a filename within the ``scripts`` metadata
directory).  For ``ENTRY-SCRIPT`` wrappers, there are three:
the project version requirement, the entry point group name, and the
entry point name.  (See the "Automatic Script Creation" section in the
setuptools manual for more information about entry point scripts.)

In each case, the project version requirement string will be a string
parseable with the ``pkg_resources`` modules' ``Requirement.parse()``
classmethod.  The only difference between a ``SCRIPT`` wrapper and a
``DEV-SCRIPT`` is that a ``DEV-SCRIPT`` actually executes the original
source script in the project's source tree, and is created when the
"setup.py develop" command is run.  A ``SCRIPT`` wrapper, on the other
hand, uses the "installed" script written to the ``EGG-INFO/scripts``
subdirectory of the corresponding ``.egg`` zipfile or directory.
(``.egg-info`` eggs do not have script wrappers associated with them,
except in the "setup.py develop" case.)

The purpose of including the marker line in generated script wrappers is
to facilitate introspection of installed scripts, and their relationship
to installed eggs.  For example, an uninstallation tool could use this
data to identify what scripts can safely be removed, and/or identify
what scripts would stop working if a particular egg is uninstalled.
