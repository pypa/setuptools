"""Utility functions to expand configuration directives or special values
(such glob patterns).

We can split the process of interpreting configuration files into 2 steps:

1. The parsing the file contents from strings to value objects
   that can be understand by Python (for example a string with a comma
   separated list of keywords into an actual Python list of strings).

2. The expansion (or post-processing) of these values according to the
   semantics ``setuptools`` assign to them (for example a configuration field
   with the ``file:`` directive should be expanded from a list of file paths to
   a single string with the contents of those files concatenated)

This module focus on the second step, and therefore allow sharing the expansion
functions among several configuration file formats.
"""
import ast
import contextlib
import importlib
import io
import os
import sys
from glob import iglob
from itertools import chain

from distutils.errors import DistutilsOptionError

chain_iter = chain.from_iterable


class StaticModule:
    """
    Attempt to load the module by the name
    """

    def __init__(self, name):
        spec = importlib.util.find_spec(name)
        if spec is None:
            raise ModuleNotFoundError(name)
        with open(spec.origin) as strm:
            src = strm.read()
        module = ast.parse(src)
        vars(self).update(locals())
        del self.self

    def __getattr__(self, attr):
        try:
            return next(
                ast.literal_eval(statement.value)
                for statement in self.module.body
                if isinstance(statement, ast.Assign)
                for target in statement.targets
                if isinstance(target, ast.Name) and target.id == attr
            )
        except Exception as e:
            raise AttributeError(
                "{self.name} has no attribute {attr}".format(**locals())
            ) from e


@contextlib.contextmanager
def patch_path(path):
    """
    Add path to front of sys.path for the duration of the context.
    """
    try:
        sys.path.insert(0, path)
        yield
    finally:
        sys.path.remove(path)


def glob_relative(patterns, root_dir=None):
    """Expand the list of glob patterns, but preserving relative paths.

    :param list[str] patterns: List of glob patterns
    :param str root_dir: Path to which globs should be relative
                         (current directory by default)
    :rtype: list
    """
    glob_characters = ('*', '?', '[', ']', '{', '}')
    expanded_values = []
    root_dir = root_dir or os.getcwd()
    for value in patterns:

        # Has globby characters?
        if any(char in value for char in glob_characters):
            # then expand the glob pattern while keeping paths *relative*:
            glob_path = os.path.abspath(os.path.join(root_dir, value))
            expanded_values.extend(sorted(
                os.path.relpath(path, root_dir)
                for path in iglob(glob_path, recursive=True)))

        else:
            # take the value as-is
            expanded_values.append(os.path.relpath(value, root_dir))

    return expanded_values


def read_files(filepaths, root_dir=None):
    """Return the content of the files concatenated using ``\n`` as str

    This function is sandboxed and won't reach anything outside ``root_dir``

    (By default ``root_dir`` is the current directory).
    """
    if isinstance(filepaths, (str, bytes)):
        filepaths = [filepaths]

    root_dir = os.path.abspath(root_dir or os.getcwd())
    _filepaths = (os.path.join(root_dir, path) for path in filepaths)
    return '\n'.join(
        _read_file(path)
        for path in _filepaths
        if _assert_local(path, root_dir) and os.path.isfile(path)
    )


def _read_file(filepath):
    with io.open(filepath, encoding='utf-8') as f:
        return f.read()


def _assert_local(filepath, root_dir):
    if not os.path.abspath(filepath).startswith(root_dir):
        msg = f"Cannot access {filepath!r} (or anything outside {root_dir!r})"
        raise DistutilsOptionError(msg)

    return True


def read_attr(attr_desc, package_dir=None, root_dir=None):
    """Reads the value of an attribute from a module.

    This function will try to read the attributed statically first
    (via :func:`ast.literal_eval`), and only evaluate the module if it fails.

    Examples:
        read_attr("package.attr")
        read_attr("package.module.attr")

    :param str attr_desc: Dot-separated string describing how to reach the
        attribute (see examples above)
    :param dict[str, str] package_dir: Mapping of package names to their
        location in disk (represented by paths relative to ``root_dir``).
    :param str root_dir: Path to directory containing all the packages in
        ``package_dir`` (current directory by default).
    :rtype: str
    """
    root_dir = root_dir or os.getcwd()
    attrs_path = attr_desc.strip().split('.')
    attr_name = attrs_path.pop()

    module_name = '.'.join(attrs_path)
    module_name = module_name or '__init__'

    parent_path = root_dir
    if package_dir:
        if attrs_path[0] in package_dir:
            # A custom path was specified for the module we want to import
            custom_path = package_dir[attrs_path[0]]
            parts = custom_path.rsplit('/', 1)
            if len(parts) > 1:
                parent_path = os.path.join(root_dir, parts[0])
                parent_module = parts[1]
            else:
                parent_module = custom_path
            module_name = ".".join([parent_module, *attrs_path[1:]])
        elif '' in package_dir:
            # A custom parent directory was specified for all root modules
            parent_path = os.path.join(root_dir, package_dir[''])

    with patch_path(parent_path):
        try:
            # attempt to load value statically
            return getattr(StaticModule(module_name), attr_name)
        except Exception:
            # fallback to simple import
            module = importlib.import_module(module_name)

    return getattr(module, attr_name)


def resolve_class(qualified_class_name):
    """Given a qualified class name, return the associated class object"""
    idx = qualified_class_name.rfind('.')
    class_name = qualified_class_name[idx + 1 :]
    pkg_name = qualified_class_name[:idx]
    module = importlib.import_module(pkg_name)
    return getattr(module, class_name)


def find_packages(namespaces=False, **kwargs):
    """Works similarly to :func:`setuptools.find_packages`, but with all
    arguments given as keyword arguments. Moreover, ``where`` can be given
    as a list (the results will be simply concatenated).

    When the additional keyword argument ``namespaces`` is ``True``, it will
    behave like :func:`setuptools.find_namespace_packages`` (i.e. include
    implicit namespaces as per :pep:`420`).

    :rtype: list
    """

    if namespaces:
        from setuptools import PEP420PackageFinder as PackageFinder
    else:
        from setuptools import PackageFinder

    where = kwargs.pop('where', ['.'])
    if isinstance(where, str):
        where = [where]

    return list(chain_iter(PackageFinder.find(x, **kwargs) for x in where))


def version(value):
    """When getting the version directly from an attribute,
    it should be normalised to string.
    """
    if callable(value):
        value = value()

    if not isinstance(value, str):
        if hasattr(value, '__iter__'):
            value = '.'.join(map(str, value))
        else:
            value = '%s' % value

    return value
