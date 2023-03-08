=============================================================
Package Discovery and Resource Access using ``pkg_resources``
=============================================================

The ``pkg_resources`` module distributed with ``setuptools`` provides an API
for Python libraries to access their resource files, and for extensible
applications and frameworks to automatically discover plugins.  It also
provides runtime support for using C extensions that are inside zipfile-format
eggs, support for merging packages that have separately-distributed modules or
subpackages, and APIs for managing Python's current "working set" of active
packages.

.. attention::
   Use of ``pkg_resources`` is deprecated in favor of
   :mod:`importlib.resources`, :mod:`importlib.metadata`
   and their backports (:pypi:`importlib_resources`, :pypi:`importlib_metadata`).
   Users should refrain from new usage of ``pkg_resources`` and
   should work to port to importlib-based solutions.


--------
Overview
--------

The ``pkg_resources`` module provides runtime facilities for finding,
introspecting, activating and using installed Python distributions. Some
of the more advanced features (notably the support for parallel installation
of multiple versions) rely specifically on the "egg" format (either as a
zip archive or subdirectory), while others (such as plugin discovery) will
work correctly so long as "egg-info" metadata directories are available for
relevant distributions.

Eggs are a distribution format for Python modules, similar in concept to
Java's "jars" or Ruby's "gems", or the "wheel" format defined in PEP 427.
However, unlike a pure distribution format, eggs can also be installed and
added directly to ``sys.path`` as an import location. When installed in
this way, eggs are *discoverable*, meaning that they carry metadata that
unambiguously identifies their contents and dependencies. This means that
an installed egg can be *automatically* found and added to ``sys.path`` in
response to simple requests of the form, "get me everything I need to use
docutils' PDF support". This feature allows mutually conflicting versions of
a distribution to co-exist in the same Python installation, with individual
applications activating the desired version at runtime by manipulating the
contents of ``sys.path`` (this differs from the virtual environment
approach, which involves creating isolated environments for each
application).

The following terms are needed in order to explain the capabilities offered
by this module:

project
    A library, framework, script, plugin, application, or collection of data
    or other resources, or some combination thereof.  Projects are assumed to
    have "relatively unique" names, e.g. names registered with PyPI.

release
    A snapshot of a project at a particular point in time, denoted by a version
    identifier.

distribution
    A file or files that represent a particular release.

importable distribution
    A file or directory that, if placed on ``sys.path``, allows Python to
    import any modules contained within it.

pluggable distribution
    An importable distribution whose filename unambiguously identifies its
    release (i.e. project and version), and whose contents unambiguously
    specify what releases of other projects will satisfy its runtime
    requirements.

extra
    An "extra" is an optional feature of a release, that may impose additional
    runtime requirements.  For example, if docutils PDF support required a
    PDF support library to be present, docutils could define its PDF support as
    an "extra", and list what other project releases need to be available in
    order to provide it.

environment
    A collection of distributions potentially available for importing, but not
    necessarily active.  More than one distribution (i.e. release version) for
    a given project may be present in an environment.

working set
    A collection of distributions actually available for importing, as on
    ``sys.path``.  At most one distribution (release version) of a given
    project may be present in a working set, as otherwise there would be
    ambiguity as to what to import.

eggs
    Eggs are pluggable distributions in one of the three formats currently
    supported by ``pkg_resources``.  There are built eggs, development eggs,
    and egg links.  Built eggs are directories or zipfiles whose name ends
    with ``.egg`` and follows the egg naming conventions, and contain an
    ``EGG-INFO`` subdirectory (zipped or otherwise).  Development eggs are
    normal directories of Python code with one or more ``ProjectName.egg-info``
    subdirectories. The development egg format is also used to provide a
    default version of a distribution that is available to software that
    doesn't use ``pkg_resources`` to request specific versions. Egg links
    are ``*.egg-link`` files that contain the name of a built or
    development egg, to support symbolic linking on platforms that do not
    have native symbolic links (or where the symbolic link support is
    limited).

(For more information about these terms and concepts, see also this
`architectural overview`_ of ``pkg_resources`` and Python Eggs in general.)

.. _architectural overview: http://mail.python.org/pipermail/distutils-sig/2005-June/004652.html


.. -----------------
.. Developer's Guide
.. -----------------

.. This section isn't written yet.  Currently planned topics include
    Accessing Resources
    Finding and Activating Package Distributions
        get_provider()
        require()
        WorkingSet
        iter_distributions
    Running Scripts
    Configuration
    Namespace Packages
    Extensible Applications and Frameworks
        Locating entry points
        Activation listeners
        Metadata access
        Extended Discovery and Installation
    Supporting Custom PEP 302 Implementations
.. For now, please check out the extensive `API Reference`_ below.


-------------
API Reference
-------------

Namespace Package Support
=========================

A namespace package is a package that only contains other packages and modules,
with no direct contents of its own.  Such packages can be split across
multiple, separately-packaged distributions.  They are normally used to split
up large packages produced by a single organization, such as in the ``zope``
namespace package for Zope Corporation packages, and the ``peak`` namespace
package for the Python Enterprise Application Kit.

To create a namespace package, you list it in the ``namespace_packages``
argument to ``setup()``, in your project's ``setup.py``.  (See the
:ref:`setuptools documentation on namespace packages <Namespace Packages>` for
more information on this.)  Also, you must add a ``declare_namespace()`` call
in the package's ``__init__.py`` file(s):

``declare_namespace(name)``
    Declare that the dotted package name ``name`` is a "namespace package" whose
    contained packages and modules may be spread across multiple distributions.
    The named package's ``__path__`` will be extended to include the
    corresponding package in all distributions on ``sys.path`` that contain a
    package of that name.  (More precisely, if an importer's
    ``find_module(name)`` returns a loader, then it will also be searched for
    the package's contents.)  Whenever a Distribution's ``activate()`` method
    is invoked, it checks for the presence of namespace packages and updates
    their ``__path__`` contents accordingly.

Applications that manipulate namespace packages or directly alter ``sys.path``
at runtime may also need to use this API function:

``fixup_namespace_packages(path_item)``
    Declare that ``path_item`` is a newly added item on ``sys.path`` that may
    need to be used to update existing namespace packages.  Ordinarily, this is
    called for you when an egg is automatically added to ``sys.path``, but if
    your application modifies ``sys.path`` to include locations that may
    contain portions of a namespace package, you will need to call this
    function to ensure they are added to the existing namespace packages.

Although by default ``pkg_resources`` only supports namespace packages for
filesystem and zip importers, you can extend its support to other "importers"
compatible with PEP 302 using the ``register_namespace_handler()`` function.
See the section below on `Supporting Custom Importers`_ for details.


``WorkingSet`` Objects
======================

The ``WorkingSet`` class provides access to a collection of "active"
distributions.  In general, there is only one meaningful ``WorkingSet``
instance: the one that represents the distributions that are currently active
on ``sys.path``.  This global instance is available under the name
``working_set`` in the ``pkg_resources`` module.  However, specialized
tools may wish to manipulate working sets that don't correspond to
``sys.path``, and therefore may wish to create other ``WorkingSet`` instances.

It's important to note that the global ``working_set`` object is initialized
from ``sys.path`` when ``pkg_resources`` is first imported, but is only updated
if you do all future ``sys.path`` manipulation via ``pkg_resources`` APIs.  If
you manually modify ``sys.path``, you must invoke the appropriate methods on
the ``working_set`` instance to keep it in sync.  Unfortunately, Python does
not provide any way to detect arbitrary changes to a list object like
``sys.path``, so ``pkg_resources`` cannot automatically update the
``working_set`` based on changes to ``sys.path``.

``WorkingSet(entries=None)``
    Create a ``WorkingSet`` from an iterable of path entries.  If ``entries``
    is not supplied, it defaults to the value of ``sys.path`` at the time
    the constructor is called.

    Note that you will not normally construct ``WorkingSet`` instances
    yourself, but instead you will implicitly or explicitly use the global
    ``working_set`` instance.  For the most part, the ``pkg_resources`` API
    is designed so that the ``working_set`` is used by default, such that you
    don't have to explicitly refer to it most of the time.

All distributions available directly on ``sys.path`` will be activated
automatically when ``pkg_resources`` is imported. This behaviour can cause
version conflicts for applications which require non-default versions of
those distributions. To handle this situation, ``pkg_resources`` checks for a
``__requires__`` attribute in the ``__main__`` module when initializing the
default working set, and uses this to ensure a suitable version of each
affected distribution is activated. For example::

    __requires__ = ["CherryPy < 3"] # Must be set before pkg_resources import
    import pkg_resources


Basic ``WorkingSet`` Methods
----------------------------

The following methods of ``WorkingSet`` objects are also available as module-
level functions in ``pkg_resources`` that apply to the default ``working_set``
instance.  Thus, you can use e.g. ``pkg_resources.require()`` as an
abbreviation for ``pkg_resources.working_set.require()``:


``require(*requirements)``
    Ensure that distributions matching ``requirements`` are activated

    ``requirements`` must be a string or a (possibly-nested) sequence
    thereof, specifying the distributions and versions required.  The
    return value is a sequence of the distributions that needed to be
    activated to fulfill the requirements; all relevant distributions are
    included, even if they were already activated in this working set.

    For the syntax of requirement specifiers, see the section below on
    `Requirements Parsing`_.

    In general, it should not be necessary for you to call this method
    directly.  It's intended more for use in quick-and-dirty scripting and
    interactive interpreter hacking than for production use. If you're creating
    an actual library or application, it's strongly recommended that you create
    a "setup.py" script using ``setuptools``, and declare all your requirements
    there.  That way, tools like pip can automatically detect what requirements
    your package has, and deal with them accordingly.

    Note that calling ``require('SomePackage')`` will not install
    ``SomePackage`` if it isn't already present.  If you need to do this, you
    should use the ``resolve()`` method instead, which allows you to pass an
    ``installer`` callback that will be invoked when a needed distribution
    can't be found on the local machine.  You can then have this callback
    display a dialog, automatically download the needed distribution, or
    whatever else is appropriate for your application. See the documentation
    below on the ``resolve()`` method for more information, and also on the
    ``obtain()`` method of ``Environment`` objects.

``run_script(requires, script_name)``
    Locate distribution specified by ``requires`` and run its ``script_name``
    script.  ``requires`` must be a string containing a requirement specifier.
    (See `Requirements Parsing`_ below for the syntax.)

    The script, if found, will be executed in *the caller's globals*.  That's
    because this method is intended to be called from wrapper scripts that
    act as a proxy for the "real" scripts in a distribution.  A wrapper script
    usually doesn't need to do anything but invoke this function with the
    correct arguments.

    If you need more control over the script execution environment, you
    probably want to use the ``run_script()`` method of a ``Distribution``
    object's `Metadata API`_ instead.

``iter_entry_points(group, name=None)``
    Yield entry point objects from ``group`` matching ``name``

    If ``name`` is None, yields all entry points in ``group`` from all
    distributions in the working set, otherwise only ones matching both
    ``group`` and ``name`` are yielded.  Entry points are yielded from the active
    distributions in the order that the distributions appear in the working
    set.  (For the global ``working_set``, this should be the same as the order
    that they are listed in ``sys.path``.)  Note that within the entry points
    advertised by an individual distribution, there is no particular ordering.

    Please see the section below on `Entry Points`_ for more information.


``WorkingSet`` Methods and Attributes
-------------------------------------

These methods are used to query or manipulate the contents of a specific
working set, so they must be explicitly invoked on a particular ``WorkingSet``
instance:

``add_entry(entry)``
    Add a path item to the ``entries``, finding any distributions on it.  You
    should use this when you add additional items to ``sys.path`` and you want
    the global ``working_set`` to reflect the change.  This method is also
    called by the ``WorkingSet()`` constructor during initialization.

    This method uses ``find_distributions(entry,True)`` to find distributions
    corresponding to the path entry, and then ``add()`` them.  ``entry`` is
    always appended to the ``entries`` attribute, even if it is already
    present, however. (This is because ``sys.path`` can contain the same value
    more than once, and the ``entries`` attribute should be able to reflect
    this.)

``__contains__(dist)``
    True if ``dist`` is active in this ``WorkingSet``.  Note that only one
    distribution for a given project can be active in a given ``WorkingSet``.

``__iter__()``
    Yield distributions for non-duplicate projects in the working set.
    The yield order is the order in which the items' path entries were
    added to the working set.

``find(req)``
    Find a distribution matching ``req`` (a ``Requirement`` instance).
    If there is an active distribution for the requested project, this
    returns it, as long as it meets the version requirement specified by
    ``req``.  But, if there is an active distribution for the project and it
    does *not* meet the ``req`` requirement, ``VersionConflict`` is raised.
    If there is no active distribution for the requested project, ``None``
    is returned.

``resolve(requirements, env=None, installer=None)``
    List all distributions needed to (recursively) meet ``requirements``

    ``requirements`` must be a sequence of ``Requirement`` objects.  ``env``,
    if supplied, should be an ``Environment`` instance.  If
    not supplied, an ``Environment`` is created from the working set's
    ``entries``.  ``installer``, if supplied, will be invoked with each
    requirement that cannot be met by an already-installed distribution; it
    should return a ``Distribution`` or ``None``.  (See the ``obtain()`` method
    of `Environment Objects`_, below, for more information on the ``installer``
    argument.)

``add(dist, entry=None)``
    Add ``dist`` to working set, associated with ``entry``

    If ``entry`` is unspecified, it defaults to ``dist.location``.  On exit from
    this routine, ``entry`` is added to the end of the working set's ``.entries``
    (if it wasn't already present).

    ``dist`` is only added to the working set if it's for a project that
    doesn't already have a distribution active in the set.  If it's
    successfully added, any  callbacks registered with the ``subscribe()``
    method will be called.  (See `Receiving Change Notifications`_, below.)

    Note: ``add()`` is automatically called for you by the ``require()``
    method, so you don't normally need to use this method directly.

``entries``
    This attribute represents a "shadow" ``sys.path``, primarily useful for
    debugging.  If you are experiencing import problems, you should check
    the global ``working_set`` object's ``entries`` against ``sys.path``, to
    ensure that they match.  If they do not, then some part of your program
    is manipulating ``sys.path`` without updating the ``working_set``
    accordingly.  IMPORTANT NOTE: do not directly manipulate this attribute!
    Setting it equal to ``sys.path`` will not fix your problem, any more than
    putting black tape over an "engine warning" light will fix your car!  If
    this attribute is out of sync with ``sys.path``, it's merely an *indicator*
    of the problem, not the cause of it.


Receiving Change Notifications
------------------------------

Extensible applications and frameworks may need to receive notification when
a new distribution (such as a plug-in component) has been added to a working
set.  This is what the ``subscribe()`` method and ``add_activation_listener()``
function are for.

``subscribe(callback)``
    Invoke ``callback(distribution)`` once for each active distribution that is
    in the set now, or gets added later.  Because the callback is invoked for
    already-active distributions, you do not need to loop over the working set
    yourself to deal with the existing items; just register the callback and
    be prepared for the fact that it will be called immediately by this method.

    Note that callbacks *must not* allow exceptions to propagate, or they will
    interfere with the operation of other callbacks and possibly result in an
    inconsistent working set state.  Callbacks should use a try/except block
    to ignore, log, or otherwise process any errors, especially since the code
    that caused the callback to be invoked is unlikely to be able to handle
    the errors any better than the callback itself.

``pkg_resources.add_activation_listener()`` is an alternate spelling of
``pkg_resources.working_set.subscribe()``.


Locating Plugins
----------------

Extensible applications will sometimes have a "plugin directory" or a set of
plugin directories, from which they want to load entry points or other
metadata.  The ``find_plugins()`` method allows you to do this, by scanning an
environment for the newest version of each project that can be safely loaded
without conflicts or missing requirements.

``find_plugins(plugin_env, full_env=None, fallback=True)``
   Scan ``plugin_env`` and identify which distributions could be added to this
   working set without version conflicts or missing requirements.

   Example usage::

       distributions, errors = working_set.find_plugins(
           Environment(plugin_dirlist)
       )
       map(working_set.add, distributions)  # add plugins+libs to sys.path
       print "Couldn't load", errors        # display errors

   The ``plugin_env`` should be an ``Environment`` instance that contains only
   distributions that are in the project's "plugin directory" or directories.
   The ``full_env``, if supplied, should be an ``Environment`` instance that
   contains all currently-available distributions.

   If ``full_env`` is not supplied, one is created automatically from the
   ``WorkingSet`` this method is called on, which will typically mean that
   every directory on ``sys.path`` will be scanned for distributions.

   This method returns a 2-tuple: (``distributions``, ``error_info``), where
   ``distributions`` is a list of the distributions found in ``plugin_env`` that
   were loadable, along with any other distributions that are needed to resolve
   their dependencies.  ``error_info`` is a dictionary mapping unloadable plugin
   distributions to an exception instance describing the error that occurred.
   Usually this will be a ``DistributionNotFound`` or ``VersionConflict``
   instance.

   Most applications will use this method mainly on the master ``working_set``
   instance in ``pkg_resources``, and then immediately add the returned
   distributions to the working set so that they are available on sys.path.
   This will make it possible to find any entry points, and allow any other
   metadata tracking and hooks to be activated.

   The resolution algorithm used by ``find_plugins()`` is as follows.  First,
   the project names of the distributions present in ``plugin_env`` are sorted.
   Then, each project's eggs are tried in descending version order (i.e.,
   newest version first).

   An attempt is made to resolve each egg's dependencies. If the attempt is
   successful, the egg and its dependencies are added to the output list and to
   a temporary copy of the working set.  The resolution process continues with
   the next project name, and no older eggs for that project are tried.

   If the resolution attempt fails, however, the error is added to the error
   dictionary.  If the ``fallback`` flag is true, the next older version of the
   plugin is tried, until a working version is found.  If false, the resolution
   process continues with the next plugin project name.

   Some applications may have stricter fallback requirements than others. For
   example, an application that has a database schema or persistent objects
   may not be able to safely downgrade a version of a package. Others may want
   to ensure that a new plugin configuration is either 100% good or else
   revert to a known-good configuration.  (That is, they may wish to revert to
   a known configuration if the ``error_info`` return value is non-empty.)

   Note that this algorithm gives precedence to satisfying the dependencies of
   alphabetically prior project names in case of version conflicts. If two
   projects named "AaronsPlugin" and "ZekesPlugin" both need different versions
   of "TomsLibrary", then "AaronsPlugin" will win and "ZekesPlugin" will be
   disabled due to version conflict.


``Environment`` Objects
=======================

An "environment" is a collection of ``Distribution`` objects, usually ones
that are present and potentially importable on the current platform.
``Environment`` objects are used by ``pkg_resources`` to index available
distributions during dependency resolution.

``Environment(search_path=None, platform=get_supported_platform(), python=PY_MAJOR)``
    Create an environment snapshot by scanning ``search_path`` for distributions
    compatible with ``platform`` and ``python``.  ``search_path`` should be a
    sequence of strings such as might be used on ``sys.path``.  If a
    ``search_path`` isn't supplied, ``sys.path`` is used.

    ``platform`` is an optional string specifying the name of the platform
    that platform-specific distributions must be compatible with.  If
    unspecified, it defaults to the current platform.  ``python`` is an
    optional string naming the desired version of Python (e.g. ``'2.4'``);
    it defaults to the currently-running version.

    You may explicitly set ``platform`` (and/or ``python``) to ``None`` if you
    wish to include *all* distributions, not just those compatible with the
    running platform or Python version.

    Note that ``search_path`` is scanned immediately for distributions, and the
    resulting ``Environment`` is a snapshot of the found distributions.  It
    is not automatically updated if the system's state changes due to e.g.
    installation or removal of distributions.

``__getitem__(project_name)``
    Returns a list of distributions for the given project name, ordered
    from newest to oldest version.  (And highest to lowest format precedence
    for distributions that contain the same version of the project.)  If there
    are no distributions for the project, returns an empty list.

``__iter__()``
    Yield the unique project names of the distributions in this environment.
    The yielded names are always in lower case.

``add(dist)``
    Add ``dist`` to the environment if it matches the platform and python version
    specified at creation time, and only if the distribution hasn't already
    been added. (i.e., adding the same distribution more than once is a no-op.)

``remove(dist)``
    Remove ``dist`` from the environment.

``can_add(dist)``
    Is distribution ``dist`` acceptable for this environment?  If it's not
    compatible with the ``platform`` and ``python`` version values specified
    when the environment was created, a false value is returned.

``__add__(dist_or_env)``  (``+`` operator)
    Add a distribution or environment to an ``Environment`` instance, returning
    a *new* environment object that contains all the distributions previously
    contained by both.  The new environment will have a ``platform`` and
    ``python`` of ``None``, meaning that it will not reject any distributions
    from being added to it; it will simply accept whatever is added.  If you
    want the added items to be filtered for platform and Python version, or
    you want to add them to the *same* environment instance, you should use
    in-place addition (``+=``) instead.

``__iadd__(dist_or_env)``  (``+=`` operator)
    Add a distribution or environment to an ``Environment`` instance
    *in-place*, updating the existing instance and returning it.  The
    ``platform`` and ``python`` filter attributes take effect, so distributions
    in the source that do not have a suitable platform string or Python version
    are silently ignored.

``best_match(req, working_set, installer=None)``
    Find distribution best matching ``req`` and usable on ``working_set``

    This calls the ``find(req)`` method of the ``working_set`` to see if a
    suitable distribution is already active.  (This may raise
    ``VersionConflict`` if an unsuitable version of the project is already
    active in the specified ``working_set``.)  If a suitable distribution isn't
    active, this method returns the newest distribution in the environment
    that meets the ``Requirement`` in ``req``.  If no suitable distribution is
    found, and ``installer`` is supplied, then the result of calling
    the environment's ``obtain(req, installer)`` method will be returned.

``obtain(requirement, installer=None)``
    Obtain a distro that matches requirement (e.g. via download).  In the
    base ``Environment`` class, this routine just returns
    ``installer(requirement)``, unless ``installer`` is None, in which case
    None is returned instead.  This method is a hook that allows subclasses
    to attempt other ways of obtaining a distribution before falling back
    to the ``installer`` argument.

``scan(search_path=None)``
    Scan ``search_path`` for distributions usable on ``platform``

    Any distributions found are added to the environment.  ``search_path`` should
    be a sequence of strings such as might be used on ``sys.path``.  If not
    supplied, ``sys.path`` is used.  Only distributions conforming to
    the platform/python version defined at initialization are added.  This
    method is a shortcut for using the ``find_distributions()`` function to
    find the distributions from each item in ``search_path``, and then calling
    ``add()`` to add each one to the environment.


``Requirement`` Objects
=======================

``Requirement`` objects express what versions of a project are suitable for
some purpose.  These objects (or their string form) are used by various
``pkg_resources`` APIs in order to find distributions that a script or
distribution needs.


Requirements Parsing
--------------------

``parse_requirements(s)``
    Yield ``Requirement`` objects for a string or iterable of lines.  Each
    requirement must start on a new line.  See below for syntax.

``Requirement.parse(s)``
    Create a ``Requirement`` object from a string or iterable of lines.  A
    ``ValueError`` is raised if the string or lines do not contain a valid
    requirement specifier, or if they contain more than one specifier.  (To
    parse multiple specifiers from a string or iterable of strings, use
    ``parse_requirements()`` instead.)

    The syntax of a requirement specifier is defined in full in PEP 508.

    Some examples of valid requirement specifiers::

        FooProject >= 1.2
        Fizzy [foo, bar]
        PickyThing>1.6,<=1.9,!=1.8.6
        SomethingWhoseVersionIDontCareAbout
        SomethingWithMarker[foo]>1.0;python_version<"2.7"

    The project name is the only required portion of a requirement string, and
    if it's the only thing supplied, the requirement will accept any version
    of that project.

    The "extras" in a requirement are used to request optional features of a
    project, that may require additional project distributions in order to
    function.  For example, if the hypothetical "Report-O-Rama" project offered
    optional PDF support, it might require an additional library in order to
    provide that support.  Thus, a project needing Report-O-Rama's PDF features
    could use a requirement of ``Report-O-Rama[PDF]`` to request installation
    or activation of both Report-O-Rama and any libraries it needs in order to
    provide PDF support.  For example, you could use::

        pip install Report-O-Rama[PDF]

    To install the necessary packages using pip, or call
    ``pkg_resources.require('Report-O-Rama[PDF]')`` to add the necessary
    distributions to sys.path at runtime.

    The "markers" in a requirement are used to specify when a requirement
    should be installed -- the requirement will be installed if the marker
    evaluates as true in the current environment. For example, specifying
    ``argparse;python_version<"3.0"`` will not install in an Python 3
    environment, but will in a Python 2 environment.

``Requirement`` Methods and Attributes
--------------------------------------

``__contains__(dist_or_version)``
    Return true if ``dist_or_version`` fits the criteria for this requirement.
    If ``dist_or_version`` is a ``Distribution`` object, its project name must
    match the requirement's project name, and its version must meet the
    requirement's version criteria.  If ``dist_or_version`` is a string, it is
    parsed using the ``parse_version()`` utility function.  Otherwise, it is
    assumed to be an already-parsed version.

    The ``Requirement`` object's version specifiers (``.specs``) are internally
    sorted into ascending version order, and used to establish what ranges of
    versions are acceptable.  Adjacent redundant conditions are effectively
    consolidated (e.g. ``">1, >2"`` produces the same results as ``">2"``, and
    ``"<2,<3"`` produces the same results as ``"<2"``). ``"!="`` versions are
    excised from the ranges they fall within.  The version being tested for
    acceptability is then checked for membership in the resulting ranges.

``__eq__(other_requirement)``
    A requirement compares equal to another requirement if they have
    case-insensitively equal project names, version specifiers, and "extras".
    (The order that extras and version specifiers are in is also ignored.)
    Equal requirements also have equal hashes, so that requirements can be
    used in sets or as dictionary keys.

``__str__()``
    The string form of a ``Requirement`` is a string that, if passed to
    ``Requirement.parse()``, would return an equal ``Requirement`` object.

``project_name``
    The name of the required project

``key``
    An all-lowercase version of the ``project_name``, useful for comparison
    or indexing.

``extras``
    A tuple of names of "extras" that this requirement calls for.  (These will
    be all-lowercase and normalized using the ``safe_extra()`` parsing utility
    function, so they may not exactly equal the extras the requirement was
    created with.)

``specs``
    A list of ``(op,version)`` tuples, sorted in ascending parsed-version
    order.  The ``op`` in each tuple is a comparison operator, represented as
    a string.  The ``version`` is the (unparsed) version number.

``marker``
    An instance of ``packaging.markers.Marker`` that allows evaluation
    against the current environment. May be None if no marker specified.

``url``
    The location to download the requirement from if specified.

Entry Points
============

Entry points are a simple way for distributions to "advertise" Python objects
(such as functions or classes) for use by other distributions.  Extensible
applications and frameworks can search for entry points with a particular name
or group, either from a specific distribution or from all active distributions
on sys.path, and then inspect or load the advertised objects at will.

Entry points belong to "groups" which are named with a dotted name similar to
a Python package or module name.  For example, the ``setuptools`` package uses
an entry point named ``distutils.commands`` in order to find commands defined
by distutils extensions.  ``setuptools`` treats the names of entry points
defined in that group as the acceptable commands for a setup script.

In a similar way, other packages can define their own entry point groups,
either using dynamic names within the group (like ``distutils.commands``), or
possibly using predefined names within the group.  For example, a blogging
framework that offers various pre- or post-publishing hooks might define an
entry point group and look for entry points named "pre_process" and
"post_process" within that group.

To advertise an entry point, a project needs to use ``setuptools`` and provide
an ``entry_points`` argument to ``setup()`` in its setup script, so that the
entry points will be included in the distribution's metadata.  For more
details, see :ref:`Advertising Behavior<dynamic discovery of services and plugins>`.

Each project distribution can advertise at most one entry point of a given
name within the same entry point group.  For example, a distutils extension
could advertise two different ``distutils.commands`` entry points, as long as
they had different names.  However, there is nothing that prevents *different*
projects from advertising entry points of the same name in the same group.  In
some cases, this is a desirable thing, since the application or framework that
uses the entry points may be calling them as hooks, or in some other way
combining them.  It is up to the application or framework to decide what to do
if multiple distributions advertise an entry point; some possibilities include
using both entry points, displaying an error message, using the first one found
in sys.path order, etc.


Convenience API
---------------

In the following functions, the ``dist`` argument can be a ``Distribution``
instance, a ``Requirement`` instance, or a string specifying a requirement
(i.e. project name, version, etc.).  If the argument is a string or
``Requirement``, the specified distribution is located (and added to sys.path
if not already present).  An error will be raised if a matching distribution is
not available.

The ``group`` argument should be a string containing a dotted identifier,
identifying an entry point group.  If you are defining an entry point group,
you should include some portion of your package's name in the group name so as
to avoid collision with other packages' entry point groups.

``load_entry_point(dist, group, name)``
    Load the named entry point from the specified distribution, or raise
    ``ImportError``.

``get_entry_info(dist, group, name)``
    Return an ``EntryPoint`` object for the given ``group`` and ``name`` from
    the specified distribution.  Returns ``None`` if the distribution has not
    advertised a matching entry point.

``get_entry_map(dist, group=None)``
    Return the distribution's entry point map for ``group``, or the full entry
    map for the distribution.  This function always returns a dictionary,
    even if the distribution advertises no entry points.  If ``group`` is given,
    the dictionary maps entry point names to the corresponding ``EntryPoint``
    object.  If ``group`` is None, the dictionary maps group names to
    dictionaries that then map entry point names to the corresponding
    ``EntryPoint`` instance in that group.

``iter_entry_points(group, name=None)``
    Yield entry point objects from ``group`` matching ``name``.

    If ``name`` is None, yields all entry points in ``group`` from all
    distributions in the working set on sys.path, otherwise only ones matching
    both ``group`` and ``name`` are yielded.  Entry points are yielded from
    the active distributions in the order that the distributions appear on
    sys.path.  (Within entry points for a particular distribution, however,
    there is no particular ordering.)

    (This API is actually a method of the global ``working_set`` object; see
    the section above on `Basic WorkingSet Methods`_ for more information.)


Creating and Parsing
--------------------

``EntryPoint(name, module_name, attrs=(), extras=(), dist=None)``
    Create an ``EntryPoint`` instance.  ``name`` is the entry point name.  The
    ``module_name`` is the (dotted) name of the module containing the advertised
    object.  ``attrs`` is an optional tuple of names to look up from the
    module to obtain the advertised object.  For example, an ``attrs`` of
    ``("foo","bar")`` and a ``module_name`` of ``"baz"`` would mean that the
    advertised object could be obtained by the following code::

        import baz
        advertised_object = baz.foo.bar

    The ``extras`` are an optional tuple of "extra feature" names that the
    distribution needs in order to provide this entry point.  When the
    entry point is loaded, these extra features are looked up in the ``dist``
    argument to find out what other distributions may need to be activated
    on sys.path; see the ``load()`` method for more details.  The ``extras``
    argument is only meaningful if ``dist`` is specified.  ``dist`` must be
    a ``Distribution`` instance.

``EntryPoint.parse(src, dist=None)`` (classmethod)
    Parse a single entry point from string ``src``

    Entry point syntax follows the form::

        name = some.module:some.attr [extra1,extra2]

    The entry name and module name are required, but the ``:attrs`` and
    ``[extras]`` parts are optional, as is the whitespace shown between
    some of the items.  The ``dist`` argument is passed through to the
    ``EntryPoint()`` constructor, along with the other values parsed from
    ``src``.

``EntryPoint.parse_group(group, lines, dist=None)`` (classmethod)
    Parse ``lines`` (a string or sequence of lines) to create a dictionary
    mapping entry point names to ``EntryPoint`` objects.  ``ValueError`` is
    raised if entry point names are duplicated, if ``group`` is not a valid
    entry point group name, or if there are any syntax errors.  (Note: the
    ``group`` parameter is used only for validation and to create more
    informative error messages.)  If ``dist`` is provided, it will be used to
    set the ``dist`` attribute of the created ``EntryPoint`` objects.

``EntryPoint.parse_map(data, dist=None)`` (classmethod)
    Parse ``data`` into a dictionary mapping group names to dictionaries mapping
    entry point names to ``EntryPoint`` objects.  If ``data`` is a dictionary,
    then the keys are used as group names and the values are passed to
    ``parse_group()`` as the ``lines`` argument.  If ``data`` is a string or
    sequence of lines, it is first split into .ini-style sections (using
    the ``split_sections()`` utility function) and the section names are used
    as group names.  In either case, the ``dist`` argument is passed through to
    ``parse_group()`` so that the entry points will be linked to the specified
    distribution.


``EntryPoint`` Objects
----------------------

For simple introspection, ``EntryPoint`` objects have attributes that
correspond exactly to the constructor argument names: ``name``,
``module_name``, ``attrs``, ``extras``, and ``dist`` are all available.  In
addition, the following methods are provided:

``load()``
    Load the entry point, returning the advertised Python object.  Effectively
    calls ``self.require()`` then returns ``self.resolve()``.

``require(env=None, installer=None)``
    Ensure that any "extras" needed by the entry point are available on
    sys.path.  ``UnknownExtra`` is raised if the ``EntryPoint`` has ``extras``,
    but no ``dist``, or if the named extras are not defined by the
    distribution.  If ``env`` is supplied, it must be an ``Environment``, and it
    will be used to search for needed distributions if they are not already
    present on sys.path.  If ``installer`` is supplied, it must be a callable
    taking a ``Requirement`` instance and returning a matching importable
    ``Distribution`` instance or None.

``resolve()``
    Resolve the entry point from its module and attrs, returning the advertised
    Python object. Raises ``ImportError`` if it cannot be obtained.

``__str__()``
    The string form of an ``EntryPoint`` is a string that could be passed to
    ``EntryPoint.parse()`` to produce an equivalent ``EntryPoint``.


``Distribution`` Objects
========================

``Distribution`` objects represent collections of Python code that may or may
not be importable, and may or may not have metadata and resources associated
with them.  Their metadata may include information such as what other projects
the distribution depends on, what entry points the distribution advertises, and
so on.


Getting or Creating Distributions
---------------------------------

Most commonly, you'll obtain ``Distribution`` objects from a ``WorkingSet`` or
an ``Environment``.  (See the sections above on `WorkingSet Objects`_ and
`Environment Objects`_, which are containers for active distributions and
available distributions, respectively.)  You can also obtain ``Distribution``
objects from one of these high-level APIs:

``find_distributions(path_item, only=False)``
    Yield distributions accessible via ``path_item``.  If ``only`` is true, yield
    only distributions whose ``location`` is equal to ``path_item``.  In other
    words, if ``only`` is true, this yields any distributions that would be
    importable if ``path_item`` were on ``sys.path``.  If ``only`` is false, this
    also yields distributions that are "in" or "under" ``path_item``, but would
    not be importable unless their locations were also added to ``sys.path``.

``get_distribution(dist_spec)``
    Return a ``Distribution`` object for a given ``Requirement`` or string.
    If ``dist_spec`` is already a ``Distribution`` instance, it is returned.
    If it is a ``Requirement`` object or a string that can be parsed into one,
    it is used to locate and activate a matching distribution, which is then
    returned.

However, if you're creating specialized tools for working with distributions,
or creating a new distribution format, you may also need to create
``Distribution`` objects directly, using one of the three constructors below.

These constructors all take an optional ``metadata`` argument, which is used to
access any resources or metadata associated with the distribution.  ``metadata``
must be an object that implements the ``IResourceProvider`` interface, or None.
If it is None, an ``EmptyProvider`` is used instead.  ``Distribution`` objects
implement both the `IResourceProvider`_ and `IMetadataProvider Methods`_ by
delegating them to the ``metadata`` object.

``Distribution.from_location(location, basename, metadata=None, **kw)`` (classmethod)
    Create a distribution for ``location``, which must be a string such as a
    URL, filename, or other string that might be used on ``sys.path``.
    ``basename`` is a string naming the distribution, like ``Foo-1.2-py2.4.egg``.
    If ``basename`` ends with ``.egg``, then the project's name, version, python
    version and platform are extracted from the filename and used to set those
    properties of the created distribution.  Any additional keyword arguments
    are forwarded to the ``Distribution()`` constructor.

``Distribution.from_filename(filename, metadata=None**kw)`` (classmethod)
    Create a distribution by parsing a local filename.  This is a shorter way
    of saying  ``Distribution.from_location(normalize_path(filename),
    os.path.basename(filename), metadata)``.  In other words, it creates a
    distribution whose location is the normalize form of the filename, parsing
    name and version information from the base portion of the filename.  Any
    additional keyword arguments are forwarded to the ``Distribution()``
    constructor.

``Distribution(location,metadata,project_name,version,py_version,platform,precedence)``
    Create a distribution by setting its properties.  All arguments are
    optional and default to None, except for ``py_version`` (which defaults to
    the current Python version) and ``precedence`` (which defaults to
    ``EGG_DIST``; for more details see ``precedence`` under `Distribution
    Attributes`_ below).  Note that it's usually easier to use the
    ``from_filename()`` or ``from_location()`` constructors than to specify
    all these arguments individually.


``Distribution`` Attributes
---------------------------

location
    A string indicating the distribution's location.  For an importable
    distribution, this is the string that would be added to ``sys.path`` to
    make it actively importable.  For non-importable distributions, this is
    simply a filename, URL, or other way of locating the distribution.

project_name
    A string, naming the project that this distribution is for.  Project names
    are defined by a project's setup script, and they are used to identify
    projects on PyPI.  When a ``Distribution`` is constructed, the
    ``project_name`` argument is passed through the ``safe_name()`` utility
    function to filter out any unacceptable characters.

key
    ``dist.key`` is short for ``dist.project_name.lower()``.  It's used for
    case-insensitive comparison and indexing of distributions by project name.

extras
    A list of strings, giving the names of extra features defined by the
    project's dependency list (the ``extras_require`` argument specified in
    the project's setup script).

version
    A string denoting what release of the project this distribution contains.
    When a ``Distribution`` is constructed, the ``version`` argument is passed
    through the ``safe_version()`` utility function to filter out any
    unacceptable characters.  If no ``version`` is specified at construction
    time, then attempting to access this attribute later will cause the
    ``Distribution`` to try to discover its version by reading its ``PKG-INFO``
    metadata file.  If ``PKG-INFO`` is unavailable or can't be parsed,
    ``ValueError`` is raised.

parsed_version
    The ``parsed_version`` is an object representing a "parsed" form of the
    distribution's ``version``.  ``dist.parsed_version`` is a shortcut for
    calling ``parse_version(dist.version)``.  It is used to compare or sort
    distributions by version.  (See the `Parsing Utilities`_ section below for
    more information on the ``parse_version()`` function.)  Note that accessing
    ``parsed_version`` may result in a ``ValueError`` if the ``Distribution``
    was constructed without a ``version`` and without ``metadata`` capable of
    supplying the missing version info.

py_version
    The major/minor Python version the distribution supports, as a string.
    For example, "2.7" or "3.4".  The default is the current version of Python.

platform
    A string representing the platform the distribution is intended for, or
    ``None`` if the distribution is "pure Python" and therefore cross-platform.
    See `Platform Utilities`_ below for more information on platform strings.

precedence
    A distribution's ``precedence`` is used to determine the relative order of
    two distributions that have the same ``project_name`` and
    ``parsed_version``.  The default precedence is ``pkg_resources.EGG_DIST``,
    which is the highest (i.e. most preferred) precedence.  The full list
    of predefined precedences, from most preferred to least preferred, is:
    ``EGG_DIST``, ``BINARY_DIST``, ``SOURCE_DIST``, ``CHECKOUT_DIST``, and
    ``DEVELOP_DIST``.  Normally, precedences other than ``EGG_DIST`` are used
    only by the ``setuptools.package_index`` module, when sorting distributions
    found in a package index to determine their suitability for installation.
    "System" and "Development" eggs (i.e., ones that use the ``.egg-info``
    format), however, are automatically given a precedence of ``DEVELOP_DIST``.



``Distribution`` Methods
------------------------

``activate(path=None)``
    Ensure distribution is importable on ``path``.  If ``path`` is None,
    ``sys.path`` is used instead.  This ensures that the distribution's
    ``location`` is in the ``path`` list, and it also performs any necessary
    namespace package fixups or declarations.  (That is, if the distribution
    contains namespace packages, this method ensures that they are declared,
    and that the distribution's contents for those namespace packages are
    merged with the contents provided by any other active distributions.  See
    the section above on `Namespace Package Support`_ for more information.)

    ``pkg_resources`` adds a notification callback to the global ``working_set``
    that ensures this method is called whenever a distribution is added to it.
    Therefore, you should not normally need to explicitly call this method.
    (Note that this means that namespace packages on ``sys.path`` are always
    imported as soon as ``pkg_resources`` is, which is another reason why
    namespace packages should not contain any code or import statements.)

``as_requirement()``
    Return a ``Requirement`` instance that matches this distribution's project
    name and version.

``requires(extras=())``
    List the ``Requirement`` objects that specify this distribution's
    dependencies.  If ``extras`` is specified, it should be a sequence of names
    of "extras" defined by the distribution, and the list returned will then
    include any dependencies needed to support the named "extras".

``clone(**kw)``
    Create a copy of the distribution.  Any supplied keyword arguments override
    the corresponding argument to the ``Distribution()`` constructor, allowing
    you to change some of the copied distribution's attributes.

``egg_name()``
    Return what this distribution's standard filename should be, not including
    the ".egg" extension.  For example, a distribution for project "Foo"
    version 1.2 that runs on Python 2.3 for Windows would have an ``egg_name()``
    of ``Foo-1.2-py2.3-win32``.  Any dashes in the name or version are
    converted to underscores.  (``Distribution.from_location()`` will convert
    them back when parsing a ".egg" file name.)

``__cmp__(other)``, ``__hash__()``
    Distribution objects are hashed and compared on the basis of their parsed
    version and precedence, followed by their key (lowercase project name),
    location, Python version, and platform.

The following methods are used to access ``EntryPoint`` objects advertised
by the distribution.  See the section above on `Entry Points`_ for more
detailed information about these operations:

``get_entry_info(group, name)``
    Return the ``EntryPoint`` object for ``group`` and ``name``, or None if no
    such point is advertised by this distribution.

``get_entry_map(group=None)``
    Return the entry point map for ``group``.  If ``group`` is None, return
    a dictionary mapping group names to entry point maps for all groups.
    (An entry point map is a dictionary of entry point names to ``EntryPoint``
    objects.)

``load_entry_point(group, name)``
    Short for ``get_entry_info(group, name).load()``.  Returns the object
    advertised by the named entry point, or raises ``ImportError`` if
    the entry point isn't advertised by this distribution, or there is some
    other import problem.

In addition to the above methods, ``Distribution`` objects also implement all
of the `IResourceProvider`_ and `IMetadataProvider Methods`_ (which are
documented in later sections):

* ``has_metadata(name)``
* ``metadata_isdir(name)``
* ``metadata_listdir(name)``
* ``get_metadata(name)``
* ``get_metadata_lines(name)``
* ``run_script(script_name, namespace)``
* ``get_resource_filename(manager, resource_name)``
* ``get_resource_stream(manager, resource_name)``
* ``get_resource_string(manager, resource_name)``
* ``has_resource(resource_name)``
* ``resource_isdir(resource_name)``
* ``resource_listdir(resource_name)``

If the distribution was created with a ``metadata`` argument, these resource and
metadata access methods are all delegated to that ``metadata`` provider.
Otherwise, they are delegated to an ``EmptyProvider``, so that the distribution
will appear to have no resources or metadata.  This delegation approach is used
so that supporting custom importers or new distribution formats can be done
simply by creating an appropriate `IResourceProvider`_ implementation; see the
section below on `Supporting Custom Importers`_ for more details.

.. _ResourceManager API:

``ResourceManager`` API
=======================

The ``ResourceManager`` class provides uniform access to package resources,
whether those resources exist as files and directories or are compressed in
an archive of some kind.

Normally, you do not need to create or explicitly manage ``ResourceManager``
instances, as the ``pkg_resources`` module creates a global instance for you,
and makes most of its methods available as top-level names in the
``pkg_resources`` module namespace.  So, for example, this code actually
calls the ``resource_string()`` method of the global ``ResourceManager``::

    import pkg_resources
    my_data = pkg_resources.resource_string(__name__, "foo.dat")

Thus, you can use the APIs below without needing an explicit
``ResourceManager`` instance; just import and use them as needed.


Basic Resource Access
---------------------

In the following methods, the ``package_or_requirement`` argument may be either
a Python package/module name (e.g. ``foo.bar``) or a ``Requirement`` instance.
If it is a package or module name, the named module or package must be
importable (i.e., be in a distribution or directory on ``sys.path``), and the
``resource_name`` argument is interpreted relative to the named package.  (Note
that if a module name is used, then the resource name is relative to the
package immediately containing the named module.  Also, you should not use use
a namespace package name, because a namespace package can be spread across
multiple distributions, and is therefore ambiguous as to which distribution
should be searched for the resource.)

If it is a ``Requirement``, then the requirement is automatically resolved
(searching the current ``Environment`` if necessary) and a matching
distribution is added to the ``WorkingSet`` and ``sys.path`` if one was not
already present.  (Unless the ``Requirement`` can't be satisfied, in which
case an exception is raised.)  The ``resource_name`` argument is then interpreted
relative to the root of the identified distribution; i.e. its first path
segment will be treated as a peer of the top-level modules or packages in the
distribution.

Note that resource names must be ``/``-separated paths rooted at the package,
cannot contain relative names like ``".."``, and cannot be absolute.  Do *not* use
``os.path`` routines to manipulate resource paths, as they are *not* filesystem
paths.

``resource_exists(package_or_requirement, resource_name)``
    Does the named resource exist?  Return ``True`` or ``False`` accordingly.

``resource_stream(package_or_requirement, resource_name)``
    Return a readable file-like object for the specified resource; it may be
    an actual file, a ``StringIO``, or some similar object.  The stream is
    in "binary mode", in the sense that whatever bytes are in the resource
    will be read as-is.

``resource_string(package_or_requirement, resource_name)``
    Return the specified resource as ``bytes``.  The resource is read in
    binary fashion, such that the returned string contains exactly the bytes
    that are stored in the resource.

``resource_isdir(package_or_requirement, resource_name)``
    Is the named resource a directory?  Return ``True`` or ``False``
    accordingly.

``resource_listdir(package_or_requirement, resource_name)``
    List the contents of the named resource directory, just like ``os.listdir``
    except that it works even if the resource is in a zipfile.

Note that only ``resource_exists()`` and ``resource_isdir()`` are insensitive
as to the resource type.  You cannot use ``resource_listdir()`` on a file
resource, and you can't use ``resource_string()`` or ``resource_stream()`` on
directory resources.  Using an inappropriate method for the resource type may
result in an exception or undefined behavior, depending on the platform and
distribution format involved.


Resource Extraction
-------------------

``resource_filename(package_or_requirement, resource_name)``
    Sometimes, it is not sufficient to access a resource in string or stream
    form, and a true filesystem filename is needed.  In such cases, you can
    use this method (or module-level function) to obtain a filename for a
    resource.  If the resource is in an archive distribution (such as a zipped
    egg), it will be extracted to a cache directory, and the filename within
    the cache will be returned.  If the named resource is a directory, then
    all resources within that directory (including subdirectories) are also
    extracted.  If the named resource is a C extension or "eager resource"
    (see the ``setuptools`` documentation for details), then all C extensions
    and eager resources are extracted at the same time.

    Archived resources are extracted to a cache location that can be managed by
    the following two methods:

``set_extraction_path(path)``
    Set the base path where resources will be extracted to, if needed.

    If you do not call this routine before any extractions take place, the
    path defaults to the return value of ``get_default_cache()``.  (Which is
    based on the ``PYTHON_EGG_CACHE`` environment variable, with various
    platform-specific fallbacks.  See that routine's documentation for more
    details.)

    Resources are extracted to subdirectories of this path based upon
    information given by the resource provider.  You may set this to a
    temporary directory, but then you must call ``cleanup_resources()`` to
    delete the extracted files when done.  There is no guarantee that
    ``cleanup_resources()`` will be able to remove all extracted files.  (On
    Windows, for example, you can't unlink .pyd or .dll files that are still
    in use.)

    Note that you may not change the extraction path for a given resource
    manager once resources have been extracted, unless you first call
    ``cleanup_resources()``.

``cleanup_resources(force=False)``
    Delete all extracted resource files and directories, returning a list
    of the file and directory names that could not be successfully removed.
    This function does not have any concurrency protection, so it should
    generally only be called when the extraction path is a temporary
    directory exclusive to a single process.  This method is not
    automatically called; you must call it explicitly or register it as an
    ``atexit`` function if you wish to ensure cleanup of a temporary
    directory used for extractions.


"Provider" Interface
--------------------

If you are implementing an ``IResourceProvider`` and/or ``IMetadataProvider``
for a new distribution archive format, you may need to use the following
``IResourceManager`` methods to coordinate extraction of resources to the
filesystem.  If you're not implementing an archive format, however, you have
no need to use these methods.  Unlike the other methods listed above, they are
*not* available as top-level functions tied to the global ``ResourceManager``;
you must therefore have an explicit ``ResourceManager`` instance to use them.

``get_cache_path(archive_name, names=())``
    Return absolute location in cache for ``archive_name`` and ``names``

    The parent directory of the resulting path will be created if it does
    not already exist.  ``archive_name`` should be the base filename of the
    enclosing egg (which may not be the name of the enclosing zipfile!),
    including its ".egg" extension.  ``names``, if provided, should be a
    sequence of path name parts "under" the egg's extraction location.

    This method should only be called by resource providers that need to
    obtain an extraction location, and only for names they intend to
    extract, as it tracks the generated names for possible cleanup later.

``extraction_error()``
    Raise an ``ExtractionError`` describing the active exception as interfering
    with the extraction process.  You should call this if you encounter any
    OS errors extracting the file to the cache path; it will format the
    operating system exception for you, and add other information to the
    ``ExtractionError`` instance that may be needed by programs that want to
    wrap or handle extraction errors themselves.

``postprocess(tempname, filename)``
    Perform any platform-specific postprocessing of ``tempname``.
    Resource providers should call this method ONLY after successfully
    extracting a compressed resource.  They must NOT call it on resources
    that are already in the filesystem.

    ``tempname`` is the current (temporary) name of the file, and ``filename``
    is the name it will be renamed to by the caller after this routine
    returns.


Metadata API
============

The metadata API is used to access metadata resources bundled in a pluggable
distribution.  Metadata resources are virtual files or directories containing
information about the distribution, such as might be used by an extensible
application or framework to connect "plugins".  Like other kinds of resources,
metadata resource names are ``/``-separated and should not contain ``..`` or
begin with a ``/``.  You should not use ``os.path`` routines to manipulate
resource paths.

The metadata API is provided by objects implementing the ``IMetadataProvider``
or ``IResourceProvider`` interfaces.  ``Distribution`` objects implement this
interface, as do objects returned by the ``get_provider()`` function:

``get_provider(package_or_requirement)``
    If a package name is supplied, return an ``IResourceProvider`` for the
    package.  If a ``Requirement`` is supplied, resolve it by returning a
    ``Distribution`` from the current working set (searching the current
    ``Environment`` if necessary and adding the newly found ``Distribution``
    to the working set).  If the named package can't be imported, or the
    ``Requirement`` can't be satisfied, an exception is raised.

    NOTE: if you use a package name rather than a ``Requirement``, the object
    you get back may not be a pluggable distribution, depending on the method
    by which the package was installed.  In particular, "development" packages
    and "single-version externally-managed" packages do not have any way to
    map from a package name to the corresponding project's metadata.  Do not
    write code that passes a package name to ``get_provider()`` and then tries
    to retrieve project metadata from the returned object.  It may appear to
    work when the named package is in an ``.egg`` file or directory, but
    it will fail in other installation scenarios.  If you want project
    metadata, you need to ask for a *project*, not a package.


``IMetadataProvider`` Methods
-----------------------------

The methods provided by objects (such as ``Distribution`` instances) that
implement the ``IMetadataProvider`` or ``IResourceProvider`` interfaces are:

``has_metadata(name)``
    Does the named metadata resource exist?

``metadata_isdir(name)``
    Is the named metadata resource a directory?

``metadata_listdir(name)``
    List of metadata names in the directory (like ``os.listdir()``)

``get_metadata(name)``
    Return the named metadata resource as a string.  The data is read in binary
    mode; i.e., the exact bytes of the resource file are returned.

``get_metadata_lines(name)``
    Yield named metadata resource as list of non-blank non-comment lines.  This
    is short for calling ``yield_lines(provider.get_metadata(name))``.  See the
    section on `yield_lines()`_ below for more information on the syntax it
    recognizes.

``run_script(script_name, namespace)``
    Execute the named script in the supplied namespace dictionary.  Raises
    ``ResolutionError`` if there is no script by that name in the ``scripts``
    metadata directory.  ``namespace`` should be a Python dictionary, usually
    a module dictionary if the script is being run as a module.


Exceptions
==========

``pkg_resources`` provides a simple exception hierarchy for problems that may
occur when processing requests to locate and activate packages::

    ResolutionError
        DistributionNotFound
        VersionConflict
        UnknownExtra

    ExtractionError

``ResolutionError``
    This class is used as a base class for the other three exceptions, so that
    you can catch all of them with a single "except" clause.  It is also raised
    directly for miscellaneous requirement-resolution problems like trying to
    run a script that doesn't exist in the distribution it was requested from.

``DistributionNotFound``
    A distribution needed to fulfill a requirement could not be found.

``VersionConflict``
    The requested version of a project conflicts with an already-activated
    version of the same project.

``UnknownExtra``
    One of the "extras" requested was not recognized by the distribution it
    was requested from.

``ExtractionError``
    A problem occurred extracting a resource to the Python Egg cache.  The
    following attributes are available on instances of this exception:

    manager
        The resource manager that raised this exception

    cache_path
        The base directory for resource extraction

    original_error
        The exception instance that caused extraction to fail


Supporting Custom Importers
===========================

By default, ``pkg_resources`` supports normal filesystem imports, and
``zipimport`` importers.  If you wish to use the ``pkg_resources`` features
with other (PEP 302-compatible) importers or module loaders, you may need to
register various handlers and support functions using these APIs:

``register_finder(importer_type, distribution_finder)``
    Register ``distribution_finder`` to find distributions in ``sys.path`` items.
    ``importer_type`` is the type or class of a PEP 302 "Importer" (``sys.path``
    item handler), and ``distribution_finder`` is a callable that, when passed a
    path item, the importer instance, and an ``only`` flag, yields
    ``Distribution`` instances found under that path item.  (The ``only`` flag,
    if true, means the finder should yield only ``Distribution`` objects whose
    ``location`` is equal to the path item provided.)

    See the source of the ``pkg_resources.find_on_path`` function for an
    example finder function.

``register_loader_type(loader_type, provider_factory)``
    Register ``provider_factory`` to make ``IResourceProvider`` objects for
    ``loader_type``.  ``loader_type`` is the type or class of a PEP 302
    ``module.__loader__``, and ``provider_factory`` is a function that, when
    passed a module object, returns an `IResourceProvider`_ for that module,
    allowing it to be used with the `ResourceManager API`_.

``register_namespace_handler(importer_type, namespace_handler)``
    Register ``namespace_handler`` to declare namespace packages for the given
    ``importer_type``.  ``importer_type`` is the type or class of a PEP 302
    "importer" (sys.path item handler), and ``namespace_handler`` is a callable
    with a signature like this::

        def namespace_handler(importer, path_entry, moduleName, module):
            # return a path_entry to use for child packages

    Namespace handlers are only called if the relevant importer object has
    already agreed that it can handle the relevant path item.  The handler
    should only return a subpath if the module ``__path__`` does not already
    contain an equivalent subpath.  Otherwise, it should return None.

    For an example namespace handler, see the source of the
    ``pkg_resources.file_ns_handler`` function, which is used for both zipfile
    importing and regular importing.


IResourceProvider
-----------------

``IResourceProvider`` is an abstract class that documents what methods are
required of objects returned by a ``provider_factory`` registered with
``register_loader_type()``.  ``IResourceProvider`` is a subclass of
``IMetadataProvider``, so objects that implement this interface must also
implement all of the `IMetadataProvider Methods`_ as well as the methods
shown here.  The ``manager`` argument to the methods below must be an object
that supports the full `ResourceManager API`_ documented above.

``get_resource_filename(manager, resource_name)``
    Return a true filesystem path for ``resource_name``, coordinating the
    extraction with ``manager``, if the resource must be unpacked to the
    filesystem.

``get_resource_stream(manager, resource_name)``
    Return a readable file-like object for ``resource_name``.

``get_resource_string(manager, resource_name)``
    Return a string containing the contents of ``resource_name``.

``has_resource(resource_name)``
    Does the package contain the named resource?

``resource_isdir(resource_name)``
    Is the named resource a directory?  Return a false value if the resource
    does not exist or is not a directory.

``resource_listdir(resource_name)``
    Return a list of the contents of the resource directory, ala
    ``os.listdir()``.  Requesting the contents of a non-existent directory may
    raise an exception.

Note, by the way, that your provider classes need not (and should not) subclass
``IResourceProvider`` or ``IMetadataProvider``!  These classes exist solely
for documentation purposes and do not provide any useful implementation code.
You may instead wish to subclass one of the `built-in resource providers`_.


Built-in Resource Providers
---------------------------

``pkg_resources`` includes several provider classes that are automatically used
where appropriate.  Their inheritance tree looks like this::

    NullProvider
        EggProvider
            DefaultProvider
                PathMetadata
            ZipProvider
                EggMetadata
        EmptyProvider
            FileMetadata


``NullProvider``
    This provider class is just an abstract base that provides for common
    provider behaviors (such as running scripts), given a definition for just
    a few abstract methods.

``EggProvider``
    This provider class adds in some egg-specific features that are common
    to zipped and unzipped eggs.

``DefaultProvider``
    This provider class is used for unpacked eggs and "plain old Python"
    filesystem modules.

``ZipProvider``
    This provider class is used for all zipped modules, whether they are eggs
    or not.

``EmptyProvider``
    This provider class always returns answers consistent with a provider that
    has no metadata or resources.  ``Distribution`` objects created without
    a ``metadata`` argument use an instance of this provider class instead.
    Since all ``EmptyProvider`` instances are equivalent, there is no need
    to have more than one instance.  ``pkg_resources`` therefore creates a
    global instance of this class under the name ``empty_provider``, and you
    may use it if you have need of an ``EmptyProvider`` instance.

``PathMetadata(path, egg_info)``
    Create an ``IResourceProvider`` for a filesystem-based distribution, where
    ``path`` is the filesystem location of the importable modules, and ``egg_info``
    is the filesystem location of the distribution's metadata directory.
    ``egg_info`` should usually be the ``EGG-INFO`` subdirectory of ``path`` for an
    "unpacked egg", and a ``ProjectName.egg-info`` subdirectory of ``path`` for
    a "development egg".  However, other uses are possible for custom purposes.

``EggMetadata(zipimporter)``
    Create an ``IResourceProvider`` for a zipfile-based distribution.  The
    ``zipimporter`` should be a ``zipimport.zipimporter`` instance, and may
    represent a "basket" (a zipfile containing multiple ".egg" subdirectories)
    a specific egg *within* a basket, or a zipfile egg (where the zipfile
    itself is a ".egg").  It can also be a combination, such as a zipfile egg
    that also contains other eggs.

``FileMetadata(path_to_pkg_info)``
    Create an ``IResourceProvider`` that provides exactly one metadata
    resource: ``PKG-INFO``.  The supplied path should be a distutils PKG-INFO
    file.  This is basically the same as an ``EmptyProvider``, except that
    requests for ``PKG-INFO`` will be answered using the contents of the
    designated file.  (This provider is used to wrap ``.egg-info`` files
    installed by vendor-supplied system packages.)


Utility Functions
=================

In addition to its high-level APIs, ``pkg_resources`` also includes several
generally-useful utility routines.  These routines are used to implement the
high-level APIs, but can also be quite useful by themselves.


Parsing Utilities
-----------------

``parse_version(version)``
    Parsed a project's version string as defined by PEP 440. The returned
    value will be an object that represents the version. These objects may
    be compared to each other and sorted. The sorting algorithm is as defined
    by PEP 440 with the addition that any version which is not a valid PEP 440
    version will be considered less than any valid PEP 440 version and the
    invalid versions will continue sorting using the original algorithm.

.. _yield_lines():

``yield_lines(strs)``
    Yield non-empty/non-comment lines from a string/unicode or a possibly-
    nested sequence thereof.  If ``strs`` is an instance of ``basestring``, it
    is split into lines, and each non-blank, non-comment line is yielded after
    stripping leading and trailing whitespace.  (Lines whose first non-blank
    character is ``#`` are considered comment lines.)

    If ``strs`` is not an instance of ``basestring``, it is iterated over, and
    each item is passed recursively to ``yield_lines()``, so that an arbitrarily
    nested sequence of strings, or sequences of sequences of strings can be
    flattened out to the lines contained therein.  So for example, passing
    a file object or a list of strings to ``yield_lines`` will both work.
    (Note that between each string in a sequence of strings there is assumed to
    be an implicit line break, so lines cannot bridge two strings in a
    sequence.)

    This routine is used extensively by ``pkg_resources`` to parse metadata
    and file formats of various kinds, and most other ``pkg_resources``
    parsing functions that yield multiple values will use it to break up their
    input.  However, this routine is idempotent, so calling ``yield_lines()``
    on the output of another call to ``yield_lines()`` is completely harmless.

``split_sections(strs)``
    Split a string (or possibly-nested iterable thereof), yielding ``(section,
    content)`` pairs found using an ``.ini``-like syntax.  Each ``section`` is
    a whitespace-stripped version of the section name ("``[section]``")
    and each ``content`` is a list of stripped lines excluding blank lines and
    comment-only lines.  If there are any non-blank, non-comment lines before
    the first section header, they're yielded in a first ``section`` of
    ``None``.

    This routine uses ``yield_lines()`` as its front end, so you can pass in
    anything that ``yield_lines()`` accepts, such as an open text file, string,
    or sequence of strings.  ``ValueError`` is raised if a malformed section
    header is found (i.e. a line starting with ``[`` but not ending with
    ``]``).

    Note that this simplistic parser assumes that any line whose first nonblank
    character is ``[`` is a section heading, so it can't support .ini format
    variations that allow ``[`` as the first nonblank character on other lines.

``safe_name(name)``
    Return a "safe" form of a project's name, suitable for use in a
    ``Requirement`` string, as a distribution name, or a PyPI project name.
    All non-alphanumeric runs are condensed to single "-" characters, such that
    a name like "The $$$ Tree" becomes "The-Tree".  Note that if you are
    generating a filename from this value you should combine it with a call to
    ``to_filename()`` so all dashes ("-") are replaced by underscores ("_").
    See ``to_filename()``.

``safe_version(version)``
    This will return the normalized form of any PEP 440 version. If the version
    string is not PEP 440 compatible, this function behaves similar to
    ``safe_name()`` except that spaces in the input become dots, and dots are
    allowed to exist in the output.  As with ``safe_name()``, if you are
    generating a filename from this you should replace any "-" characters in
    the output with underscores.

``safe_extra(extra)``
    Return a "safe" form of an extra's name, suitable for use in a requirement
    string or a setup script's ``extras_require`` keyword.  This routine is
    similar to ``safe_name()`` except that non-alphanumeric runs are replaced
    by a single underbar (``_``), and the result is lowercased.

``to_filename(name_or_version)``
    Escape a name or version string so it can be used in a dash-separated
    filename (or ``#egg=name-version`` tag) without ambiguity.  You
    should only pass in values that were returned by ``safe_name()`` or
    ``safe_version()``.


Platform Utilities
------------------

``get_build_platform()``
    Return this platform's identifier string.  For Windows, the return value
    is ``"win32"``, and for macOS it is a string of the form
    ``"macosx-10.4-ppc"``.  All other platforms return the same uname-based
    string that the ``distutils.util.get_platform()`` function returns.
    This string is the minimum platform version required by distributions built
    on the local machine.  (Backward compatibility note: setuptools versions
    prior to 0.6b1 called this function ``get_platform()``, and the function is
    still available under that name for backward compatibility reasons.)

``get_supported_platform()`` (New in 0.6b1)
    This is the similar to ``get_build_platform()``, but is the maximum
    platform version that the local machine supports.  You will usually want
    to use this value as the ``provided`` argument to the
    ``compatible_platforms()`` function.

``compatible_platforms(provided, required)``
    Return true if a distribution built on the ``provided`` platform may be used
    on the ``required`` platform.  If either platform value is ``None``, it is
    considered a wildcard, and the platforms are therefore compatible.
    Likewise, if the platform strings are equal, they're also considered
    compatible, and ``True`` is returned.  Currently, the only non-equal
    platform strings that are considered compatible are macOS platform
    strings with the same hardware type (e.g. ``ppc``) and major version
    (e.g. ``10``) with the ``provided`` platform's minor version being less than
    or equal to the ``required`` platform's minor version.

``get_default_cache()``
    Determine the default cache location for extracting resources from zipped
    eggs.  This routine returns the ``PYTHON_EGG_CACHE`` environment variable,
    if set.  Otherwise, on Windows, it returns a "Python-Eggs" subdirectory of
    the user's "Application Data" directory.  On all other systems, it returns
    ``os.path.expanduser("~/.python-eggs")`` if ``PYTHON_EGG_CACHE`` is not
    set.


PEP 302 Utilities
-----------------

``get_importer(path_item)``
    A deprecated alias for ``pkgutil.get_importer()``


File/Path Utilities
-------------------

``ensure_directory(path)``
    Ensure that the parent directory (``os.path.dirname``) of ``path`` actually
    exists, using ``os.makedirs()`` if necessary.

``normalize_path(path)``
    Return a "normalized" version of ``path``, such that two paths represent
    the same filesystem location if they have equal ``normalized_path()``
    values.  Specifically, this is a shortcut for calling ``os.path.realpath``
    and ``os.path.normcase`` on ``path``.  Unfortunately, on certain platforms
    (notably Cygwin and macOS) the ``normcase`` function does not accurately
    reflect the platform's case-sensitivity, so there is always the possibility
    of two apparently-different paths being equal on such platforms.

History
-------

0.6c9
 * Fix ``resource_listdir('')`` always returning an empty list for zipped eggs.

0.6c7
 * Fix package precedence problem where single-version eggs installed in
   ``site-packages`` would take precedence over ``.egg`` files (or directories)
   installed in ``site-packages``.

0.6c6
 * Fix extracted C extensions not having executable permissions under Cygwin.

 * Allow ``.egg-link`` files to contain relative paths.

 * Fix cache dir defaults on Windows when multiple environment vars are needed
   to construct a path.

0.6c4
 * Fix "dev" versions being considered newer than release candidates.

0.6c3
 * Python 2.5 compatibility fixes.

0.6c2
 * Fix a problem with eggs specified directly on ``PYTHONPATH`` on
   case-insensitive filesystems possibly not showing up in the default
   working set, due to differing normalizations of ``sys.path`` entries.

0.6b3
 * Fixed a duplicate path insertion problem on case-insensitive filesystems.

0.6b1
 * Split ``get_platform()`` into ``get_supported_platform()`` and
   ``get_build_platform()`` to work around a Mac versioning problem that caused
   the behavior of ``compatible_platforms()`` to be platform specific.

 * Fix entry point parsing when a standalone module name has whitespace
   between it and the extras.

0.6a11
 * Added ``ExtractionError`` and ``ResourceManager.extraction_error()`` so that
   cache permission problems get a more user-friendly explanation of the
   problem, and so that programs can catch and handle extraction errors if they
   need to.

0.6a10
 * Added the ``extras`` attribute to ``Distribution``, the ``find_plugins()``
   method to ``WorkingSet``, and the ``__add__()`` and ``__iadd__()`` methods
   to ``Environment``.

 * ``safe_name()`` now allows dots in project names.

 * There is a new ``to_filename()`` function that escapes project names and
   versions for safe use in constructing egg filenames from a Distribution
   object's metadata.

 * Added ``Distribution.clone()`` method, and keyword argument support to other
   ``Distribution`` constructors.

 * Added the ``DEVELOP_DIST`` precedence, and automatically assign it to
   eggs using ``.egg-info`` format.

0.6a9
 * Don't raise an error when an invalid (unfinished) distribution is found
   unless absolutely necessary.  Warn about skipping invalid/unfinished eggs
   when building an Environment.

 * Added support for ``.egg-info`` files or directories with version/platform
   information embedded in the filename, so that system packagers have the
   option of including ``PKG-INFO`` files to indicate the presence of a
   system-installed egg, without needing to use ``.egg`` directories, zipfiles,
   or ``.pth`` manipulation.

 * Changed ``parse_version()`` to remove dashes before pre-release tags, so
   that ``0.2-rc1`` is considered an *older* version than ``0.2``, and is equal
   to ``0.2rc1``.  The idea that a dash *always* meant a post-release version
   was highly non-intuitive to setuptools users and Python developers, who
   seem to want to use ``-rc`` version numbers a lot.

0.6a8
 * Fixed a problem with ``WorkingSet.resolve()`` that prevented version
   conflicts from being detected at runtime.

 * Improved runtime conflict warning message to identify a line in the user's
   program, rather than flagging the ``warn()`` call in ``pkg_resources``.

 * Avoid giving runtime conflict warnings for namespace packages, even if they
   were declared by a different package than the one currently being activated.

 * Fix path insertion algorithm for case-insensitive filesystems.

 * Fixed a problem with nested namespace packages (e.g. ``peak.util``) not
   being set as an attribute of their parent package.

0.6a6
 * Activated distributions are now inserted in ``sys.path`` (and the working
   set) just before the directory that contains them, instead of at the end.
   This allows e.g. eggs in ``site-packages`` to override unmanaged modules in
   the same location, and allows eggs found earlier on ``sys.path`` to override
   ones found later.

 * When a distribution is activated, it now checks whether any contained
   non-namespace modules have already been imported and issues a warning if
   a conflicting module has already been imported.

 * Changed dependency processing so that it's breadth-first, allowing a
   depender's preferences to override those of a dependee, to prevent conflicts
   when a lower version is acceptable to the dependee, but not the depender.

 * Fixed a problem extracting zipped files on Windows, when the egg in question
   has had changed contents but still has the same version number.

0.6a4
 * Fix a bug in ``WorkingSet.resolve()`` that was introduced in 0.6a3.

0.6a3
 * Added ``safe_extra()`` parsing utility routine, and use it for Requirement,
   EntryPoint, and Distribution objects' extras handling.

0.6a1
 * Enhanced performance of ``require()`` and related operations when all
   requirements are already in the working set, and enhanced performance of
   directory scanning for distributions.

 * Fixed some problems using ``pkg_resources`` w/PEP 302 loaders other than
   ``zipimport``, and the previously-broken "eager resource" support.

 * Fixed ``pkg_resources.resource_exists()`` not working correctly, along with
   some other resource API bugs.

 * Many API changes and enhancements:

   * Added ``EntryPoint``, ``get_entry_map``, ``load_entry_point``, and
     ``get_entry_info`` APIs for dynamic plugin discovery.

   * ``list_resources`` is now ``resource_listdir`` (and it actually works)

   * Resource API functions like ``resource_string()`` that accepted a package
     name and resource name, will now also accept a ``Requirement`` object in
     place of the package name (to allow access to non-package data files in
     an egg).

   * ``get_provider()`` will now accept a ``Requirement`` instance or a module
     name.  If it is given a ``Requirement``, it will return a corresponding
     ``Distribution`` (by calling ``require()`` if a suitable distribution
     isn't already in the working set), rather than returning a metadata and
     resource provider for a specific module.  (The difference is in how
     resource paths are interpreted; supplying a module name means resources
     path will be module-relative, rather than relative to the distribution's
     root.)

   * ``Distribution`` objects now implement the ``IResourceProvider`` and
     ``IMetadataProvider`` interfaces, so you don't need to reference the (no
     longer available) ``metadata`` attribute to get at these interfaces.

   * ``Distribution`` and ``Requirement`` both have a ``project_name``
     attribute for the project name they refer to.  (Previously these were
     ``name`` and ``distname`` attributes.)

   * The ``path`` attribute of ``Distribution`` objects is now ``location``,
     because it isn't necessarily a filesystem path (and hasn't been for some
     time now).  The ``location`` of ``Distribution`` objects in the filesystem
     should always be normalized using ``pkg_resources.normalize_path()``; all
     of the setuptools' code that generates distributions from the filesystem
     (including ``Distribution.from_filename()``) ensure this invariant, but if
     you use a more generic API like ``Distribution()`` or
     ``Distribution.from_location()`` you should take care that you don't
     create a distribution with an un-normalized filesystem path.

   * ``Distribution`` objects now have an ``as_requirement()`` method that
     returns a ``Requirement`` for the distribution's project name and version.

   * Distribution objects no longer have an ``installed_on()`` method, and the
     ``install_on()`` method is now ``activate()`` (but may go away altogether
     soon).  The ``depends()`` method has also been renamed to ``requires()``,
     and ``InvalidOption`` is now ``UnknownExtra``.

   * ``find_distributions()`` now takes an additional argument called ``only``,
     that tells it to only yield distributions whose location is the passed-in
     path.  (It defaults to False, so that the default behavior is unchanged.)

   * ``AvailableDistributions`` is now called ``Environment``, and the
     ``get()``, ``__len__()``, and ``__contains__()`` methods were removed,
     because they weren't particularly useful.  ``__getitem__()`` no longer
     raises ``KeyError``; it just returns an empty list if there are no
     distributions for the named project.

   * The ``resolve()`` method of ``Environment`` is now a method of
     ``WorkingSet`` instead, and the ``best_match()`` method now uses a working
     set instead of a path list as its second argument.

   * There is a new ``pkg_resources.add_activation_listener()`` API that lets
     you register a callback for notifications about distributions added to
     ``sys.path`` (including the distributions already on it).  This is
     basically a hook for extensible applications and frameworks to be able to
     search for plugin metadata in distributions added at runtime.

0.5a13
 * Fixed a bug in resource extraction from nested packages in a zipped egg.

0.5a12
 * Updated extraction/cache mechanism for zipped resources to avoid inter-
   process and inter-thread races during extraction.  The default cache
   location can now be set via the ``PYTHON_EGGS_CACHE`` environment variable,
   and the default Windows cache is now a ``Python-Eggs`` subdirectory of the
   current user's "Application Data" directory, if the ``PYTHON_EGGS_CACHE``
   variable isn't set.

0.5a10
 * Fix a problem with ``pkg_resources`` being confused by non-existent eggs on
   ``sys.path`` (e.g. if a user deletes an egg without removing it from the
   ``easy-install.pth`` file).

 * Fix a problem with "basket" support in ``pkg_resources``, where egg-finding
   never actually went inside ``.egg`` files.

 * Made ``pkg_resources`` import the module you request resources from, if it's
   not already imported.

0.5a4
 * ``pkg_resources.AvailableDistributions.resolve()`` and related methods now
   accept an ``installer`` argument: a callable taking one argument, a
   ``Requirement`` instance.  The callable must return a ``Distribution``
   object, or ``None`` if no distribution is found.  This feature is used by
   EasyInstall to resolve dependencies by recursively invoking itself.

0.4a4
 * Fix problems with ``resource_listdir()``, ``resource_isdir()`` and resource
   directory extraction for zipped eggs.

0.4a3
 * Fixed scripts not being able to see a ``__file__`` variable in ``__main__``

 * Fixed a problem with ``resource_isdir()`` implementation that was introduced
   in 0.4a2.

0.4a1
 * Fixed a bug in requirements processing for exact versions (i.e. ``==`` and
   ``!=``) when only one condition was included.

 * Added ``safe_name()`` and ``safe_version()`` APIs to clean up handling of
   arbitrary distribution names and versions found on PyPI.

0.3a4
 * ``pkg_resources`` now supports resource directories, not just the resources
   in them.  In particular, there are ``resource_listdir()`` and
   ``resource_isdir()`` APIs.

 * ``pkg_resources`` now supports "egg baskets" -- .egg zipfiles which contain
   multiple distributions in subdirectories whose names end with ``.egg``.
   Having such a "basket" in a directory on ``sys.path`` is equivalent to
   having the individual eggs in that directory, but the contained eggs can
   be individually added (or not) to ``sys.path``.  Currently, however, there
   is no automated way to create baskets.

 * Namespace package manipulation is now protected by the Python import lock.

0.3a1
 * Initial release.
