.. _Specifying Your Project's Version:

Specifying Your Project's Version
=================================

Setuptools can work well with most versioning schemes. Over the years,
setuptools has tried to closely follow the :pep:`440` scheme, but it
also supports legacy versions. There are, however, a
few special things to watch out for, in order to ensure that setuptools and
other tools can always tell what version of your package is newer than another
version.  Knowing these things will also help you correctly specify what
versions of other projects your project depends on.

A version consists of an alternating series of release numbers and
`pre-release <https://peps.python.org/pep-0440/#pre-releases>`_
or `post-release <https://peps.python.org/pep-0440/#post-releases>`_ tags.  A
release number is a series of digits punctuated by
dots, such as ``2.4`` or ``0.5``.  Each series of digits is treated
numerically, so releases ``2.1`` and ``2.1.0`` are different ways to spell the
same release number, denoting the first subrelease of release 2.  But  ``2.10``
is the *tenth* subrelease of release 2, and so is a different and newer release
from ``2.1`` or ``2.1.0``.  Leading zeros within a series of digits are also
ignored, so ``2.01`` is the same as ``2.1``, and different from ``2.0.1``.

Following a release number, you can have either a pre-release or post-release
tag.  Pre-release tags make a version be considered *older* than the version
they are appended to.  So, revision ``2.4`` is *newer* than release candidate
``2.4rc1``, which in turn is newer than beta release ``2.4b1`` or
alpha release ``2.4a1``.  Postrelease tags make
a version be considered *newer* than the version they are appended to.  So,
revisions like ``2.4.post1`` are newer than ``2.4``, but *older*
than ``2.4.1`` (which has a higher release number).

In the case of legacy versions (for example, ``2.4pl1``), they are considered
older than non-legacy versions. Taking that in count, a revision ``2.4pl1``
is *older* than ``2.4``. Note that ``2.4pl1`` is not :pep:`440`-compliant.

A pre-release tag is a series of letters that are alphabetically before
"final".  Some examples of prerelease tags would include ``alpha``, ``beta``,
``a``, ``c``, ``dev``, and so on.  You do not have to place a dot or dash
before the prerelease tag if it's immediately after a number, but it's okay to
do so if you prefer.  Thus, ``2.4c1`` and ``2.4.c1`` and ``2.4-c1`` all
represent release candidate 1 of version ``2.4``, and are treated as identical
by setuptools. Note that only ``a``, ``b``, and ``rc`` are :pep:`440`-compliant
pre-release tags.

In addition, there are three special prerelease tags that are treated as if
they were ``rc``: ``c``, ``pre``, and ``preview``.  So, version
``2.4c1``, ``2.4pre1`` and ``2.4preview1`` are all the exact same version as
``2.4rc1``, and are treated as identical by setuptools.

A post-release tag is the string ``.post``, followed by a non-negative integer
value. Post-release tags are generally used to separate patch numbers, port
numbers, build numbers, revision numbers, or date stamps from the release
number.  For example, the version ``2.4.post1263`` might denote Subversion
revision 1263 of a post-release patch of version ``2.4``. Or you might use
``2.4.post20051127`` to denote a date-stamped post-release. Legacy post-release
tags could be either a series of letters that are alphabetically greater than or
equal to "final", or a dash (``-``) - for example ``2.4-r1263`` or
``2.4-20051127``.

Notice that after each legacy pre or post-release tag, you are free to place
another release number, followed again by more pre- or post-release tags.  For
example, ``0.6a9.dev41475`` could denote Subversion revision 41475 of the in-
development version of the ninth alpha of release 0.6.  Notice that ``dev`` is
a pre-release tag, so this version is a *lower* version number than ``0.6a9``,
which would be the actual ninth alpha of release 0.6.  But the ``41475`` is
a post-release tag, so this version is *newer* than ``0.6a9.dev``.

For the most part, setuptools' interpretation of version numbers is intuitive,
but here are a few tips that will keep you out of trouble in the corner cases:

* Don't stick adjoining pre-release tags together without a dot or number
  between them.  Version ``1.9adev`` is the ``adev`` prerelease of ``1.9``,
  *not* a development pre-release of ``1.9a``.  Use ``.dev`` instead, as in
  ``1.9a.dev``, or separate the prerelease tags with a number, as in
  ``1.9a0dev``.  ``1.9a.dev``, ``1.9a0dev``, and even ``1.9a0.dev0`` are
  identical versions from setuptools' point of view, so you can use whatever
  scheme you prefer. Of these examples, only ``1.9a0.dev0`` is
  :pep:`440`-compliant.

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
pre- or post-release tags. See the following section for more details.


Tagging and "Daily Build" or "Snapshot" Releases
------------------------------------------------

.. warning::
   Please note that running ``python setup.py ...`` directly is no longer
   considered a good practice and that in the future the commands ``egg_info``
   and ``rotate`` will be deprecated.

   As a result, the instructions and information presented in this section
   should be considered **transitional** while setuptools don't provide a
   mechanism for tagging releases.

   Meanwhile, if you can also consider using :pypi:`setuptools-scm` to achieve
   similar objectives.


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
which versions of your project are newer than others).

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

Making "Official" (Non-Snapshot) Releases
-----------------------------------------

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
