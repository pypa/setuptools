"""Package resource API
--------------------

A resource is a logical file contained within a package, or a logical
subdirectory thereof.  The package resource API expects resource names
to have their path parts separated with ``/``, *not* whatever the local
path separator is.  Do not use os.path operations to manipulate resource
names being passed into the API.

The package resource API is designed to work with normal filesystem packages,
.egg files, and unpacked .egg files.  It can also work in a limited way with
.zip files and with custom PEP 302 loaders that support the ``get_data()``
method.
"""
__all__ = [
    'register_loader_type', 'get_provider', 'IResourceProvider','PathMetadata',
    'ResourceManager', 'AvailableDistributions', 'require', 'resource_string',
    'resource_stream', 'resource_filename', 'set_extraction_path', 'EGG_DIST',
    'cleanup_resources', 'parse_requirements', 'ensure_directory','SOURCE_DIST',
    'compatible_platforms', 'get_platform', 'IMetadataProvider','parse_version',
    'ResolutionError', 'VersionConflict', 'DistributionNotFound','EggMetadata',
    'InvalidOption', 'Distribution', 'Requirement', 'yield_lines',
    'get_importer', 'find_distributions', 'find_on_path', 'register_finder',
    'split_sections', 'declare_namespace', 'register_namespace_handler',
    'safe_name', 'safe_version', 'run_main',
]

import sys, os, zipimport, time, re, imp
from sets import ImmutableSet












class ResolutionError(Exception):
    """Abstract base for dependency resolution errors"""

class VersionConflict(ResolutionError):
    """An already-installed version conflicts with the requested version"""

class DistributionNotFound(ResolutionError):
    """A requested distribution was not found"""

class InvalidOption(ResolutionError):
    """Invalid or unrecognized option name for a distribution"""

_provider_factories = {}
PY_MAJOR = sys.version[:3]

EGG_DIST    = 2
SOURCE_DIST = 1

def register_loader_type(loader_type, provider_factory):
    """Register `provider_factory` to make providers for `loader_type`

    `loader_type` is the type or class of a PEP 302 ``module.__loader__``,
    and `provider_factory` is a function that, passed a *module* object,
    returns an ``IResourceProvider`` for that module.
    """
    _provider_factories[loader_type] = provider_factory

def get_provider(moduleName):
    """Return an IResourceProvider for the named module"""
    module = sys.modules[moduleName]
    loader = getattr(module, '__loader__', None)
    return _find_adapter(_provider_factories, loader)(module)









def get_platform():
    """Return this platform's string for platform-specific distributions

    XXX Currently this is the same as ``distutils.util.get_platform()``, but it
    needs some hacks for Linux and Mac OS X.
    """
    from distutils.util import get_platform
    return get_platform()

def compatible_platforms(provided,required):
    """Can code for the `provided` platform run on the `required` platform?

    Returns true if either platform is ``None``, or the platforms are equal.

    XXX Needs compatibility checks for Linux and Mac OS X.
    """
    if provided is None or required is None or provided==required:
        return True     # easy case

    # XXX all the tricky cases go here
    return False

def run_main(dist_spec, script_name):
    """Locate distribution `dist_spec` and run its `script_name` script"""
    import __main__
    __main__.__dict__.clear()
    __main__.__dict__.update({'__name__':'__main__'})
    require(dist_spec)[0].metadata.run_script(script_name, __main__.__dict__)













class IMetadataProvider:

    def has_metadata(name):
        """Does the package's distribution contain the named metadata?"""

    def get_metadata(name):
        """The named metadata resource as a string"""

    def get_metadata_lines(name):
        """Yield named metadata resource as list of non-blank non-comment lines

       Leading and trailing whitespace is stripped from each line, and lines
       with ``#`` as the first non-blank character are omitted."""

    def metadata_isdir(name):
        """Is the named metadata a directory?  (like ``os.path.isdir()``)"""

    def metadata_listdir(name):
        """List of metadata names in the directory (like ``os.listdir()``)"""

    def run_script(script_name, namespace):
        """Execute the named script in the supplied namespace dictionary"""



















class IResourceProvider(IMetadataProvider):
    """An object that provides access to package resources"""

    def get_resource_filename(manager, resource_name):
        """Return a true filesystem path for `resource_name`

        `manager` must be an ``IResourceManager``"""

    def get_resource_stream(manager, resource_name):
        """Return a readable file-like object for `resource_name`

        `manager` must be an ``IResourceManager``"""

    def get_resource_string(manager, resource_name):
        """Return a string containing the contents of `resource_name`

        `manager` must be an ``IResourceManager``"""

    def has_resource(resource_name):
        """Does the package contain the named resource?"""

    def resource_isdir(resource_name):
        """Is the named resource a directory?  (like ``os.path.isdir()``)"""

    def resource_listdir(resource_name):
        """List of resource names in the directory (like ``os.listdir()``)"""















class AvailableDistributions(object):
    """Searchable snapshot of distributions on a search path"""

    def __init__(self,search_path=None,platform=get_platform(),python=PY_MAJOR):
        """Snapshot distributions available on a search path

        Any distributions found on `search_path` are added to the distribution
        map.  `search_path` should be a sequence of ``sys.path`` items.  If not
        supplied, ``sys.path`` is used.

        `platform` is an optional string specifying the name of the platform
        that platform-specific distributions must be compatible with.  If
        unspecified, it defaults to the current platform.  `python` is an
        optional string naming the desired version of Python (e.g. ``'2.4'``);
        it defaults to the current version.

        You may explicitly set `platform` (and/or `python`) to ``None`` if you
        wish to map *all* distributions, not just those compatible with the
        running platform or Python version.
        """
        self._distmap = {}
        self._cache = {}
        self.platform = platform
        self.python = python
        self.scan(search_path)

    def can_add(self, dist):
        """Is distribution `dist` acceptable for this collection?"""
        return (self.python is None or dist.py_version==self.python) \
           and compatible_platforms(dist.platform,self.platform)

    def __iter__(self):
        """Iterate over distribution keys"""
        return iter(self._distmap.keys())

    def __contains__(self,name):
        """Has a distribution named `name` ever been added to this map?"""
        return name.lower() in self._distmap

    def __len__(self): return len(self._distmap)

    def get(self,key,default=None):
        """Return ``self[key]`` if `key` in self, otherwise return `default`"""
        if key in self:
            return self[key]
        else:
            return default

    def scan(self, search_path=None):
        """Scan `search_path` for distributions usable on `platform`

        Any distributions found are added to the distribution map.
        `search_path` should be a sequence of ``sys.path`` items.  If not
        supplied, ``sys.path`` is used.  Only distributions conforming to
        the platform/python version defined at initialization are added.
        """
        if search_path is None:
            search_path = sys.path

        for item in search_path:
            for dist in find_distributions(item):
                self.add(dist)

    def __getitem__(self,key):
        """Return a newest-to-oldest list of distributions for the given key

        The returned list may be modified in-place, e.g. for narrowing down
        usable distributions.
        """
        try:
            return self._cache[key]
        except KeyError:
            key = key.lower()
            if key not in self._distmap:
                raise

        if key not in self._cache:
            dists = self._cache[key] = self._distmap[key]
            _sort_dists(dists)

        return self._cache[key]

    def add(self,dist):
        """Add `dist` to the distribution map, only if it's suitable"""
        if self.can_add(dist):
            self._distmap.setdefault(dist.key,[]).append(dist)
            if dist.key in self._cache:
                _sort_dists(self._cache[dist.key])

    def remove(self,dist):
        """Remove `dist` from the distribution map"""
        self._distmap[dist.key].remove(dist)

    def best_match(self,requirement,path=None):
        """Find distribution best matching `requirement` and usable on `path`

        If a distribution that's already installed on `path` is unsuitable,
        a VersionConflict is raised.  If one or more suitable distributions are
        already installed, the leftmost distribution (i.e., the one first in
        the search path) is returned.  Otherwise, the available distribution
        with the highest version number is returned, or a deferred distribution
        object is returned if a suitable ``obtain()`` method exists.  If there
        is no way to meet the requirement, None is returned.
        """
        if path is None:
            path = sys.path

        distros = self.get(requirement.key, ())
        find = dict([(dist.path,dist) for dist in distros]).get

        for item in path:
            dist = find(item)
            if dist is not None:
                if dist in requirement:
                    return dist
                else:
                    raise VersionConflict(dist,requirement) # XXX add more info

        for dist in distros:
            if dist in requirement:
                return dist
        return self.obtain(requirement) # try and download

    def resolve(self, requirements, path=None):
        """List all distributions needed to (recursively) meet requirements"""

        if path is None:
            path = sys.path

        requirements = list(requirements)[::-1]  # set up the stack
        processed = {}  # set of processed requirements
        best = {}       # key -> dist
        to_install = []

        while requirements:
            req = requirements.pop()
            if req in processed:
                # Ignore cyclic or redundant dependencies
                continue

            dist = best.get(req.key)

            if dist is None:
                # Find the best distribution and add it to the map
                dist = best[req.key] = self.best_match(req,path)
                if dist is None:
                    raise DistributionNotFound(req)  # XXX put more info here
                to_install.append(dist)

            elif dist not in req:
                # Oops, the "best" so far conflicts with a dependency
                raise VersionConflict(req,dist) # XXX put more info here

            requirements.extend(dist.depends(req.options)[::-1])
            processed[req] = True

        return to_install    # return list of distros to install


    def obtain(self, requirement):
        """Obtain a distro that matches requirement (e.g. via download)"""
        return None     # override this in subclasses


class ResourceManager:
    """Manage resource extraction and packages"""

    extraction_path = None

    def __init__(self):
        self.cached_files = []

    def resource_exists(self, package_name, resource_name):
        """Does the named resource exist in the named package?"""
        return get_provider(package_name).has_resource(self, resource_name)

    def resource_isdir(self, package_name, resource_name):
        """Does the named resource exist in the named package?"""
        return get_provider(package_name).resource_isdir(self, resource_name)

    def resource_filename(self, package_name, resource_name):
        """Return a true filesystem path for specified resource"""
        return get_provider(package_name).get_resource_filename(
            self,resource_name
        )

    def resource_stream(self, package_name, resource_name):
        """Return a readable file-like object for specified resource"""
        return get_provider(package_name).get_resource_stream(
            self, resource_name
        )

    def resource_string(self, package_name, resource_name):
        """Return specified resource as a string"""
        return get_provider(package_name).get_resource_string(
            self, resource_name
        )

    def list_resources(self,  package_name, resource_name):
        return get_provider(package_name).resource_listdir(self, resource_name)





    def get_cache_path(self, archive_name, names=()):
        """Return absolute location in cache for `archive_name` and `names`

        The parent directory of the resulting path will be created if it does
        not already exist.  `archive_name` should be the base filename of the
        enclosing egg (which may not be the name of the enclosing zipfile!),
        including the ".egg" extension.  `names`, if provided, should be a
        sequence of path name parts "under" the egg's extraction location.

        This method should only be called by resource providers that need to
        obtain an extraction location, and only for names they intend to
        extract, as it tracks the generated names for possible cleanup later.
        """
        extract_path = self.extraction_path
        extract_path = extract_path or os.path.expanduser('~/.python-eggs')
        target_path = os.path.join(extract_path, archive_name, *names)
        ensure_directory(target_path)
        self.cached_files.append(target_path)
        return target_path


    def postprocess(self, filename):
        """Perform any platform-specific postprocessing of file `filename`

        This is where Mac header rewrites should be done; other platforms don't
        have anything special they should do.

        Resource providers should call this method ONLY after successfully
        extracting a compressed resource.  They must NOT call it on resources
        that are already in the filesystem.
        """
        # XXX









    def set_extraction_path(self, path):
        """Set the base path where resources will be extracted to, if needed.

        If not set, this defaults to ``os.expanduser("~/.python-eggs")``.
        Resources are extracted to subdirectories of this path based upon
        information given by the ``IResourceProvider``.  You may set this to a
        temporary directory, but then you must call ``cleanup_resources()`` to
        delete the extracted files when done.  There is no guarantee that
        ``cleanup_resources()`` will be able to remove all extracted files.

        (Note: you may not change the extraction path for a given resource
        manager once resources have been extracted, unless you first call
        ``cleanup_resources()``.)
        """
        if self.cached_files:
            raise ValueError(
                "Can't change extraction path, files already extracted"
            )

        self.extraction_path = path

    def cleanup_resources(self, force=False):
        """
        Delete all extracted resource files and directories, returning a list
        of the file and directory names that could not be successfully removed.
        This function does not have any concurrency protection, so it should
        generally only be called when the extraction path is a temporary
        directory exclusive to a single process.  This method is not
        automatically called; you must call it explicitly or register it as an
        ``atexit`` function if you wish to ensure cleanup of a temporary
        directory used for extractions.
        """
        # XXX








def require(*requirements):
    """Ensure that distributions matching `requirements` are on ``sys.path``

    `requirements` must be a string or a (possibly-nested) sequence
    thereof, specifying the distributions and versions required.

    XXX This doesn't support arbitrary PEP 302 sys.path items yet, because
    ``find_distributions()`` is hardcoded at the moment.
    """

    requirements = parse_requirements(requirements)
    to_install = AvailableDistributions().resolve(requirements)
    for dist in to_install:
        dist.install_on(sys.path)
    return to_install


def safe_name(name):
    """Convert an arbitrary string to a standard distribution name

    Any runs of non-alphanumeric characters are replaced with a single '-'.
    """
    return re.sub('[^A-Za-z0-9]+', '-', name)


def safe_version(version):
    """Convert an arbitrary string to a standard version string

    Spaces become dots, and all other non-alphanumeric characters become
    dashes, with runs of multiple dashes condensed to a single dash.
    """
    version = version.replace(' ','.')
    return re.sub('[^A-Za-z0-9.]+', '-', version)








class NullProvider:
    """Try to implement resources and metadata for arbitrary PEP 302 loaders"""

    egg_name = None
    egg_info = None
    loader = None

    def __init__(self, module):
        self.loader = getattr(module, '__loader__', None)
        self.module_path = os.path.dirname(getattr(module, '__file__', ''))

    def get_resource_filename(self, manager, resource_name):
        return self._fn(self.module_path, resource_name)

    def get_resource_stream(self, manager, resource_name):
        return open(self._fn(self.module_path, resource_name), 'rb')

    def get_resource_string(self, manager, resource_name):
        return self._get(self._fn(self.module_path, resource_name))

    def has_resource(self, resource_name):
        return self._has(self._fn(self.module_path, resource_name))

    def has_metadata(self, name):
        return self.egg_info and self._has(self._fn(self.egg_info,name))

    def get_metadata(self, name):
        if not self.egg_info:
            return ""
        return self._get(self._fn(self.egg_info,name))

    def get_metadata_lines(self, name):
        return yield_lines(self.get_metadata(name))

    def resource_isdir(self,resource_name):
        return self._isdir(self._fn(self.module_path, resource_name))

    def metadata_isdir(self,name):
        return self.egg_info and self._isdir(self._fn(self.egg_info,name))


    def resource_listdir(self,resource_name):
        return self._listdir(self._fn(self.egg_info,resource_name))

    def metadata_listdir(self,name):
        if self.egg_info:
            return self._listdir(self._fn(self.egg_info,name))
        return []

    def run_script(self,script_name,namespace):
        script = 'scripts/'+script_name
        if not self.has_metadata(script):
            raise ResolutionError("No script named %r" % script_name)
        script_text = self.get_metadata(script).replace('\r\n','\n')
        script_text = script_text.replace('\r','\n')
        script_filename = self._fn(self.egg_info,script)
        namespace['__file__'] = script_filename
        if os.path.exists(script_filename):
            execfile(script_filename, namespace, namespace)
        else:
            from linecache import cache
            cache[script_filename] = (
                len(script_text), 0, script_text.split('\n'), script_filename
            )
            script_code = compile(script_text,script_filename,'exec')
            exec script_code in namespace, namespace

    def _has(self, path):
        raise NotImplementedError(
            "Can't perform this operation for unregistered loader type"
        )

    def _isdir(self, path):
        raise NotImplementedError(
            "Can't perform this operation for unregistered loader type"
        )

    def _listdir(self, path):
        raise NotImplementedError(
            "Can't perform this operation for unregistered loader type"
        )

    def _fn(self, base, resource_name):
        return os.path.join(base, *resource_name.split('/'))

    def _get(self, path):
        if hasattr(self.loader, 'get_data'):
            return self.loader.get_data(path)
        raise NotImplementedError(
            "Can't perform this operation for loaders without 'get_data()'"
        )

register_loader_type(object, NullProvider)






























class DefaultProvider(NullProvider):
    """Provides access to package resources in the filesystem"""

    def __init__(self,module):
        NullProvider.__init__(self,module)
        self._setup_prefix()

    def _setup_prefix(self):
        # we assume here that our metadata may be nested inside a "basket"
        # of multiple eggs; that's why we use module_path instead of .archive
        path = self.module_path
        old = None
        self.prefix = []
        while path!=old:
            if path.lower().endswith('.egg'):
                self.egg_name = os.path.basename(path)
                self.egg_info = os.path.join(path, 'EGG-INFO')
                break
            old = path
            path, base = os.path.split(path)
            self.prefix.append(base)

    def _has(self, path):
        return os.path.exists(path)

    def _isdir(self,path):
        return os.path.isdir(path)

    def _listdir(self,path):
        return os.listdir(path)

    def _get(self, path):
        stream = open(path, 'rb')
        try:
            return stream.read()
        finally:
            stream.close()

register_loader_type(type(None), DefaultProvider)


class ZipProvider(DefaultProvider):
    """Resource support for zips and eggs"""

    eagers = None

    def __init__(self, module):
        DefaultProvider.__init__(self,module)
        self.zipinfo = zipimport._zip_directory_cache[self.loader.archive]
        self.zip_pre = self.loader.archive+os.sep

    def _short_name(self, path):
        if path.startswith(self.zip_pre):
            return path[len(self.zip_pre):]
        return path

    def get_resource_stream(self, manager, resource_name):
        return StringIO(self.get_resource_string(manager, resource_name))

    def get_resource_filename(self, manager, resource_name):
        if not self.egg_name:
            raise NotImplementedError(
                "resource_filename() only supported for .egg, not .zip"
            )

        # should lock for extraction here
        eagers = self._get_eager_resources()
        if resource_name in eagers:
            for name in eagers:
                self._extract_resource(manager, name)

        return self._extract_resource(manager, resource_name)

    def _extract_directory(self, manager, resource_name):
        if resource_name.endswith('/'):
            resource_name = resource_name[:-1]
        for resource in self.resource_listdir(resource_name):
            last = self._extract_resource(manager, resource_name+'/'+resource)
        return os.path.dirname(last)    # return the directory path



    def _extract_resource(self, manager, resource_name):
        if self.resource_isdir(resource_name):
            return self._extract_dir(resource_name)

        parts = resource_name.split('/')
        zip_path = os.path.join(self.module_path, *parts)
        zip_stat = self.zipinfo[os.path.join(*self.prefix+parts)]
        t,d,size = zip_stat[5], zip_stat[6], zip_stat[3]
        date_time = (
            (d>>9)+1980, (d>>5)&0xF, d&0x1F,                      # ymd
            (t&0xFFFF)>>11, (t>>5)&0x3F, (t&0x1F) * 2, 0, 0, -1   # hms, etc.
        )
        timestamp = time.mktime(date_time)
        real_path = manager.get_cache_path(self.egg_name, self.prefix+parts)

        if os.path.isfile(real_path):
            stat = os.stat(real_path)
            if stat.st_size==size and stat.st_mtime==timestamp:
                # size and stamp match, don't bother extracting
                return real_path

        # print "extracting", zip_path

        data = self.loader.get_data(zip_path)
        open(real_path, 'wb').write(data)
        os.utime(real_path, (timestamp,timestamp))
        manager.postprocess(real_path)
        return real_path

    def _get_eager_resources(self):
        if self.eagers is None:
            eagers = []
            for name in ('native_libs.txt', 'eager_resources.txt'):
                if self.has_metadata(name):
                    eagers.extend(self.get_metadata_lines(name))
            self.eagers = eagers
        return self.eagers




    def _index(self):
        try:
            return self._dirindex
        except AttributeError:
            ind = {}; skip = len(self.prefix)
            for path in self.zipinfo:
                parts = path.split(os.sep)
                if parts[:skip] != self.prefix:
                    continue    # only include items under our prefix
                parts = parts[skip:]   # but don't include prefix in paths
                while parts:
                    parent = '/'.join(parts[:-1])
                    if parent in ind:
                        ind[parent].append(parts[-1])
                        break
                    else:
                        ind[parent] = [parts.pop()]
            self._dirindex = ind
            return ind

    def _has(self, path):
        return self._short_name(path) in self.zipinfo or self._isdir(path)

    def _isdir(self,path):
        path = self._short_name(path).replace(os.sep, '/')
        if path.endswith('/'): path = path[:-1]
        return path in self._index()

    def _listdir(self,path):
        path = self._short_name(path).replace(os.sep, '/')
        if path.endswith('/'): path = path[:-1]
        return list(self._index().get(path, ()))

    _get = NullProvider._get


register_loader_type(zipimport.zipimporter, ZipProvider)




class PathMetadata(DefaultProvider):
    """Metadata provider for egg directories

    Usage::

        # Development eggs:

        egg_info = "/path/to/PackageName.egg-info"
        base_dir = os.path.dirname(egg_info)
        metadata = PathMetadata(base_dir, egg_info)
        dist_name = os.path.splitext(os.path.basename(egg_info))[0]
        dist = Distribution(basedir,name=dist_name,metadata=metadata)

        # Unpacked egg directories:

        egg_path = "/path/to/PackageName-ver-pyver-etc.egg"
        metadata = PathMetadata(egg_path, os.path.join(egg_path,'EGG-INFO'))
        dist = Distribution.from_filename(egg_path, metadata=metadata)
    """

    def __init__(self, path, egg_info):
        self.module_path = path
        self.egg_info = egg_info


class EggMetadata(ZipProvider):
    """Metadata provider for .egg files"""

    def __init__(self, importer):
        """Create a metadata provider from a zipimporter"""

        self.zipinfo = zipimport._zip_directory_cache[importer.archive]
        self.zip_pre = importer.archive+os.sep
        self.loader = importer
        if importer.prefix:
            self.module_path = os.path.join(importer.archive, importer.prefix)
        else:
            self.module_path = importer.archive
        self._setup_prefix()


class ImpWrapper:
    """PEP 302 Importer that wraps Python's "normal" import algorithm"""

    def __init__(self, path=None):
        if path is not None and not os.path.isdir(path):
            raise ImportError
        self.path = path

    def find_module(self, fullname, path=None):
        subname = fullname.split(".")[-1]
        if subname != fullname and self.path is None:
            return None
        if self.path is None:
            path = None
        else:
            path = [self.path]
        try:
            file, filename, etc = imp.find_module(subname, path)
        except ImportError:
            return None
        return ImpLoader(file, filename, etc)


class ImpLoader:
    """PEP 302 Loader that wraps Python's "normal" import algorithm"""

    def __init__(self, file, filename, etc):
        self.file = file
        self.filename = filename
        self.etc = etc

    def load_module(self, fullname):
        try:
            mod = imp.load_module(fullname, self.file, self.filename, self.etc)
        finally:
            if self.file: self.file.close()
        # Note: we don't set __loader__ because we want the module to look
        # normal; i.e. this is just a wrapper for standard import machinery
        return mod


def get_importer(path_item):
    """Retrieve a PEP 302 "importer" for the given path item

    If there is no importer, this returns a wrapper around the builtin import
    machinery.  The returned importer is only cached if it was created by a
    path hook.
    """
    try:
        importer = sys.path_importer_cache[path_item]
    except KeyError:
        for hook in sys.path_hooks:
            try:
                importer = hook(path_item)
            except ImportError:
                pass
            else:
                break
        else:
            importer = None

    sys.path_importer_cache.setdefault(path_item,importer)
    if importer is None:
        try:
            importer = ImpWrapper(path_item)
        except ImportError:
            pass
    return importer














_distribution_finders = {}

def register_finder(importer_type, distribution_finder):
    """Register `distribution_finder` to find distributions in sys.path items

    `importer_type` is the type or class of a PEP 302 "Importer" (sys.path item
    handler), and `distribution_finder` is a callable that, passed a path
    item and the importer instance, yields ``Distribution`` instances found on
    that path item.  See ``pkg_resources.find_on_path`` for an example."""
    _distribution_finders[importer_type] = distribution_finder


def find_distributions(path_item):
    """Yield distributions accessible via `path_item`"""
    importer = get_importer(path_item)
    finder = _find_adapter(_distribution_finders, importer)
    return finder(importer,path_item)

def find_in_zip(importer,path_item):
    metadata = EggMetadata(importer)
    if metadata.has_metadata('PKG-INFO'):
        yield Distribution.from_filename(path_item, metadata=metadata)
    for subitem in metadata.resource_listdir('/'):
        if subitem.endswith('.egg'):
            subpath = os.path.join(path_item, subitem)
            for dist in find_in_zip(zipimport.zipimporter(subpath), subpath):
                yield dist

register_finder(zipimport.zipimporter,find_in_zip)


def StringIO(*args, **kw):
    """Thunk to load the real StringIO on demand"""
    global StringIO
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    return StringIO(*args,**kw)


def find_nothing(importer,path_item):
    return ()

register_finder(object,find_nothing)


def find_on_path(importer,path_item):
    """Yield distributions accessible on a sys.path directory"""
    if not os.path.exists(path_item):
        return
    elif os.path.isdir(path_item):
        if path_item.lower().endswith('.egg'):
            # unpacked egg
            yield Distribution.from_filename(
                path_item, metadata=PathMetadata(
                    path_item,os.path.join(path_item,'EGG-INFO')
                )
            )
        else:
            # scan for .egg and .egg-info in directory
            for entry in os.listdir(path_item):
                fullpath = os.path.join(path_item, entry)
                if entry.lower().endswith('.egg'):
                    for dist in find_on_path(importer,fullpath):
                        yield dist
                elif entry.lower().endswith('.egg-info'):
                    if os.path.isdir(fullpath):
                        # development egg
                        metadata = PathMetadata(path_item, fullpath)
                        dist_name = os.path.splitext(entry)[0]
                        yield Distribution(path_item,metadata,name=dist_name)
    elif path_item.lower().endswith('.egg'):
        # packed egg
        metadata = EggMetadata(zipimport.zipimporter(path_item))
        yield Distribution.from_filename(path_item, metadata=metadata)

register_finder(ImpWrapper,find_on_path)




_namespace_handlers = {}
_namespace_packages = {}

def register_namespace_handler(importer_type, namespace_handler):
    """Register `namespace_handler` to declare namespace packages

    `importer_type` is the type or class of a PEP 302 "Importer" (sys.path item
    handler), and `namespace_handler` is a callable like this::

        def namespace_handler(importer,path_entry,moduleName,module):
            # return a path_entry to use for child packages

    Namespace handlers are only called if the importer object has already
    agreed that it can handle the relevant path item, and they should only
    return a subpath if the module __path__ does not already contain an
    equivalent subpath.  For an example namespace handler, see
    ``pkg_resources.file_ns_handler``.
    """
    _namespace_handlers[importer_type] = namespace_handler


def _handle_ns(packageName, path_item):
    """Ensure that named package includes a subpath of path_item (if needed)"""
    importer = get_importer(path_item)
    if importer is None:
        return None
    loader = importer.find_module(packageName)
    if loader is None:
        return None

    module = sys.modules.get(packageName) or loader.load_module(packageName)
    if not hasattr(module,'__path__'):
        raise TypeError("Not a package:", packageName)

    handler = _find_adapter(_namespace_handlers, importer)
    subpath = handler(importer,path_item,packageName,module)
    if subpath is not None:
        module.__path__.append(subpath)
    return subpath


def declare_namespace(packageName):
    """Declare that package 'packageName' is a namespace package"""

    imp.acquire_lock()
    try:
        if packageName in _namespace_packages:
            return

        path, parent = sys.path, None
        if '.' in packageName:
            parent = '.'.join(package.split('.')[:-1])
            declare_namespace(parent)
            __import__(parent)
            try:
                path = sys.modules[parent].__path__
            except AttributeError:
                raise TypeError("Not a package:", parent)

        for path_item in path:
            # Ensure all the parent's path items are reflected in the child,
            # if they apply
            _handle_ns(packageName, path_item)

        # Track what packages are namespaces, so when new path items are added,
        # they can be updated
        _namespace_packages.setdefault(parent,[]).append(packageName)
        _namespace_packages.setdefault(packageName,[])

    finally:
        imp.release_lock()

def fixup_namespace_packages(path_item, parent=None):
    """Ensure that previously-declared namespace packages include path_item"""
    imp.acquire_lock()
    try:
        for package in _namespace_packages.get(parent,()):
            subpath = _handle_ns(package, path_item)
            if subpath: fixup_namespace_packages(subpath,package)
    finally:
        imp.release_lock()

def file_ns_handler(importer, path_item, packageName, module):
    """Compute an ns-package subpath for a filesystem or zipfile importer"""

    subpath = os.path.join(path_item, packageName.split('.')[-1])
    normalized = os.path.normpath(os.path.normcase(subpath))
    for item in module.__path__:
        if os.path.normpath(os.path.normcase(item))==normalized:
            break
    else:
        # Only return the path if it's not already there
        return subpath

register_namespace_handler(ImpWrapper,file_ns_handler)
register_namespace_handler(zipimport.zipimporter,file_ns_handler)


def null_ns_handler(importer, path_item, packageName, module):
    return None

register_namespace_handler(object,null_ns_handler)





















def yield_lines(strs):
    """Yield non-empty/non-comment lines of a ``basestring`` or sequence"""
    if isinstance(strs,basestring):
        for s in strs.splitlines():
            s = s.strip()
            if s and not s.startswith('#'):     # skip blank lines/comments
                yield s
    else:
        for ss in strs:
            for s in yield_lines(ss):
                yield s

LINE_END = re.compile(r"\s*(#.*)?$").match         # whitespace and comment
CONTINUE = re.compile(r"\s*\\\s*(#.*)?$").match    # line continuation
DISTRO   = re.compile(r"\s*(\w+)").match           # Distribution or option
VERSION  = re.compile(r"\s*(<=?|>=?|==|!=)\s*((\w|\.)+)").match  # version info
COMMA    = re.compile(r"\s*,").match               # comma between items
OBRACKET = re.compile(r"\s*\[").match
CBRACKET = re.compile(r"\s*\]").match

EGG_NAME = re.compile(
    r"(?P<name>[^-]+)"
    r"( -(?P<ver>[^-]+) (-py(?P<pyver>[^-]+) (-(?P<plat>.+))? )? )?",
    re.VERBOSE | re.IGNORECASE
).match

component_re = re.compile(r'(\d+ | [a-z]+ | \.| -)', re.VERBOSE)
replace = {'pre':'c', 'preview':'c','-':'final-','rc':'c'}.get

def _parse_version_parts(s):
    for part in component_re.split(s):
        part = replace(part,part)
        if not part or part=='.':
            continue
        if part[:1] in '0123456789':
            yield part.zfill(8)    # pad for numeric comparison
        else:
            yield '*'+part

    yield '*final'  # ensure that alpha/beta/candidate are before final

def parse_version(s):
    """Convert a version string to a sortable key

    This is a rough cross between distutils' StrictVersion and LooseVersion;
    if you give it versions that would work with StrictVersion, then it behaves
    the same; otherwise it acts like a slightly-smarter LooseVersion.

    The returned value will be a tuple of strings.  Numeric portions of the
    version are padded to 8 digits so they will compare numerically, but
    without relying on how numbers compare relative to strings.  Dots are
    dropped, but dashes are retained.  Trailing zeros between alpha segments
    or dashes are suppressed, so that e.g. 2.4.0 is considered the same as 2.4.
    Alphanumeric parts are lower-cased.

    The algorithm assumes that strings like '-' and any alpha string > "final"
    represents a "patch level".  So, "2.4-1" is assumed to be a branch or patch
    of "2.4", and therefore "2.4.1" is considered newer than "2.4-1".

    Strings like "a", "b", "c", "alpha", "beta", "candidate" and so on (that
    come before "final" alphabetically) are assumed to be pre-release versions,
    and so the version "2.4" is considered newer than "2.4a1".

    Finally, to handle miscellaneous cases, the strings "pre", "preview", and
    "rc" are treated as if they were "c", i.e. as though they were release
    candidates, and therefore are not as new as a version string that does not
    contain them.
    """
    parts = []
    for part in _parse_version_parts(s.lower()):
        if part.startswith('*'):
            # remove trailing zeros from each series of numeric parts
            while parts and parts[-1]=='00000000':
                parts.pop()
        parts.append(part)
    return tuple(parts)






class Distribution(object):
    """Wrap an actual or potential sys.path entry w/metadata"""

    def __init__(self,
        path_str, metadata=None, name=None, version=None,
        py_version=PY_MAJOR, platform=None, distro_type = EGG_DIST
    ):
        if name:
            self.name = safe_name(name)
        if version is not None:
            self._version = safe_version(version)
        self.py_version = py_version
        self.platform = platform
        self.path = path_str
        self.distro_type = distro_type
        self.metadata = metadata

    def installed_on(self,path=None):
        """Is this distro installed on `path`? (defaults to ``sys.path``)"""
        if path is None:
            path = sys.path
        return self.path in path

    #@classmethod
    def from_filename(cls,filename,metadata=None):
        name,version,py_version,platform = [None]*4
        basename,ext = os.path.splitext(os.path.basename(filename))
        if ext.lower()==".egg":
            match = EGG_NAME(basename)
            if match:
                name,version,py_version,platform = match.group(
                    'name','ver','pyver','plat'
                )
        return cls(
            filename, metadata, name=name, version=version,
            py_version=py_version or PY_MAJOR, platform=platform
        )
    from_filename = classmethod(from_filename)



    # These properties have to be lazy so that we don't have to load any
    # metadata until/unless it's actually needed.  (i.e., some distributions
    # may not know their name or version without loading PKG-INFO)

    #@property
    def key(self):
        try:
            return self._key
        except AttributeError:
            self._key = key = self.name.lower()
            return key
    key = property(key)

    #@property
    def parsed_version(self):
        try:
            return self._parsed_version
        except AttributeError:
            self._parsed_version = pv = parse_version(self.version)
            return pv

    parsed_version = property(parsed_version)

    #@property
    def version(self):
        try:
            return self._version
        except AttributeError:
            for line in self._get_metadata('PKG-INFO'):
                if line.lower().startswith('version:'):
                    self._version = line.split(':',1)[1].strip()
                    return self._version
            else:
                raise AttributeError(
                    "Missing 'Version:' header in PKG-INFO", self
                )
    version = property(version)

        


    #@property
    def _dep_map(self):
        try:
            return self.__dep_map
        except AttributeError:
            dm = self.__dep_map = {None: []}
            for section,contents in split_sections(
                self._get_metadata('depends.txt')
            ):
                dm[section] = list(parse_requirements(contents))
            return dm

    _dep_map = property(_dep_map)

    def depends(self,options=()):
        """List of Requirements needed for this distro if `options` are used"""
        dm = self._dep_map
        deps = []
        deps.extend(dm.get(None,()))

        for opt in options:
            try:
                deps.extend(dm[opt.lower()])
            except KeyError:
                raise InvalidOption("No such option", self, opt)
        return deps

    def _get_metadata(self,name):
        if self.metadata is not None and self.metadata.has_metadata(name):
            for line in self.metadata.get_metadata_lines(name):
                yield line

    def install_on(self,path=None):
        """Ensure distribution is importable on `path` (default=sys.path)"""
        if path is None: path = sys.path
        if self.path not in path:
            path.append(self.path)
        if path is sys.path:
            fixup_namespace_packages(self.path)
            map(declare_namespace, self._get_metadata('namespace_packages.txt'))

    def egg_name(self):
        """Return what this distribution's standard .egg filename should be"""
        filename = "%s-%s-py%s" % (
            self.name.replace('-','_'), self.version.replace('-','_'),
            self.py_version or PY_MAJOR
        )

        if self.platform:
            filename += '-'+self.platform

        return filename

    def __repr__(self):
        return "%s (%s)" % (self,self.path)

    def __str__(self):
        version = getattr(self,'version',None) or "[unknown version]"
        return "%s %s" % (self.name,version)























def parse_requirements(strs):
    """Yield ``Requirement`` objects for each specification in `strs`

    `strs` must be an instance of ``basestring``, or a (possibly-nested)
    iterable thereof.
    """
    # create a steppable iterator, so we can handle \-continuations
    lines = iter(yield_lines(strs))

    def scan_list(ITEM,TERMINATOR,line,p,groups,item_name):

        items = []

        while not TERMINATOR(line,p):
            if CONTINUE(line,p):
                try:
                    line = lines.next().replace('-','_'); p = 0
                except StopIteration:
                    raise ValueError(
                        "\\ must not appear on the last nonblank line"
                    )

            match = ITEM(line,p)
            if not match:
                raise ValueError("Expected "+item_name+" in",line,"at",line[p:])

            items.append(match.group(*groups))
            p = match.end()

            match = COMMA(line,p)
            if match:
                p = match.end() # skip the comma
            elif not TERMINATOR(line,p):
                raise ValueError(
                    "Expected ',' or end-of-list in",line,"at",line[p:]
                )

        match = TERMINATOR(line,p)
        if match: p = match.end()   # skip the terminator, if any
        return line, p, items

    for line in lines:
        line = line.replace('-','_')
        match = DISTRO(line)
        if not match:
            raise ValueError("Missing distribution spec", line)
        distname = match.group(1)
        p = match.end()
        options = []

        match = OBRACKET(line,p)
        if match:
            p = match.end()
            line, p, options = scan_list(DISTRO,CBRACKET,line,p,(1,),"option")

        line, p, specs = scan_list(VERSION,LINE_END,line,p,(1,2),"version spec")
        specs = [(op,val.replace('_','-')) for op,val in specs]
        yield Requirement(distname.replace('_','-'), specs, options)


def _sort_dists(dists):
    tmp = [(dist.version,dist.distro_type,dist) for dist in dists]
    tmp.sort()
    dists[::-1] = [d for v,t,d in tmp]


















class Requirement:

    def __init__(self, distname, specs=(), options=()):
        self.distname = distname
        self.key = distname.lower()
        index = [(parse_version(v),state_machine[op],op,v) for op,v in specs]
        index.sort()
        self.specs = [(op,ver) for parsed,trans,op,ver in index]
        self.index, self.options = index, tuple(options)
        self.hashCmp = (
            self.key, tuple([(op,parsed) for parsed,trans,op,ver in index]),
            ImmutableSet(map(str.lower,options))
        )
        self.__hash = hash(self.hashCmp)

    def __str__(self):
        return self.distname + ','.join([''.join(s) for s in self.specs])

    def __repr__(self):
        return "Requirement(%r, %r, %r)" % \
            (self.distname,self.specs,self.options)

    def __eq__(self,other):
        return isinstance(other,Requirement) and self.hashCmp==other.hashCmp

    def __contains__(self,item):
        if isinstance(item,Distribution):
            if item.key <> self.key: return False
            item = item.parsed_version
        elif isinstance(item,basestring):
            item = parse_version(item)
        last = None
        for parsed,trans,op,ver in self.index:
            action = trans[cmp(item,parsed)]
            if action=='F':     return False
            elif action=='T':   return True
            elif action=='+':   last = True
            elif action=='-' or last is None:   last = False
        if last is None: last = True    # no rules encountered
        return last

    def __hash__(self):
        return self.__hash

    #@staticmethod
    def parse(s):
        reqs = list(parse_requirements(s))
        if reqs:
            if len(reqs)==1:
                return reqs[0]
            raise ValueError("Expected only one requirement", s)
        raise ValueError("No requirements found", s)

    parse = staticmethod(parse)


state_machine = {
    #       =><
    '<' :  '--T',
    '<=':  'T-T',
    '>' :  'F+F',
    '>=':  'T+F',
    '==':  'T..',
    '!=':  'F++',
}


def _get_mro(cls):
    """Get an mro for a type or classic class"""
    if not isinstance(cls,type):
        class cls(cls,object): pass
        return cls.__mro__[1:]
    return cls.__mro__


def _find_adapter(registry, ob):
    """Return an adapter factory for `ob` from `registry`"""
    for t in _get_mro(getattr(ob, '__class__', type(ob))):
        if t in registry:
            return registry[t]


def ensure_directory(path):
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def split_sections(s):
    """Split a string or iterable thereof into (section,content) pairs

    Each ``section`` is a lowercase version of the section header ("[section]")
    and each ``content`` is a list of stripped lines excluding blank lines and
    comment-only lines.  If there are any such lines before the first section
    header, they're returned in a first ``section`` of ``None``.
    """
    section = None
    content = []
    for line in yield_lines(s):
        if line.startswith("["):
            if line.endswith("]"):
                if section or content:
                    yield section, content
                section = line[1:-1].strip().lower()
                content = []
            else:
                raise ValueError("Invalid section heading", line)
        else:
            content.append(line)

    # wrap up last segment
    yield section, content











# Set up global resource manager

_manager = ResourceManager()

def _initialize(g):
    for name in dir(_manager):
        if not name.startswith('_'):
            g[name] = getattr(_manager, name)
_initialize(globals())
































