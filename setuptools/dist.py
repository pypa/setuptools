__all__ = ['Distribution']

import re
import os
import sys
import distutils.log
import distutils.core
import distutils.cmd
from distutils.core import Distribution as _Distribution
from distutils.errors import DistutilsSetupError

from setuptools.compat import numeric_types, basestring
import pkg_resources

def _get_unpatched(cls):
    """Protect against re-patching the distutils if reloaded

    Also ensures that no other distutils extension monkeypatched the distutils
    first.
    """
    while cls.__module__.startswith('setuptools'):
        cls, = cls.__bases__
    if not cls.__module__.startswith('distutils'):
        raise AssertionError(
            "distutils has already been patched by %r" % cls
        )
    return cls

_Distribution = _get_unpatched(_Distribution)

sequence = tuple, list

def check_importable(dist, attr, value):
    try:
        ep = pkg_resources.EntryPoint.parse('x='+value)
        assert not ep.extras
    except (TypeError,ValueError,AttributeError,AssertionError):
        raise DistutilsSetupError(
            "%r must be importable 'module:attrs' string (got %r)"
            % (attr,value)
        )


def assert_string_list(dist, attr, value):
    """Verify that value is a string list or None"""
    try:
        assert ''.join(value)!=value
    except (TypeError,ValueError,AttributeError,AssertionError):
        raise DistutilsSetupError(
            "%r must be a list of strings (got %r)" % (attr,value)
        )
def check_nsp(dist, attr, value):
    """Verify that namespace packages are valid"""
    assert_string_list(dist,attr,value)
    for nsp in value:
        if not dist.has_contents_for(nsp):
            raise DistutilsSetupError(
                "Distribution contains no modules or packages for " +
                "namespace package %r" % nsp
            )
        if '.' in nsp:
            parent = '.'.join(nsp.split('.')[:-1])
            if parent not in value:
                distutils.log.warn(
                    "WARNING: %r is declared as a package namespace, but %r"
                    " is not: please correct this in setup.py", nsp, parent
                )

def check_extras(dist, attr, value):
    """Verify that extras_require mapping is valid"""
    try:
        for k,v in value.items():
            if ':' in k:
                k,m = k.split(':',1)
                if pkg_resources.invalid_marker(m):
                    raise DistutilsSetupError("Invalid environment marker: "+m)
            list(pkg_resources.parse_requirements(v))
    except (TypeError,ValueError,AttributeError):
        raise DistutilsSetupError(
            "'extras_require' must be a dictionary whose values are "
            "strings or lists of strings containing valid project/version "
            "requirement specifiers."
        )

def assert_bool(dist, attr, value):
    """Verify that value is True, False, 0, or 1"""
    if bool(value) != value:
        raise DistutilsSetupError(
            "%r must be a boolean value (got %r)" % (attr,value)
        )
def check_requirements(dist, attr, value):
    """Verify that install_requires is a valid requirements list"""
    try:
        list(pkg_resources.parse_requirements(value))
    except (TypeError,ValueError):
        raise DistutilsSetupError(
            "%r must be a string or list of strings "
            "containing valid project/version requirement specifiers" % (attr,)
        )
def check_entry_points(dist, attr, value):
    """Verify that entry_points map is parseable"""
    try:
        pkg_resources.EntryPoint.parse_map(value)
    except ValueError:
        e = sys.exc_info()[1]
        raise DistutilsSetupError(e)

def check_test_suite(dist, attr, value):
    if not isinstance(value,basestring):
        raise DistutilsSetupError("test_suite must be a string")

def check_package_data(dist, attr, value):
    """Verify that value is a dictionary of package names to glob lists"""
    if isinstance(value,dict):
        for k,v in value.items():
            if not isinstance(k,str): break
            try: iter(v)
            except TypeError:
                break
        else:
            return
    raise DistutilsSetupError(
        attr+" must be a dictionary mapping package names to lists of "
        "wildcard patterns"
    )

def check_packages(dist, attr, value):
    for pkgname in value:
        if not re.match(r'\w+(\.\w+)*', pkgname):
            distutils.log.warn(
                "WARNING: %r not a valid package name; please use only"
                ".-separated package names in setup.py", pkgname
            )


class Distribution(_Distribution):
    """Distribution with support for tests and package data

    This is an enhanced version of 'distutils.dist.Distribution' that
    effectively adds the following new optional keyword arguments to 'setup()':

     'install_requires' -- a string or sequence of strings specifying project
        versions that the distribution requires when installed, in the format
        used by 'pkg_resources.require()'.  They will be installed
        automatically when the package is installed.  If you wish to use
        packages that are not available in PyPI, or want to give your users an
        alternate download location, you can add a 'find_links' option to the
        '[easy_install]' section of your project's 'setup.cfg' file, and then
        setuptools will scan the listed web pages for links that satisfy the
        requirements.

     'extras_require' -- a dictionary mapping names of optional "extras" to the
        additional requirement(s) that using those extras incurs. For example,
        this::

            extras_require = dict(reST = ["docutils>=0.3", "reSTedit"])

        indicates that the distribution can optionally provide an extra
        capability called "reST", but it can only be used if docutils and
        reSTedit are installed.  If the user installs your package using
        EasyInstall and requests one of your extras, the corresponding
        additional requirements will be installed if needed.

     'test_suite' -- the name of a test suite to run for the 'test' command.
        If the user runs 'python setup.py test', the package will be installed,
        and the named test suite will be run.  The format is the same as
        would be used on a 'unittest.py' command line.  That is, it is the
        dotted name of an object to import and call to generate a test suite.

     'package_data' -- a dictionary mapping package names to lists of filenames
        or globs to use to find data files contained in the named packages.
        If the dictionary has filenames or globs listed under '""' (the empty
        string), those names will be searched for in every package, in addition
        to any names for the specific package.  Data files found using these
        names/globs will be installed along with the package, in the same
        location as the package.  Note that globs are allowed to reference
        the contents of non-package subdirectories, as long as you use '/' as
        a path separator.  (Globs are automatically converted to
        platform-specific paths at runtime.)

    In addition to these new keywords, this class also has several new methods
    for manipulating the distribution's contents.  For example, the 'include()'
    and 'exclude()' methods can be thought of as in-place add and subtract
    commands that add or remove packages, modules, extensions, and so on from
    the distribution.
    """

    _patched_dist = None

    def patch_missing_pkg_info(self, attrs):
        # Fake up a replacement for the data that would normally come from
        # PKG-INFO, but which might not yet be built if this is a fresh
        # checkout.
        #
        if not attrs or 'name' not in attrs or 'version' not in attrs:
            return
        key = pkg_resources.safe_name(str(attrs['name'])).lower()
        dist = pkg_resources.working_set.by_key.get(key)
        if dist is not None and not dist.has_metadata('PKG-INFO'):
            dist._version = pkg_resources.safe_version(str(attrs['version']))
            self._patched_dist = dist

    def __init__(self, attrs=None):
        have_package_data = hasattr(self, "package_data")
        if not have_package_data:
            self.package_data = {}
        self.dist_files = []
        self.src_root = attrs and attrs.pop("src_root", None)
        self.patch_missing_pkg_info(attrs)
        # Make sure we have any eggs needed to interpret 'attrs'
        if attrs is not None:
            self.dependency_links = attrs.pop('dependency_links', [])
            assert_string_list(self,'dependency_links',self.dependency_links)
        if attrs and 'setup_requires' in attrs:
            self.fetch_build_eggs(attrs.pop('setup_requires'))
        for ep in pkg_resources.iter_entry_points('distutils.setup_keywords'):
            if not hasattr(self,ep.name):
                setattr(self,ep.name,None)
        _Distribution.__init__(self,attrs)
        if isinstance(self.metadata.version, numeric_types):
            # Some people apparently take "version number" too literally :)
            self.metadata.version = str(self.metadata.version)

    def fetch_build_eggs(self, requires):
        """Resolve pre-setup requirements"""
        from pkg_resources import working_set, parse_requirements
        for dist in working_set.resolve(
            parse_requirements(requires), installer=self.fetch_build_egg,
            replace_conflicting=True
        ):
            working_set.add(dist, replace=True)

    def finalize_options(self):
        _Distribution.finalize_options(self)

        for ep in pkg_resources.iter_entry_points('distutils.setup_keywords'):
            value = getattr(self,ep.name,None)
            if value is not None:
                ep.require(installer=self.fetch_build_egg)
                ep.load()(self, ep.name, value)
        if getattr(self, 'convert_2to3_doctests', None):
            # XXX may convert to set here when we can rely on set being builtin
            self.convert_2to3_doctests = [os.path.abspath(p) for p in self.convert_2to3_doctests]
        else:
            self.convert_2to3_doctests = []

    def fetch_build_egg(self, req):
        """Fetch an egg needed for building"""

        try:
            cmd = self._egg_fetcher
            cmd.package_index.to_scan = []
        except AttributeError:
            from setuptools.command.easy_install import easy_install
            dist = self.__class__({'script_args':['easy_install']})
            dist.parse_config_files()
            opts = dist.get_option_dict('easy_install')
            keep = (
                'find_links', 'site_dirs', 'index_url', 'optimize',
                'site_dirs', 'allow_hosts'
            )
            for key in list(opts):
                if key not in keep:
                    del opts[key]   # don't use any other settings
            if self.dependency_links:
                links = self.dependency_links[:]
                if 'find_links' in opts:
                    links = opts['find_links'][1].split() + links
                opts['find_links'] = ('setup', links)
            cmd = easy_install(
                dist, args=["x"], install_dir=os.curdir, exclude_scripts=True,
                always_copy=False, build_directory=None, editable=False,
                upgrade=False, multi_version=True, no_report=True, user=False
            )
            cmd.ensure_finalized()
            self._egg_fetcher = cmd
        return cmd.easy_install(req)

    def get_command_class(self, command):
        """Pluggable version of get_command_class()"""
        if command in self.cmdclass:
            return self.cmdclass[command]

        for ep in pkg_resources.iter_entry_points('distutils.commands',command):
            ep.require(installer=self.fetch_build_egg)
            self.cmdclass[command] = cmdclass = ep.load()
            return cmdclass
        else:
            return _Distribution.get_command_class(self, command)

    def print_commands(self):
        for ep in pkg_resources.iter_entry_points('distutils.commands'):
            if ep.name not in self.cmdclass:
                cmdclass = ep.load(False) # don't require extras, we're not running
                self.cmdclass[ep.name] = cmdclass
        return _Distribution.print_commands(self)

    def include(self,**attrs):
        """Add items to distribution that are named in keyword arguments

        For example, 'dist.exclude(py_modules=["x"])' would add 'x' to
        the distribution's 'py_modules' attribute, if it was not already
        there.

        Currently, this method only supports inclusion for attributes that are
        lists or tuples.  If you need to add support for adding to other
        attributes in this or a subclass, you can add an '_include_X' method,
        where 'X' is the name of the attribute.  The method will be called with
        the value passed to 'include()'.  So, 'dist.include(foo={"bar":"baz"})'
        will try to call 'dist._include_foo({"bar":"baz"})', which can then
        handle whatever special inclusion logic is needed.
        """
        for k,v in attrs.items():
            include = getattr(self, '_include_'+k, None)
            if include:
                include(v)
            else:
                self._include_misc(k,v)

    def exclude_package(self,package):
        """Remove packages, modules, and extensions in named package"""

        pfx = package+'.'
        if self.packages:
            self.packages = [
                p for p in self.packages
                    if p != package and not p.startswith(pfx)
            ]

        if self.py_modules:
            self.py_modules = [
                p for p in self.py_modules
                    if p != package and not p.startswith(pfx)
            ]

        if self.ext_modules:
            self.ext_modules = [
                p for p in self.ext_modules
                    if p.name != package and not p.name.startswith(pfx)
            ]

    def has_contents_for(self,package):
        """Return true if 'exclude_package(package)' would do something"""

        pfx = package+'.'

        for p in self.iter_distribution_names():
            if p==package or p.startswith(pfx):
                return True

    def _exclude_misc(self,name,value):
        """Handle 'exclude()' for list/tuple attrs without a special handler"""
        if not isinstance(value,sequence):
            raise DistutilsSetupError(
                "%s: setting must be a list or tuple (%r)" % (name, value)
            )
        try:
            old = getattr(self,name)
        except AttributeError:
            raise DistutilsSetupError(
                "%s: No such distribution setting" % name
            )
        if old is not None and not isinstance(old,sequence):
            raise DistutilsSetupError(
                name+": this setting cannot be changed via include/exclude"
            )
        elif old:
            setattr(self,name,[item for item in old if item not in value])

    def _include_misc(self,name,value):
        """Handle 'include()' for list/tuple attrs without a special handler"""

        if not isinstance(value,sequence):
            raise DistutilsSetupError(
                "%s: setting must be a list (%r)" % (name, value)
            )
        try:
            old = getattr(self,name)
        except AttributeError:
            raise DistutilsSetupError(
                "%s: No such distribution setting" % name
            )
        if old is None:
            setattr(self,name,value)
        elif not isinstance(old,sequence):
            raise DistutilsSetupError(
                name+": this setting cannot be changed via include/exclude"
            )
        else:
            setattr(self,name,old+[item for item in value if item not in old])

    def exclude(self,**attrs):
        """Remove items from distribution that are named in keyword arguments

        For example, 'dist.exclude(py_modules=["x"])' would remove 'x' from
        the distribution's 'py_modules' attribute.  Excluding packages uses
        the 'exclude_package()' method, so all of the package's contained
        packages, modules, and extensions are also excluded.

        Currently, this method only supports exclusion from attributes that are
        lists or tuples.  If you need to add support for excluding from other
        attributes in this or a subclass, you can add an '_exclude_X' method,
        where 'X' is the name of the attribute.  The method will be called with
        the value passed to 'exclude()'.  So, 'dist.exclude(foo={"bar":"baz"})'
        will try to call 'dist._exclude_foo({"bar":"baz"})', which can then
        handle whatever special exclusion logic is needed.
        """
        for k,v in attrs.items():
            exclude = getattr(self, '_exclude_'+k, None)
            if exclude:
                exclude(v)
            else:
                self._exclude_misc(k,v)

    def _exclude_packages(self,packages):
        if not isinstance(packages,sequence):
            raise DistutilsSetupError(
                "packages: setting must be a list or tuple (%r)" % (packages,)
            )
        list(map(self.exclude_package, packages))

    def _parse_command_opts(self, parser, args):
        # Remove --with-X/--without-X options when processing command args
        self.global_options = self.__class__.global_options
        self.negative_opt = self.__class__.negative_opt

        # First, expand any aliases
        command = args[0]
        aliases = self.get_option_dict('aliases')
        while command in aliases:
            src,alias = aliases[command]
            del aliases[command]    # ensure each alias can expand only once!
            import shlex
            args[:1] = shlex.split(alias,True)
            command = args[0]

        nargs = _Distribution._parse_command_opts(self, parser, args)

        # Handle commands that want to consume all remaining arguments
        cmd_class = self.get_command_class(command)
        if getattr(cmd_class,'command_consumes_arguments',None):
            self.get_option_dict(command)['args'] = ("command line", nargs)
            if nargs is not None:
                return []

        return nargs

    def get_cmdline_options(self):
        """Return a '{cmd: {opt:val}}' map of all command-line options

        Option names are all long, but do not include the leading '--', and
        contain dashes rather than underscores.  If the option doesn't take
        an argument (e.g. '--quiet'), the 'val' is 'None'.

        Note that options provided by config files are intentionally excluded.
        """

        d = {}

        for cmd,opts in self.command_options.items():

            for opt,(src,val) in opts.items():

                if src != "command line":
                    continue

                opt = opt.replace('_','-')

                if val==0:
                    cmdobj = self.get_command_obj(cmd)
                    neg_opt = self.negative_opt.copy()
                    neg_opt.update(getattr(cmdobj,'negative_opt',{}))
                    for neg,pos in neg_opt.items():
                        if pos==opt:
                            opt=neg
                            val=None
                            break
                    else:
                        raise AssertionError("Shouldn't be able to get here")

                elif val==1:
                    val = None

                d.setdefault(cmd,{})[opt] = val

        return d

    def iter_distribution_names(self):
        """Yield all packages, modules, and extension names in distribution"""

        for pkg in self.packages or ():
            yield pkg

        for module in self.py_modules or ():
            yield module

        for ext in self.ext_modules or ():
            if isinstance(ext,tuple):
                name, buildinfo = ext
            else:
                name = ext.name
            if name.endswith('module'):
                name = name[:-6]
            yield name

    def handle_display_options(self, option_order):
        """If there were any non-global "display-only" options
        (--help-commands or the metadata display options) on the command
        line, display the requested info and return true; else return
        false.
        """
        import sys

        if sys.version_info < (3,) or self.help_commands:
            return _Distribution.handle_display_options(self, option_order)

        # Stdout may be StringIO (e.g. in tests)
        import io
        if not isinstance(sys.stdout, io.TextIOWrapper):
            return _Distribution.handle_display_options(self, option_order)

        # Don't wrap stdout if utf-8 is already the encoding. Provides
        #  workaround for #334.
        if sys.stdout.encoding.lower() in ('utf-8', 'utf8'):
            return _Distribution.handle_display_options(self, option_order)

        # Print metadata in UTF-8 no matter the platform
        encoding = sys.stdout.encoding
        errors = sys.stdout.errors
        newline = sys.platform != 'win32' and '\n' or None
        line_buffering = sys.stdout.line_buffering

        sys.stdout = io.TextIOWrapper(
            sys.stdout.detach(), 'utf-8', errors, newline, line_buffering)
        try:
            return _Distribution.handle_display_options(self, option_order)
        finally:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.detach(), encoding, errors, newline, line_buffering)


# Install it throughout the distutils
for module in distutils.dist, distutils.core, distutils.cmd:
    module.Distribution = Distribution
