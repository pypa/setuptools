__all__ = ['Distribution', 'Feature']

from distutils.core import Distribution as _Distribution
from distutils.core import Extension
from setuptools.command.build_py import build_py
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install
from setuptools.command.install_lib import install_lib
from distutils.errors import DistutilsOptionError, DistutilsPlatformError
from distutils.errors import DistutilsSetupError
sequence = tuple, list

class Distribution(_Distribution):

    """Distribution with support for features, tests, and package data

    This is an enhanced version of 'distutils.dist.Distribution' that
    effectively adds the following new optional keyword arguments to 'setup()':

     'features' -- a dictionary mapping option names to 'setuptools.Feature'
        objects.  Features are a portion of the distribution that can be
        included or excluded based on user options, inter-feature dependencies,
        and availability on the current system.  Excluded features are omitted
        from all setup commands, including source and binary distributions, so
        you can create multiple distributions from the same source tree.

        Feature names should be valid Python identifiers, except that they may
        contain the '-' (minus) sign.  Features can be included or excluded
        via the command line options '--with-X' and '--without-X', where 'X' is
        the name of the feature.  Whether a feature is included by default, and
        whether you are allowed to control this from the command line, is
        determined by the Feature object.  See the 'Feature' class for more
        information.

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
    the distribution.  They are used by the feature subsystem to configure the
    distribution for the included and excluded features.
    """

    def __init__ (self, attrs=None):
        self.features = {}
        self.package_data = {}
        self.test_suite = None
        self.requires = []
        _Distribution.__init__(self,attrs)
        self.cmdclass.setdefault('build_py',build_py)
        self.cmdclass.setdefault('build_ext',build_ext)
        self.cmdclass.setdefault('install',install)
        self.cmdclass.setdefault('install_lib',install_lib)

        if self.features:
            self._set_global_opts_from_features()

    def parse_command_line(self):
        """Process features after parsing command line options"""
        result = _Distribution.parse_command_line(self)
        if self.features:
            self._finalize_features()
        return result

    def _feature_attrname(self,name):
        """Convert feature name to corresponding option attribute name"""
        return 'with_'+name.replace('-','_')

    def _set_global_opts_from_features(self):
        """Add --with-X/--without-X options based on optional features"""

        go = []
        no = self.negative_opt.copy()

        for name,feature in self.features.items():
            self._set_feature(name,None)
            feature.validate(self)

            if feature.optional:
                descr = feature.description
                incdef = ' (default)'
                excdef=''
                if not feature.include_by_default():
                    excdef, incdef = incdef, excdef

                go.append(('with-'+name, None, 'include '+descr+incdef))
                go.append(('without-'+name, None, 'exclude '+descr+excdef))
                no['without-'+name] = 'with-'+name

        self.global_options = self.feature_options = go + self.global_options
        self.negative_opt = self.feature_negopt = no

    def _finalize_features(self):
        """Add/remove features and resolve dependencies between them"""

        # First, flag all the enabled items (and thus their dependencies)
        for name,feature in self.features.items():
            enabled = self.feature_is_included(name)
            if enabled or (enabled is None and feature.include_by_default()):
                feature.include_in(self)
                self._set_feature(name,1)

        # Then disable the rest, so that off-by-default features don't
        # get flagged as errors when they're required by an enabled feature
        for name,feature in self.features.items():
            if not self.feature_is_included(name):
                feature.exclude_from(self)
                self._set_feature(name,0)

    def _set_feature(self,name,status):
        """Set feature's inclusion status"""
        setattr(self,self._feature_attrname(name),status)

    def feature_is_included(self,name):
        """Return 1 if feature is included, 0 if excluded, 'None' if unknown"""
        return getattr(self,self._feature_attrname(name))

    def include_feature(self,name):
        """Request inclusion of feature named 'name'"""

        if self.feature_is_included(name)==0:
            descr = self.features[name].description
            raise DistutilsOptionError(
               descr + " is required, but was excluded or is not available"
           )
        self.features[name].include_in(self)
        self._set_feature(name,1)

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
                    if p<>package and not p.startswith(pfx)
            ]

        if self.py_modules:
            self.py_modules = [
                p for p in self.py_modules
                    if p<>package and not p.startswith(pfx)
            ]

        if self.ext_modules:
            self.ext_modules = [
                p for p in self.ext_modules
                    if p.name<>package and not p.name.startswith(pfx)
            ]


    def has_contents_for(self,package):
        """Return true if 'exclude_package(package)' would do something"""

        pfx = package+'.'

        for p in self.packages or ():
            if p==package or p.startswith(pfx):
                return True

        for p in self.py_modules or ():
            if p==package or p.startswith(pfx):
                return True

        for p in self.ext_modules or ():
            if p.name==package or p.name.startswith(pfx):
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
        map(self.exclude_package, packages)

    def _parse_command_opts(self, parser, args):
        # Remove --with-X/--without-X options when processing command args
        self.global_options = self.__class__.global_options
        self.negative_opt = self.__class__.negative_opt
        return _Distribution._parse_command_opts(self, parser, args)

    def has_dependencies(self):
        return not not self.requires



class Feature:

    """A subset of the distribution that can be excluded if unneeded/wanted

    Features are created using these keyword arguments:

      'description' -- a short, human readable description of the feature, to
         be used in error messages, and option help messages.

      'standard' -- if true, the feature is included by default if it is
         available on the current system.  Otherwise, the feature is only
         included if requested via a command line '--with-X' option, or if
         another included feature requires it.  The default setting is 'False'.

      'available' -- if true, the feature is available for installation on the
         current system.  The default setting is 'True'.

      'optional' -- if true, the feature's inclusion can be controlled from the
         command line, using the '--with-X' or '--without-X' options.  If
         false, the feature's inclusion status is determined automatically,
         based on 'availabile', 'standard', and whether any other feature
         requires it.  The default setting is 'True'.

      'requires' -- a string or sequence of strings naming features that should
         also be included if this feature is included.  Defaults to empty list.

      'remove' -- a string or list of strings naming packages to be removed
         from the distribution if this feature is *not* included.  If the
         feature *is* included, this argument is ignored.  This argument exists
         to support removing features that "crosscut" a distribution, such as
         defining a 'tests' feature that removes all the 'tests' subpackages
         provided by other features.  The default for this argument is an empty
         list.  (Note: the named package(s) or modules must exist in the base
         distribution when the 'setup()' function is initially called.)

      other keywords -- any other keyword arguments are saved, and passed to
         the distribution's 'include()' and 'exclude()' methods when the
         feature is included or excluded, respectively.  So, for example, you
         could pass 'packages=["a","b"]' to cause packages 'a' and 'b' to be
         added or removed from the distribution as appropriate.

    A feature must include at least one 'requires', 'remove', or other
    keyword argument.  Otherwise, it can't affect the distribution in any way.
    Note also that you can subclass 'Feature' to create your own specialized
    feature types that modify the distribution in other ways when included or
    excluded.  See the docstrings for the various methods here for more detail.
    Aside from the methods, the only feature attributes that distributions look
    at are 'description' and 'optional'.
    """

    def __init__(self, description, standard=False, available=True,
        optional=True, requires=(), remove=(), **extras
    ):

        self.description = description
        self.standard = standard
        self.available = available
        self.optional = optional

        if isinstance(requires,str):
            requires = requires,

        self.requires = requires

        if isinstance(remove,str):
            remove = remove,

        self.remove = remove
        self.extras = extras

        if not remove and not requires and not extras:
            raise DistutilsSetupError(
                "Feature %s: must define 'requires', 'remove', or at least one"
                " of 'packages', 'py_modules', etc."
            )


    def include_by_default(self):
        """Should this feature be included by default?"""
        return self.available and self.standard


    def include_in(self,dist):

        """Ensure feature and its requirements are included in distribution

        You may override this in a subclass to perform additional operations on
        the distribution.  Note that this method may be called more than once
        per feature, and so should be idempotent.

        """

        if not self.available:
            raise DistutilsPlatformError(
                self.description+" is required,"
                "but is not available on this platform"
            )

        dist.include(**self.extras)

        for f in self.requires:
            dist.include_feature(f)



    def exclude_from(self,dist):

        """Ensure feature is excluded from distribution

        You may override this in a subclass to perform additional operations on
        the distribution.  This method will be called at most once per
        feature, and only after all included features have been asked to
        include themselves.
        """

        dist.exclude(**self.extras)

        if self.remove:
            for item in self.remove:
                dist.exclude_package(item)



    def validate(self,dist):

        """Verify that feature makes sense in context of distribution

        This method is called by the distribution just before it parses its
        command line.  It checks to ensure that the 'remove' attribute, if any,
        contains only valid package/module names that are present in the base
        distribution when 'setup()' is called.  You may override it in a
        subclass to perform any other required validation of the feature
        against a target distribution.
        """

        for item in self.remove:
            if not dist.has_contents_for(item):
                raise DistutilsSetupError(
                    "%s wants to be able to remove %s, but the distribution"
                    " doesn't contain any packages or modules under %s"
                    % (self.description, item, item)
                )






















