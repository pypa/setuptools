Tagging and "Daily Build" or "Snapshot" Releases
------------------------------------------------

When a set of related projects are under development, it may be important to
track finer-grained version increments than you would normally use for e.g.
"stable" releases.  While stable releases might be measured in dotted numbers
with alpha/beta/etc. status codes, development versions of a project often
need to be tracked by revision or build number or even build date.  This is
especially true when projects in development need to refer to one another, and
therefore may literally need an up-to-the-minute version of something!

To support these scenarios, ``setuptools`` allows you to "tag" your source and
egg distributions by adding one or more of the following to the project's
"official" version identifier:

* A manually-specified pre-release tag, such as "build" or "dev", or a
  manually-specified post-release tag, such as a build or revision number
  (``--tag-build=STRING, -bSTRING``)

* An 8-character representation of the build date (``--tag-date, -d``), as
  a postrelease tag

You can add these tags by adding ``egg_info`` and the desired options to
the command line ahead of the ``sdist`` or ``bdist`` commands that you want
to generate a daily build or snapshot for.  See the section below on the
:ref:`egg_info <egg_info>` command for more details.

(Also, before you release your project, be sure to see the section on
:ref:`Specifying Your Project's Version` for more information about how pre- and
post-release tags affect how version numbers are interpreted.  This is
important in order to make sure that dependency processing tools will know
which versions of your project are newer than others.)

Finally, if you are creating builds frequently, and either building them in a
downloadable location or are copying them to a distribution server, you should
probably also check out the :ref:`rotate <rotate>` command, which lets you automatically
delete all but the N most-recently-modified distributions matching a glob
pattern.  So, you can use a command line like::

    setup.py egg_info -rbDEV bdist_egg rotate -m.egg -k3

to build an egg whose version info includes "DEV-rNNNN" (where NNNN is the
most recent Subversion revision that affected the source tree), and then
delete any egg files from the distribution directory except for the three
that were built most recently.

If you have to manage automated builds for multiple packages, each with
different tagging and rotation policies, you may also want to check out the
:ref:`alias <alias>` command, which would let each package define an alias like ``daily``
that would perform the necessary tag, build, and rotate commands.  Then, a
simpler script or cron job could just run ``setup.py daily`` in each project
directory.  (And, you could also define sitewide or per-user default versions
of the ``daily`` alias, so that projects that didn't define their own would
use the appropriate defaults.)

Generating Source Distributions
-------------------------------

``setuptools`` enhances the distutils' default algorithm for source file
selection with pluggable endpoints for looking up files to include. If you are
using a revision control system, and your source distributions only need to
include files that you're tracking in revision control, use a corresponding
plugin instead of writing a ``MANIFEST.in`` file. See the section below on
:ref:`Adding Support for Revision Control Systems` for information on plugins.

If you need to include automatically generated files, or files that are kept in
an unsupported revision control system, you'll need to create a ``MANIFEST.in``
file to specify any files that the default file location algorithm doesn't
catch.  See the distutils documentation for more information on the format of
the ``MANIFEST.in`` file.

But, be sure to ignore any part of the distutils documentation that deals with
``MANIFEST`` or how it's generated from ``MANIFEST.in``; setuptools shields you
from these issues and doesn't work the same way in any case.  Unlike the
distutils, setuptools regenerates the source distribution manifest file
every time you build a source distribution, and it builds it inside the
project's ``.egg-info`` directory, out of the way of your main project
directory.  You therefore need not worry about whether it is up-to-date or not.

Indeed, because setuptools' approach to determining the contents of a source
distribution is so much simpler, its ``sdist`` command omits nearly all of
the options that the distutils' more complex ``sdist`` process requires.  For
all practical purposes, you'll probably use only the ``--formats`` option, if
you use any option at all.


Making "Official" (Non-Snapshot) Releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you make an official release, creating source or binary distributions,
you will need to override the tag settings from ``setup.cfg``, so that you
don't end up registering versions like ``foobar-0.7a1.dev-r34832``.  This is
easy to do if you are developing on the trunk and using tags or branches for
your releases - just make the change to ``setup.cfg`` after branching or
tagging the release, so the trunk will still produce development snapshots.

Alternately, if you are not branching for releases, you can override the
default version options on the command line, using something like::

    setup.py egg_info -Db "" sdist bdist_egg

The first part of this command (``egg_info -Db ""``) will override the
configured tag information, before creating source and binary eggs. Thus, these
commands will use the plain version from your ``setup.py``, without adding the
build designation string.

Of course, if you will be doing this a lot, you may wish to create a personal
alias for this operation, e.g.::

    setup.py alias -u release egg_info -Db ""

You can then use it like this::

    setup.py release sdist bdist_egg

Or of course you can create more elaborate aliases that do all of the above.
See the sections below on the :ref:`egg_info <egg_info>` and
:ref:`alias <alias>` commands for more ideas.

Distributing Extensions compiled with Cython
--------------------------------------------

``setuptools`` will detect at build time whether Cython is installed or not.
If Cython is not found ``setuptools`` will ignore pyx files.

To ensure Cython is available, include Cython in the build-requires section
of your pyproject.toml::

    [build-system]
    requires=[..., "cython"]

Built with pip 10 or later, that declaration is sufficient to include Cython
in the build. For broader compatibility, declare the dependency in your
setup-requires of setup.cfg::

    [options]
    setup_requires =
        ...
        cython

As long as Cython is present in the build environment, ``setuptools`` includes
transparent support for building Cython extensions, as
long as extensions are defined using ``setuptools.Extension``.

If you follow these rules, you can safely list ``.pyx`` files as the source
of your ``Extension`` objects in the setup script.  If it is, then ``setuptools``
will use it.

Of course, for this to work, your source distributions must include the C
code generated by Cython, as well as your original ``.pyx`` files.  This means
that you will probably want to include current ``.c`` files in your revision
control system, rebuilding them whenever you check changes in for the ``.pyx``
source files.  This will ensure that people tracking your project in a revision
control system will be able to build it even if they don't have Cython
installed, and that your source releases will be similarly usable with or
without Cython.


.. _Specifying Your Project's Version:

Specifying Your Project's Version
---------------------------------

Setuptools can work well with most versioning schemes. Over the years,
setuptools has tried to closely follow the 
`PEP 440 <https://www.python.org/dev/peps/pep-0440/>`_ scheme, but it
also supports legacy versions. There are, however, a
few special things to watch out for, in order to ensure that setuptools and
other tools can always tell what version of your package is newer than another
version.  Knowing these things will also help you correctly specify what
versions of other projects your project depends on.

A version consists of an alternating series of release numbers and pre-release
or post-release tags.  A release number is a series of digits punctuated by
dots, such as ``2.4`` or ``0.5``.  Each series of digits is treated
numerically, so releases ``2.1`` and ``2.1.0`` are different ways to spell the
same release number, denoting the first subrelease of release 2.  But  ``2.10``
is the *tenth* subrelease of release 2, and so is a different and newer release
from ``2.1`` or ``2.1.0``.  Leading zeros within a series of digits are also
ignored, so ``2.01`` is the same as ``2.1``, and different from ``2.0.1``.

Following a release number, you can have either a pre-release or post-release
tag.  Pre-release tags make a version be considered *older* than the version
they are appended to.  So, revision ``2.4`` is *newer* than revision ``2.4c1``,
which in turn is newer than ``2.4b1`` or ``2.4a1``.  Postrelease tags make
a version be considered *newer* than the version they are appended to.  So,
revisions like ``2.4-1`` are newer than ``2.4``, but *older*
than ``2.4.1`` (which has a higher release number).

In the case of legacy versions (for example, ``2.4pl1``), they are considered
older than non-legacy versions. Taking that in count, a revision ``2.4pl1``
is *older* than ``2.4``

A pre-release tag is a series of letters that are alphabetically before
"final".  Some examples of prerelease tags would include ``alpha``, ``beta``,
``a``, ``c``, ``dev``, and so on.  You do not have to place a dot or dash
before the prerelease tag if it's immediately after a number, but it's okay to
do so if you prefer.  Thus, ``2.4c1`` and ``2.4.c1`` and ``2.4-c1`` all
represent release candidate 1 of version ``2.4``, and are treated as identical
by setuptools.

In addition, there are three special prerelease tags that are treated as if
they were the letter ``c``: ``pre``, ``preview``, and ``rc``.  So, version
``2.4rc1``, ``2.4pre1`` and ``2.4preview1`` are all the exact same version as
``2.4c1``, and are treated as identical by setuptools.

A post-release tag is either a series of letters that are alphabetically
greater than or equal to "final", or a dash (``-``).  Post-release tags are
generally used to separate patch numbers, port numbers, build numbers, revision
numbers, or date stamps from the release number.  For example, the version
``2.4-r1263`` might denote Subversion revision 1263 of a post-release patch of
version ``2.4``.  Or you might use ``2.4-20051127`` to denote a date-stamped
post-release.

Notice that after each pre or post-release tag, you are free to place another
release number, followed again by more pre- or post-release tags.  For example,
``0.6a9.dev-r41475`` could denote Subversion revision 41475 of the in-
development version of the ninth alpha of release 0.6.  Notice that ``dev`` is
a pre-release tag, so this version is a *lower* version number than ``0.6a9``,
which would be the actual ninth alpha of release 0.6.  But the ``-r41475`` is
a post-release tag, so this version is *newer* than ``0.6a9.dev``.

For the most part, setuptools' interpretation of version numbers is intuitive,
but here are a few tips that will keep you out of trouble in the corner cases:

* Don't stick adjoining pre-release tags together without a dot or number
  between them.  Version ``1.9adev`` is the ``adev`` prerelease of ``1.9``,
  *not* a development pre-release of ``1.9a``.  Use ``.dev`` instead, as in
  ``1.9a.dev``, or separate the prerelease tags with a number, as in
  ``1.9a0dev``.  ``1.9a.dev``, ``1.9a0dev``, and even ``1.9.a.dev`` are
  identical versions from setuptools' point of view, so you can use whatever
  scheme you prefer.

* If you want to be certain that your chosen numbering scheme works the way
  you think it will, you can use the ``pkg_resources.parse_version()`` function
  to compare different version numbers::

    >>> from pkg_resources import parse_version
    >>> parse_version("1.9.a.dev") == parse_version("1.9a0dev")
    True
    >>> parse_version("2.1-rc2") < parse_version("2.1")
    True
    >>> parse_version("0.6a9dev-r41475") < parse_version("0.6a9")
    True

Once you've decided on a version numbering scheme for your project, you can
have setuptools automatically tag your in-development releases with various
pre- or post-release tags.  See the following sections for more details:

* `Tagging and "Daily Build" or "Snapshot" Releases`_
* The :ref:`egg_info <egg_info>` command
