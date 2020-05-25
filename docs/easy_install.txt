============
Easy Install
============

.. warning::
    Easy Install is deprecated. Do not use it. Instead use pip. If
    you think you need Easy Install, please reach out to the PyPA
    team (a ticket to pip or setuptools is fine), describing your
    use-case.

Easy Install is a python module (``easy_install``) bundled with ``setuptools``
that lets you automatically download, build, install, and manage Python
packages.

Please share your experiences with us! If you encounter difficulty installing
a package, please contact us via the `distutils mailing list
<http://mail.python.org/pipermail/distutils-sig/>`_.  (Note: please DO NOT send
private email directly to the author of setuptools; it will be discarded.  The
mailing list is a searchable archive of previously-asked and answered
questions; you should begin your research there before reporting something as a
bug -- and then do so via list discussion first.)

(Also, if you'd like to learn about how you can use ``setuptools`` to make your
own packages work better with EasyInstall, or provide EasyInstall-like features
without requiring your users to use EasyInstall directly, you'll probably want
to check out the full documentation as well.)

.. contents:: **Table of Contents**


Using "Easy Install"
====================


.. _installation instructions:

Installing "Easy Install"
-------------------------

Please see the `setuptools PyPI page <https://pypi.org/project/setuptools/>`_
for download links and basic installation instructions for each of the
supported platforms.

You will need at least Python 3.5 or 2.7.  An ``easy_install`` script will be
installed in the normal location for Python scripts on your platform.

Note that the instructions on the setuptools PyPI page assume that you are
are installing to Python's primary ``site-packages`` directory.  If this is
not the case, you should consult the section below on `Custom Installation
Locations`_ before installing.  (And, on Windows, you should not use the
``.exe`` installer when installing to an alternate location.)

Note that ``easy_install`` normally works by downloading files from the
internet.  If you are behind an NTLM-based firewall that prevents Python
programs from accessing the net directly, you may wish to first install and use
the `APS proxy server <http://ntlmaps.sf.net/>`_, which lets you get past such
firewalls in the same way that your web browser(s) do.

(Alternately, if you do not wish easy_install to actually download anything, you
can restrict it from doing so with the ``--allow-hosts`` option; see the
sections on `restricting downloads with --allow-hosts`_ and `command-line
options`_ for more details.)


Troubleshooting
~~~~~~~~~~~~~~~

If EasyInstall/setuptools appears to install correctly, and you can run the
``easy_install`` command but it fails with an ``ImportError``, the most likely
cause is that you installed to a location other than ``site-packages``,
without taking any of the steps described in the `Custom Installation
Locations`_ section below.  Please see that section and follow the steps to
make sure that your custom location will work correctly.  Then re-install.

Similarly, if you can run ``easy_install``, and it appears to be installing
packages, but then you can't import them, the most likely issue is that you
installed EasyInstall correctly but are using it to install packages to a
non-standard location that hasn't been properly prepared.  Again, see the
section on `Custom Installation Locations`_ for more details.


Windows Notes
~~~~~~~~~~~~~

Installing setuptools will provide an ``easy_install`` command according to
the techniques described in `Executables and Launchers`_. If the
``easy_install`` command is not available after installation, that section
provides details on how to configure Windows to make the commands available.


Downloading and Installing a Package
------------------------------------

For basic use of ``easy_install``, you need only supply the filename or URL of
a source distribution or .egg file (`Python Egg`__).

__ http://peak.telecommunity.com/DevCenter/PythonEggs

**Example 1**. Install a package by name, searching PyPI for the latest
version, and automatically downloading, building, and installing it::

    easy_install SQLObject

**Example 2**. Install or upgrade a package by name and version by finding
links on a given "download page"::

    easy_install -f http://pythonpaste.org/package_index.html SQLObject

**Example 3**. Download a source distribution from a specified URL,
automatically building and installing it::

    easy_install http://example.com/path/to/MyPackage-1.2.3.tgz

**Example 4**. Install an already-downloaded .egg file::

    easy_install /my_downloads/OtherPackage-3.2.1-py2.3.egg

**Example 5**.  Upgrade an already-installed package to the latest version
listed on PyPI::

    easy_install --upgrade PyProtocols

**Example 6**.  Install a source distribution that's already downloaded and
extracted in the current directory (New in 0.5a9)::

    easy_install .

**Example 7**.  (New in 0.6a1) Find a source distribution or Subversion
checkout URL for a package, and extract it or check it out to
``~/projects/sqlobject`` (the name will always be in all-lowercase), where it
can be examined or edited.  (The package will not be installed, but it can
easily be installed with ``easy_install ~/projects/sqlobject``.  See `Editing
and Viewing Source Packages`_ below for more info.)::

    easy_install --editable --build-directory ~/projects SQLObject

**Example 7**. (New in 0.6.11) Install a distribution within your home dir::

    easy_install --user SQLAlchemy

Easy Install accepts URLs, filenames, PyPI package names (i.e., ``distutils``
"distribution" names), and package+version specifiers.  In each case, it will
attempt to locate the latest available version that meets your criteria.

When downloading or processing downloaded files, Easy Install recognizes
distutils source distribution files with extensions of .tgz, .tar, .tar.gz,
.tar.bz2, or .zip.  And of course it handles already-built .egg
distributions as well as ``.win32.exe`` installers built using distutils.

By default, packages are installed to the running Python installation's
``site-packages`` directory, unless you provide the ``-d`` or ``--install-dir``
option to specify an alternative directory, or specify an alternate location
using distutils configuration files.  (See `Configuration Files`_, below.)

By default, any scripts included with the package are installed to the running
Python installation's standard script installation location.  However, if you
specify an installation directory via the command line or a config file, then
the default directory for installing scripts will be the same as the package
installation directory, to ensure that the script will have access to the
installed package.  You can override this using the ``-s`` or ``--script-dir``
option.

Installed packages are added to an ``easy-install.pth`` file in the install
directory, so that Python will always use the most-recently-installed version
of the package.  If you would like to be able to select which version to use at
runtime, you should use the ``-m`` or ``--multi-version`` option.


Upgrading a Package
-------------------

You don't need to do anything special to upgrade a package: just install the
new version, either by requesting a specific version, e.g.::

    easy_install "SomePackage==2.0"

a version greater than the one you have now::

    easy_install "SomePackage>2.0"

using the upgrade flag, to find the latest available version on PyPI::

    easy_install --upgrade SomePackage

or by using a download page, direct download URL, or package filename::

    easy_install -f http://example.com/downloads ExamplePackage

    easy_install http://example.com/downloads/ExamplePackage-2.0-py2.4.egg

    easy_install my_downloads/ExamplePackage-2.0.tgz

If you're using ``-m`` or ``--multi-version`` , using the ``require()``
function at runtime automatically selects the newest installed version of a
package that meets your version criteria.  So, installing a newer version is
the only step needed to upgrade such packages.

If you're installing to a directory on PYTHONPATH, or a configured "site"
directory (and not using ``-m``), installing a package automatically replaces
any previous version in the ``easy-install.pth`` file, so that Python will
import the most-recently installed version by default.  So, again, installing
the newer version is the only upgrade step needed.

If you haven't suppressed script installation (using ``--exclude-scripts`` or
``-x``), then the upgraded version's scripts will be installed, and they will
be automatically patched to ``require()`` the corresponding version of the
package, so that you can use them even if they are installed in multi-version
mode.

``easy_install`` never actually deletes packages (unless you're installing a
package with the same name and version number as an existing package), so if
you want to get rid of older versions of a package, please see `Uninstalling
Packages`_, below.


Changing the Active Version
---------------------------

If you've upgraded a package, but need to revert to a previously-installed
version, you can do so like this::

    easy_install PackageName==1.2.3

Where ``1.2.3`` is replaced by the exact version number you wish to switch to.
If a package matching the requested name and version is not already installed
in a directory on ``sys.path``, it will be located via PyPI and installed.

If you'd like to switch to the latest installed version of ``PackageName``, you
can do so like this::

    easy_install PackageName

This will activate the latest installed version.  (Note: if you have set any
``find_links`` via distutils configuration files, those download pages will be
checked for the latest available version of the package, and it will be
downloaded and installed if it is newer than your current version.)

Note that changing the active version of a package will install the newly
active version's scripts, unless the ``--exclude-scripts`` or ``-x`` option is
specified.


Uninstalling Packages
---------------------

If you have replaced a package with another version, then you can just delete
the package(s) you don't need by deleting the PackageName-versioninfo.egg file
or directory (found in the installation directory).

If you want to delete the currently installed version of a package (or all
versions of a package), you should first run::

    easy_install -m PackageName

This will ensure that Python doesn't continue to search for a package you're
planning to remove. After you've done this, you can safely delete the .egg
files or directories, along with any scripts you wish to remove.


Managing Scripts
----------------

Whenever you install, upgrade, or change versions of a package, EasyInstall
automatically installs the scripts for the selected package version, unless
you tell it not to with ``-x`` or ``--exclude-scripts``.  If any scripts in
the script directory have the same name, they are overwritten.

Thus, you do not normally need to manually delete scripts for older versions of
a package, unless the newer version of the package does not include a script
of the same name.  However, if you are completely uninstalling a package, you
may wish to manually delete its scripts.

EasyInstall's default behavior means that you can normally only run scripts
from one version of a package at a time.  If you want to keep multiple versions
of a script available, however, you can simply use the ``--multi-version`` or
``-m`` option, and rename the scripts that EasyInstall creates.  This works
because EasyInstall installs scripts as short code stubs that ``require()`` the
matching version of the package the script came from, so renaming the script
has no effect on what it executes.

For example, suppose you want to use two versions of the ``rst2html`` tool
provided by the `docutils <http://docutils.sf.net/>`_ package.  You might
first install one version::

    easy_install -m docutils==0.3.9

then rename the ``rst2html.py`` to ``r2h_039``, and install another version::

    easy_install -m docutils==0.3.10

This will create another ``rst2html.py`` script, this one using docutils
version 0.3.10 instead of 0.3.9.  You now have two scripts, each using a
different version of the package.  (Notice that we used ``-m`` for both
installations, so that Python won't lock us out of using anything but the most
recently-installed version of the package.)


Executables and Launchers
-------------------------

On Unix systems, scripts are installed with as natural files with a "#!"
header and no extension and they launch under the Python version indicated in
the header.

On Windows, there is no mechanism to "execute" files without extensions, so
EasyInstall provides two techniques to mirror the Unix behavior. The behavior
is indicated by the SETUPTOOLS_LAUNCHER environment variable, which may be
"executable" (default) or "natural".

Regardless of the technique used, the script(s) will be installed to a Scripts
directory (by default in the Python installation directory). It is recommended
for EasyInstall that you ensure this directory is in the PATH environment
variable. The easiest way to ensure the Scripts directory is in the PATH is
to run ``Tools\Scripts\win_add2path.py`` from the Python directory.

Note that instead of changing your ``PATH`` to include the Python scripts
directory, you can also retarget the installation location for scripts so they
go on a directory that's already on the ``PATH``.  For more information see
`Command-Line Options`_ and `Configuration Files`_.  During installation,
pass command line options (such as ``--script-dir``) to control where
scripts will be installed.


Windows Executable Launcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the "executable" launcher is used, EasyInstall will create a '.exe'
launcher of the same name beside each installed script (including
``easy_install`` itself). These small .exe files launch the script of the
same name using the Python version indicated in the '#!' header.

This behavior is currently default. To force
the use of executable launchers, set ``SETUPTOOLS_LAUNCHER`` to "executable".

Natural Script Launcher
~~~~~~~~~~~~~~~~~~~~~~~

EasyInstall also supports deferring to an external launcher such as
`pylauncher <https://bitbucket.org/pypa/pylauncher>`_ for launching scripts.
Enable this experimental functionality by setting the
``SETUPTOOLS_LAUNCHER`` environment variable to "natural". EasyInstall will
then install scripts as simple
scripts with a .pya (or .pyw) extension appended. If these extensions are
associated with the pylauncher and listed in the PATHEXT environment variable,
these scripts can then be invoked simply and directly just like any other
executable. This behavior may become default in a future version.

EasyInstall uses the .pya extension instead of simply
the typical '.py' extension. This distinct extension is necessary to prevent
Python
from treating the scripts as importable modules (where name conflicts exist).
Current releases of pylauncher do not yet associate with .pya files by
default, but future versions should do so.


Tips & Techniques
-----------------

Multiple Python Versions
~~~~~~~~~~~~~~~~~~~~~~~~

EasyInstall installs itself under two names:
``easy_install`` and ``easy_install-N.N``, where ``N.N`` is the Python version
used to install it.  Thus, if you install EasyInstall for both Python 3.2 and
2.7, you can use the ``easy_install-3.2`` or ``easy_install-2.7`` scripts to
install packages for the respective Python version.

Setuptools also supplies easy_install as a runnable module which may be
invoked using ``python -m easy_install`` for any Python with Setuptools
installed.

Restricting Downloads with ``--allow-hosts``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use the ``--allow-hosts`` (``-H``) option to restrict what domains
EasyInstall will look for links and downloads on.  ``--allow-hosts=None``
prevents downloading altogether.  You can also use wildcards, for example
to restrict downloading to hosts in your own intranet.  See the section below
on `Command-Line Options`_ for more details on the ``--allow-hosts`` option.

By default, there are no host restrictions in effect, but you can change this
default by editing the appropriate `configuration files`_ and adding:

.. code-block:: ini

    [easy_install]
    allow_hosts = *.myintranet.example.com,*.python.org

The above example would then allow downloads only from hosts in the
``python.org`` and ``myintranet.example.com`` domains, unless overridden on the
command line.


Installing on Un-networked Machines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Just copy the eggs or source packages you need to a directory on the target
machine, then use the ``-f`` or ``--find-links`` option to specify that
directory's location.  For example::

    easy_install -H None -f somedir SomePackage

will attempt to install SomePackage using only eggs and source packages found
in ``somedir`` and disallowing all remote access.  You should of course make
sure you have all of SomePackage's dependencies available in somedir.

If you have another machine of the same operating system and library versions
(or if the packages aren't platform-specific), you can create the directory of
eggs using a command like this::

    easy_install -zmaxd somedir SomePackage

This will tell EasyInstall to put zipped eggs or source packages for
SomePackage and all its dependencies into ``somedir``, without creating any
scripts or .pth files.  You can then copy the contents of ``somedir`` to the
target machine.  (``-z`` means zipped eggs, ``-m`` means multi-version, which
prevents .pth files from being used, ``-a`` means to copy all the eggs needed,
even if they're installed elsewhere on the machine, and ``-d`` indicates the
directory to place the eggs in.)

You can also build the eggs from local development packages that were installed
with the ``setup.py develop`` command, by including the ``-l`` option, e.g.::

    easy_install -zmaxld somedir SomePackage

This will use locally-available source distributions to build the eggs.


Packaging Others' Projects As Eggs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Need to distribute a package that isn't published in egg form?  You can use
EasyInstall to build eggs for a project.  You'll want to use the ``--zip-ok``,
``--exclude-scripts``, and possibly ``--no-deps`` options (``-z``, ``-x`` and
``-N``, respectively).  Use ``-d`` or ``--install-dir`` to specify the location
where you'd like the eggs placed.  By placing them in a directory that is
published to the web, you can then make the eggs available for download, either
in an intranet or to the internet at large.

If someone distributes a package in the form of a single ``.py`` file, you can
wrap it in an egg by tacking an ``#egg=name-version`` suffix on the file's URL.
So, something like this::

    easy_install -f "http://some.example.com/downloads/foo.py#egg=foo-1.0" foo

will install the package as an egg, and this::

    easy_install -zmaxd. \
        -f "http://some.example.com/downloads/foo.py#egg=foo-1.0" foo

will create a ``.egg`` file in the current directory.


Creating your own Package Index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to local directories and the Python Package Index, EasyInstall can
find download links on most any web page whose URL is given to the ``-f``
(``--find-links``) option.  In the simplest case, you can simply have a web
page with links to eggs or Python source packages, even an automatically
generated directory listing (such as the Apache web server provides).

If you are setting up an intranet site for package downloads, you may want to
configure the target machines to use your download site by default, adding
something like this to their `configuration files`_:

.. code-block:: ini

    [easy_install]
    find_links = http://mypackages.example.com/somedir/
                 http://turbogears.org/download/
                 http://peak.telecommunity.com/dist/

As you can see, you can list multiple URLs separated by whitespace, continuing
on multiple lines if necessary (as long as the subsequent lines are indented.

If you are more ambitious, you can also create an entirely custom package index
or PyPI mirror.  See the ``--index-url`` option under `Command-Line Options`_,
below, and also the section on `Package Index "API"`_.


Password-Protected Sites
------------------------

If a site you want to download from is password-protected using HTTP "Basic"
authentication, you can specify your credentials in the URL, like so::

    http://some_userid:some_password@some.example.com/some_path/

You can do this with both index page URLs and direct download URLs.  As long
as any HTML pages read by easy_install use *relative* links to point to the
downloads, the same user ID and password will be used to do the downloading.

Using .pypirc Credentials
-------------------------

In additional to supplying credentials in the URL, ``easy_install`` will also
honor credentials if present in the .pypirc file. Teams maintaining a private
repository of packages may already have defined access credentials for
uploading packages according to the distutils documentation. ``easy_install``
will attempt to honor those if present. Refer to the distutils documentation
for Python 2.5 or later for details on the syntax.

Controlling Build Options
~~~~~~~~~~~~~~~~~~~~~~~~~

EasyInstall respects standard distutils `Configuration Files`_, so you can use
them to configure build options for packages that it installs from source.  For
example, if you are on Windows using the MinGW compiler, you can configure the
default compiler by putting something like this:

.. code-block:: ini

    [build]
    compiler = mingw32

into the appropriate distutils configuration file.  In fact, since this is just
normal distutils configuration, it will affect any builds using that config
file, not just ones done by EasyInstall.  For example, if you add those lines
to ``distutils.cfg`` in the ``distutils`` package directory, it will be the
default compiler for *all* packages you build.  See `Configuration Files`_
below for a list of the standard configuration file locations, and links to
more documentation on using distutils configuration files.


Editing and Viewing Source Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes a package's source distribution  contains additional documentation,
examples, configuration files, etc., that are not part of its actual code.  If
you want to be able to examine these files, you can use the ``--editable``
option to EasyInstall, and EasyInstall will look for a source distribution
or Subversion URL for the package, then download and extract it or check it out
as a subdirectory of the ``--build-directory`` you specify.  If you then wish
to install the package after editing or configuring it, you can do so by
rerunning EasyInstall with that directory as the target.

Note that using ``--editable`` stops EasyInstall from actually building or
installing the package; it just finds, obtains, and possibly unpacks it for
you.  This allows you to make changes to the package if necessary, and to
either install it in development mode using ``setup.py develop`` (if the
package uses setuptools, that is), or by running ``easy_install projectdir``
(where ``projectdir`` is the subdirectory EasyInstall created for the
downloaded package.

In order to use ``--editable`` (``-e`` for short), you *must* also supply a
``--build-directory`` (``-b`` for short).  The project will be placed in a
subdirectory of the build directory.  The subdirectory will have the same
name as the project itself, but in all-lowercase.  If a file or directory of
that name already exists, EasyInstall will print an error message and exit.

Also, when using ``--editable``, you cannot use URLs or filenames as arguments.
You *must* specify project names (and optional version requirements) so that
EasyInstall knows what directory name(s) to create.  If you need to force
EasyInstall to use a particular URL or filename, you should specify it as a
``--find-links`` item (``-f`` for short), and then also specify
the project name, e.g.::

    easy_install -eb ~/projects \
     -fhttp://prdownloads.sourceforge.net/ctypes/ctypes-0.9.6.tar.gz?download \
     ctypes==0.9.6


Dealing with Installation Conflicts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(NOTE: As of 0.6a11, this section is obsolete; it is retained here only so that
people using older versions of EasyInstall can consult it.  As of version
0.6a11, installation conflicts are handled automatically without deleting the
old or system-installed packages, and without ignoring the issue.  Instead,
eggs are automatically shifted to the front of ``sys.path`` using special
code added to the ``easy-install.pth`` file.  So, if you are using version
0.6a11 or better of setuptools, you do not need to worry about conflicts,
and the following issues do not apply to you.)

EasyInstall installs distributions in a "managed" way, such that each
distribution can be independently activated or deactivated on ``sys.path``.
However, packages that were not installed by EasyInstall are "unmanaged",
in that they usually live all in one directory and cannot be independently
activated or deactivated.

As a result, if you are using EasyInstall to upgrade an existing package, or
to install a package with the same name as an existing package, EasyInstall
will warn you of the conflict.  (This is an improvement over ``setup.py
install``, because the ``distutils`` just install new packages on top of old
ones, possibly combining two unrelated packages or leaving behind modules that
have been deleted in the newer version of the package.)

EasyInstall will stop the installation if it detects a conflict
between an existing, "unmanaged" package, and a module or package in any of
the distributions you're installing.  It will display a list of all of the
existing files and directories that would need to be deleted for the new
package to be able to function correctly.  To proceed, you must manually
delete these conflicting files and directories and re-run EasyInstall.

Of course, once you've replaced all of your existing "unmanaged" packages with
versions managed by EasyInstall, you won't have any more conflicts to worry
about!


Compressed Installation
~~~~~~~~~~~~~~~~~~~~~~~

EasyInstall tries to install packages in zipped form, if it can.  Zipping
packages can improve Python's overall import performance if you're not using
the ``--multi-version`` option, because Python processes zipfile entries on
``sys.path`` much faster than it does directories.

As of version 0.5a9, EasyInstall analyzes packages to determine whether they
can be safely installed as a zipfile, and then acts on its analysis.  (Previous
versions would not install a package as a zipfile unless you used the
``--zip-ok`` option.)

The current analysis approach is fairly conservative; it currently looks for:

 * Any use of the ``__file__`` or ``__path__`` variables (which should be
   replaced with ``pkg_resources`` API calls)

 * Possible use of ``inspect`` functions that expect to manipulate source files
   (e.g. ``inspect.getsource()``)

 * Top-level modules that might be scripts used with ``python -m`` (Python 2.4)

If any of the above are found in the package being installed, EasyInstall will
assume that the package cannot be safely run from a zipfile, and unzip it to
a directory instead.  You can override this analysis with the ``-zip-ok`` flag,
which will tell EasyInstall to install the package as a zipfile anyway.  Or,
you can use the ``--always-unzip`` flag, in which case EasyInstall will always
unzip, even if its analysis says the package is safe to run as a zipfile.

Normally, however, it is simplest to let EasyInstall handle the determination
of whether to zip or unzip, and only specify overrides when needed to work
around a problem.  If you find you need to override EasyInstall's guesses, you
may want to contact the package author and the EasyInstall maintainers, so that
they can make appropriate changes in future versions.

(Note: If a package uses ``setuptools`` in its setup script, the package author
has the option to declare the package safe or unsafe for zipped usage via the
``zip_safe`` argument to ``setup()``.  If the package author makes such a
declaration, EasyInstall believes the package's author and does not perform its
own analysis.  However, your command-line option, if any, will still override
the package author's choice.)


Reference Manual
================

Configuration Files
-------------------

(New in 0.4a2)

You may specify default options for EasyInstall using the standard
distutils configuration files, under the command heading ``easy_install``.
EasyInstall will look first for a ``setup.cfg`` file in the current directory,
then a ``~/.pydistutils.cfg`` or ``$HOME\\pydistutils.cfg`` (on Unix-like OSes
and Windows, respectively), and finally a ``distutils.cfg`` file in the
``distutils`` package directory.  Here's a simple example:

.. code-block:: ini

    [easy_install]

    # set the default location to install packages
    install_dir = /home/me/lib/python

    # Notice that indentation can be used to continue an option
    # value; this is especially useful for the "--find-links"
    # option, which tells easy_install to use download links on
    # these pages before consulting PyPI:
    #
    find_links = http://sqlobject.org/
                 http://peak.telecommunity.com/dist/

In addition to accepting configuration for its own options under
``[easy_install]``, EasyInstall also respects defaults specified for other
distutils commands.  For example, if you don't set an ``install_dir`` for
``[easy_install]``, but *have* set an ``install_lib`` for the ``[install]``
command, this will become EasyInstall's default installation directory.  Thus,
if you are already using distutils configuration files to set default install
locations, build options, etc., EasyInstall will respect your existing settings
until and unless you override them explicitly in an ``[easy_install]`` section.

For more information, see also the current Python documentation on the `use and
location of distutils configuration files <https://docs.python.org/install/index.html#inst-config-files>`_.

Notice that ``easy_install`` will use the ``setup.cfg`` from the current
working directory only if it was triggered from ``setup.py`` through the
``install_requires`` option. The standalone command will not use that file.

Command-Line Options
--------------------

``--zip-ok, -z``
    Install all packages as zip files, even if they are marked as unsafe for
    running as a zipfile.  This can be useful when EasyInstall's analysis
    of a non-setuptools package is too conservative, but keep in mind that
    the package may not work correctly.  (Changed in 0.5a9; previously this
    option was required in order for zipped installation to happen at all.)

``--always-unzip, -Z``
    Don't install any packages as zip files, even if the packages are marked
    as safe for running as a zipfile.  This can be useful if a package does
    something unsafe, but not in a way that EasyInstall can easily detect.
    EasyInstall's default analysis is currently very conservative, however, so
    you should only use this option if you've had problems with a particular
    package, and *after* reporting the problem to the package's maintainer and
    to the EasyInstall maintainers.

    (Note: the ``-z/-Z`` options only affect the installation of newly-built
    or downloaded packages that are not already installed in the target
    directory; if you want to convert an existing installed version from
    zipped to unzipped or vice versa, you'll need to delete the existing
    version first, and re-run EasyInstall.)

``--multi-version, -m``
    "Multi-version" mode. Specifying this option prevents ``easy_install`` from
    adding an ``easy-install.pth`` entry for the package being installed, and
    if an entry for any version the package already exists, it will be removed
    upon successful installation. In multi-version mode, no specific version of
    the package is available for importing, unless you use
    ``pkg_resources.require()`` to put it on ``sys.path``. This can be as
    simple as::

        from pkg_resources import require
        require("SomePackage", "OtherPackage", "MyPackage")

    which will put the latest installed version of the specified packages on
    ``sys.path`` for you. (For more advanced uses, like selecting specific
    versions and enabling optional dependencies, see the ``pkg_resources`` API
    doc.)

    Changed in 0.6a10: this option is no longer silently enabled when
    installing to a non-PYTHONPATH, non-"site" directory.  You must always
    explicitly use this option if you want it to be active.

``--upgrade, -U``   (New in 0.5a4)
    By default, EasyInstall only searches online if a project/version
    requirement can't be met by distributions already installed
    on sys.path or the installation directory.  However, if you supply the
    ``--upgrade`` or ``-U`` flag, EasyInstall will always check the package
    index and ``--find-links`` URLs before selecting a version to install.  In
    this way, you can force EasyInstall to use the latest available version of
    any package it installs (subject to any version requirements that might
    exclude such later versions).

``--install-dir=DIR, -d DIR``
    Set the installation directory. It is up to you to ensure that this
    directory is on ``sys.path`` at runtime, and to use
    ``pkg_resources.require()`` to enable the installed package(s) that you
    need.

    (New in 0.4a2) If this option is not directly specified on the command line
    or in a distutils configuration file, the distutils default installation
    location is used.  Normally, this would be the ``site-packages`` directory,
    but if you are using distutils configuration files, setting things like
    ``prefix`` or ``install_lib``, then those settings are taken into
    account when computing the default installation directory, as is the
    ``--prefix`` option.

``--script-dir=DIR, -s DIR``
    Set the script installation directory.  If you don't supply this option
    (via the command line or a configuration file), but you *have* supplied
    an ``--install-dir`` (via command line or config file), then this option
    defaults to the same directory, so that the scripts will be able to find
    their associated package installation.  Otherwise, this setting defaults
    to the location where the distutils would normally install scripts, taking
    any distutils configuration file settings into account.

``--exclude-scripts, -x``
    Don't install scripts.  This is useful if you need to install multiple
    versions of a package, but do not want to reset the version that will be
    run by scripts that are already installed.

``--user`` (New in 0.6.11)
    Use the user-site-packages as specified in :pep:`370`
    instead of the global site-packages.

``--always-copy, -a``   (New in 0.5a4)
    Copy all needed distributions to the installation directory, even if they
    are already present in a directory on sys.path.  In older versions of
    EasyInstall, this was the default behavior, but now you must explicitly
    request it.  By default, EasyInstall will no longer copy such distributions
    from other sys.path directories to the installation directory, unless you
    explicitly gave the distribution's filename on the command line.

    Note that as of 0.6a10, using this option excludes "system" and
    "development" eggs from consideration because they can't be reliably
    copied.  This may cause EasyInstall to choose an older version of a package
    than what you expected, or it may cause downloading and installation of a
    fresh copy of something that's already installed.  You will see warning
    messages for any eggs that EasyInstall skips, before it falls back to an
    older version or attempts to download a fresh copy.

``--find-links=URLS_OR_FILENAMES, -f URLS_OR_FILENAMES``
    Scan the specified "download pages" or directories for direct links to eggs
    or other distributions.  Any existing file or directory names or direct
    download URLs are immediately added to EasyInstall's search cache, and any
    indirect URLs (ones that don't point to eggs or other recognized archive
    formats) are added to a list of additional places to search for download
    links.  As soon as EasyInstall has to go online to find a package (either
    because it doesn't exist locally, or because ``--upgrade`` or ``-U`` was
    used), the specified URLs will be downloaded and scanned for additional
    direct links.

    Eggs and archives found by way of ``--find-links`` are only downloaded if
    they are needed to meet a requirement specified on the command line; links
    to unneeded packages are ignored.

    If all requested packages can be found using links on the specified
    download pages, the Python Package Index will not be consulted unless you
    also specified the ``--upgrade`` or ``-U`` option.

    (Note: if you want to refer to a local HTML file containing links, you must
    use a ``file:`` URL, as filenames that do not refer to a directory, egg, or
    archive are ignored.)

    You may specify multiple URLs or file/directory names with this option,
    separated by whitespace.  Note that on the command line, you will probably
    have to surround the URL list with quotes, so that it is recognized as a
    single option value.  You can also specify URLs in a configuration file;
    see `Configuration Files`_, above.

    Changed in 0.6a10: previously all URLs and directories passed to this
    option were scanned as early as possible, but from 0.6a10 on, only
    directories and direct archive links are scanned immediately; URLs are not
    retrieved unless a package search was already going to go online due to a
    package not being available locally, or due to the use of the ``--update``
    or ``-U`` option.

``--no-find-links`` Blocks the addition of any link.
    This parameter is useful if you want to avoid adding links defined in a
    project easy_install is installing (whether it's a requested project or a
    dependency). When used, ``--find-links`` is ignored.

    Added in Distribute 0.6.11 and Setuptools 0.7.

``--index-url=URL, -i URL`` (New in 0.4a1; default changed in 0.6c7)
    Specifies the base URL of the Python Package Index.  The default is
    https://pypi.org/simple/ if not specified.  When a package is requested
    that is not locally available or linked from a ``--find-links`` download
    page, the package index will be searched for download pages for the needed
    package, and those download pages will be searched for links to download
    an egg or source distribution.

``--editable, -e`` (New in 0.6a1)
    Only find and download source distributions for the specified projects,
    unpacking them to subdirectories of the specified ``--build-directory``.
    EasyInstall will not actually build or install the requested projects or
    their dependencies; it will just find and extract them for you.  See
    `Editing and Viewing Source Packages`_ above for more details.

``--build-directory=DIR, -b DIR`` (UPDATED in 0.6a1)
    Set the directory used to build source packages.  If a package is built
    from a source distribution or checkout, it will be extracted to a
    subdirectory of the specified directory.  The subdirectory will have the
    same name as the extracted distribution's project, but in all-lowercase.
    If a file or directory of that name already exists in the given directory,
    a warning will be printed to the console, and the build will take place in
    a temporary directory instead.

    This option is most useful in combination with the ``--editable`` option,
    which forces EasyInstall to *only* find and extract (but not build and
    install) source distributions.  See `Editing and Viewing Source Packages`_,
    above, for more information.

``--verbose, -v, --quiet, -q`` (New in 0.4a4)
    Control the level of detail of EasyInstall's progress messages.  The
    default detail level is "info", which prints information only about
    relatively time-consuming operations like running a setup script, unpacking
    an archive, or retrieving a URL.  Using ``-q`` or ``--quiet`` drops the
    detail level to "warn", which will only display installation reports,
    warnings, and errors.  Using ``-v`` or ``--verbose`` increases the detail
    level to include individual file-level operations, link analysis messages,
    and distutils messages from any setup scripts that get run.  If you include
    the ``-v`` option more than once, the second and subsequent uses are passed
    down to any setup scripts, increasing the verbosity of their reporting as
    well.

``--dry-run, -n`` (New in 0.4a4)
    Don't actually install the package or scripts.  This option is passed down
    to any setup scripts run, so packages should not actually build either.
    This does *not* skip downloading, nor does it skip extracting source
    distributions to a temporary/build directory.

``--optimize=LEVEL``, ``-O LEVEL`` (New in 0.4a4)
    If you are installing from a source distribution, and are *not* using the
    ``--zip-ok`` option, this option controls the optimization level for
    compiling installed ``.py`` files to ``.pyo`` files.  It does not affect
    the compilation of modules contained in ``.egg`` files, only those in
    ``.egg`` directories.  The optimization level can be set to 0, 1, or 2;
    the default is 0 (unless it's set under ``install`` or ``install_lib`` in
    one of your distutils configuration files).

``--record=FILENAME``  (New in 0.5a4)
    Write a record of all installed files to FILENAME.  This is basically the
    same as the same option for the standard distutils "install" command, and
    is included for compatibility with tools that expect to pass this option
    to "setup.py install".

``--site-dirs=DIRLIST, -S DIRLIST``   (New in 0.6a1)
    Specify one or more custom "site" directories (separated by commas).
    "Site" directories are directories where ``.pth`` files are processed, such
    as the main Python ``site-packages`` directory.  As of 0.6a10, EasyInstall
    automatically detects whether a given directory processes ``.pth`` files
    (or can be made to do so), so you should not normally need to use this
    option.  It is is now only necessary if you want to override EasyInstall's
    judgment and force an installation directory to be treated as if it
    supported ``.pth`` files.

``--no-deps, -N``  (New in 0.6a6)
    Don't install any dependencies.  This is intended as a convenience for
    tools that wrap eggs in a platform-specific packaging system.  (We don't
    recommend that you use it for anything else.)

``--allow-hosts=PATTERNS, -H PATTERNS``   (New in 0.6a6)
    Restrict downloading and spidering to hosts matching the specified glob
    patterns.  E.g. ``-H *.python.org`` restricts web access so that only
    packages listed and downloadable from machines in the ``python.org``
    domain.  The glob patterns must match the *entire* user/host/port section of
    the target URL(s).  For example, ``*.python.org`` will NOT accept a URL
    like ``http://python.org/foo`` or ``http://www.python.org:8080/``.
    Multiple patterns can be specified by separating them with commas.  The
    default pattern is ``*``, which matches anything.

    In general, this option is mainly useful for blocking EasyInstall's web
    access altogether (e.g. ``-Hlocalhost``), or to restrict it to an intranet
    or other trusted site.  EasyInstall will do the best it can to satisfy
    dependencies given your host restrictions, but of course can fail if it
    can't find suitable packages.  EasyInstall displays all blocked URLs, so
    that you can adjust your ``--allow-hosts`` setting if it is more strict
    than you intended.  Some sites may wish to define a restrictive default
    setting for this option in their `configuration files`_, and then manually
    override the setting on the command line as needed.

``--prefix=DIR`` (New in 0.6a10)
    Use the specified directory as a base for computing the default
    installation and script directories.  On Windows, the resulting default
    directories will be ``prefix\\Lib\\site-packages`` and ``prefix\\Scripts``,
    while on other platforms the defaults will be
    ``prefix/lib/python2.X/site-packages`` (with the appropriate version
    substituted) for libraries and ``prefix/bin`` for scripts.

    Note that the ``--prefix`` option only sets the *default* installation and
    script directories, and does not override the ones set on the command line
    or in a configuration file.

``--local-snapshots-ok, -l`` (New in 0.6c6)
    Normally, EasyInstall prefers to only install *released* versions of
    projects, not in-development ones, because such projects may not
    have a currently-valid version number.  So, it usually only installs them
    when their ``setup.py`` directory is explicitly passed on the command line.

    However, if this option is used, then any in-development projects that were
    installed using the ``setup.py develop`` command, will be used to build
    eggs, effectively upgrading the "in-development" project to a snapshot
    release.  Normally, this option is used only in conjunction with the
    ``--always-copy`` option to create a distributable snapshot of every egg
    needed to run an application.

    Note that if you use this option, you must make sure that there is a valid
    version number (such as an SVN revision number tag) for any in-development
    projects that may be used, as otherwise EasyInstall may not be able to tell
    what version of the project is "newer" when future installations or
    upgrades are attempted.


.. _non-root installation:

Custom Installation Locations
-----------------------------

By default, EasyInstall installs python packages into Python's main ``site-packages`` directory,
and manages them using a custom ``.pth`` file in that same directory.

Very often though, a user or developer wants ``easy_install`` to install and manage python packages
in an alternative location, usually for one of 3 reasons:

1. They don't have access to write to the main Python site-packages directory.

2. They want a user-specific stash of packages, that is not visible to other users.

3. They want to isolate a set of packages to a specific python application, usually to minimize
   the possibility of version conflicts.

Historically, there have been many approaches to achieve custom installation.
The following section lists only the easiest and most relevant approaches [1]_.

`Use the "--user" option`_

`Use the "--user" option and customize "PYTHONUSERBASE"`_

`Use "virtualenv"`_

.. [1] There are older ways to achieve custom installation using various ``easy_install`` and ``setup.py install`` options, combined with ``PYTHONPATH`` and/or ``PYTHONUSERBASE`` alterations, but all of these are effectively deprecated by the User scheme brought in by `PEP-370`_.

.. _PEP-370: http://www.python.org/dev/peps/pep-0370/


Use the "--user" option
~~~~~~~~~~~~~~~~~~~~~~~
Python provides a User scheme for installation, which means that all
python distributions support an alternative install location that is specific to a user [3]_.
The Default location for each OS is explained in the python documentation
for the ``site.USER_BASE`` variable.  This mode of installation can be turned on by
specifying the ``--user`` option to ``setup.py install`` or ``easy_install``.
This approach serves the need to have a user-specific stash of packages.

.. [3] Prior to the User scheme, there was the Home scheme, which is still available, but requires more effort than the User scheme to get packages recognized.

Use the "--user" option and customize "PYTHONUSERBASE"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The User scheme install location can be customized by setting the ``PYTHONUSERBASE`` environment
variable, which updates the value of ``site.USER_BASE``.  To isolate packages to a specific
application, simply set the OS environment of that application to a specific value of
``PYTHONUSERBASE``, that contains just those packages.

Use "virtualenv"
~~~~~~~~~~~~~~~~
"virtualenv" is a 3rd-party python package that effectively "clones" a python installation, thereby
creating an isolated location to install packages.  The evolution of "virtualenv" started before the existence
of the User installation scheme.  "virtualenv" provides a version of ``easy_install`` that is
scoped to the cloned python install and is used in the normal way. "virtualenv" does offer various features
that the User installation scheme alone does not provide, e.g. the ability to hide the main python site-packages.

Please refer to the `virtualenv`_ documentation for more details.

.. _virtualenv: https://pypi.org/project/virtualenv/



Package Index "API"
-------------------

Custom package indexes (and PyPI) must follow the following rules for
EasyInstall to be able to look up and download packages:

1. Except where stated otherwise, "pages" are HTML or XHTML, and "links"
   refer to ``href`` attributes.

2. Individual project version pages' URLs must be of the form
   ``base/projectname/version``, where ``base`` is the package index's base URL.

3. Omitting the ``/version`` part of a project page's URL (but keeping the
   trailing ``/``) should result in a page that is either:

   a) The single active version of that project, as though the version had been
      explicitly included, OR

   b) A page with links to all of the active version pages for that project.

4. Individual project version pages should contain direct links to downloadable
   distributions where possible.  It is explicitly permitted for a project's
   "long_description" to include URLs, and these should be formatted as HTML
   links by the package index, as EasyInstall does no special processing to
   identify what parts of a page are index-specific and which are part of the
   project's supplied description.

5. Where available, MD5 information should be added to download URLs by
   appending a fragment identifier of the form ``#md5=...``, where ``...`` is
   the 32-character hex MD5 digest.  EasyInstall will verify that the
   downloaded file's MD5 digest matches the given value.

6. Individual project version pages should identify any "homepage" or
   "download" URLs using ``rel="homepage"`` and ``rel="download"`` attributes
   on the HTML elements linking to those URLs. Use of these attributes will
   cause EasyInstall to always follow the provided links, unless it can be
   determined by inspection that they are downloadable distributions. If the
   links are not to downloadable distributions, they are retrieved, and if they
   are HTML, they are scanned for download links. They are *not* scanned for
   additional "homepage" or "download" links, as these are only processed for
   pages that are part of a package index site.

7. The root URL of the index, if retrieved with a trailing ``/``, must result
   in a page containing links to *all* projects' active version pages.

   (Note: This requirement is a workaround for the absence of case-insensitive
   ``safe_name()`` matching of project names in URL paths. If project names are
   matched in this fashion (e.g. via the PyPI server, mod_rewrite, or a similar
   mechanism), then it is not necessary to include this all-packages listing
   page.)

8. If a package index is accessed via a ``file://`` URL, then EasyInstall will
   automatically use ``index.html`` files, if present, when trying to read a
   directory with a trailing ``/`` on the URL.
