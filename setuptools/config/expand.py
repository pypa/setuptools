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
import importlib
import io
import os
import sys
from glob import iglob
from configparser import ConfigParser
from itertools import chain

from distutils.errors import DistutilsOptionError

chain_iter = chain.from_iterable


class StaticModule:
    """Proxy to a module object that avoids executing arbitrary code."""

    def __init__(self, name, spec):
        with open(spec.origin) as strm:
            src = strm.read()
        module = ast.parse(src)
        vars(self).update(locals())
        del self.self

    def __getattr__(self, attr):
        """Attempt to load an attribute "statically", via :func:`ast.literal_eval`."""
        try:
            assignment_expressions = (
                statement
                for statement in self.module.body
                if isinstance(statement, ast.Assign)
            )
            expressions_with_target = (
                (statement, target)
                for statement in assignment_expressions
                for target in statement.targets
            )
            matching_values = (
                statement.value
                for statement, target in expressions_with_target
                if isinstance(target, ast.Name) and target.id == attr
            )
            return next(ast.literal_eval(value) for value in matching_values)
        except Exception as e:
            raise AttributeError(f"{self.name} has no attribute {attr}") from e


def glob_relative(patterns, root_dir=None):
    """Expand the list of glob patterns, but preserving relative paths.

    :param list[str] patterns: List of glob patterns
    :param str root_dir: Path to which globs should be relative
                         (current directory by default)
    :rtype: list
    """
    glob_characters = {'*', '?', '[', ']', '{', '}'}
    expanded_values = []
    root_dir = root_dir or os.getcwd()
    for value in patterns:

        # Has globby characters?
        if any(char in value for char in glob_characters):
            # then expand the glob pattern while keeping paths *relative*:
            glob_path = os.path.abspath(os.path.join(root_dir, value))
            expanded_values.extend(sorted(
                os.path.relpath(path, root_dir).replace(os.sep, "/")
                for path in iglob(glob_path, recursive=True)))

        else:
            # take the value as-is
            path = os.path.relpath(value, root_dir).replace(os.sep, "/")
            expanded_values.append(path)

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
    parent_path, path, module_name = _find_module(module_name, package_dir, root_dir)
    spec = _find_spec(module_name, path, parent_path)

    try:
        return getattr(StaticModule(module_name, spec), attr_name)
    except Exception:
        # fallback to evaluate module
        module = _load_spec(spec, module_name)
        return getattr(module, attr_name)


def _find_spec(module_name, module_path, parent_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    spec = spec or importlib.util.find_spec(module_name)

    if spec is None:
        raise ModuleNotFoundError(module_name)

    return spec


def _load_spec(spec, module_name):
    name = getattr(spec, "__name__", module_name)
    if name in sys.modules:
        return sys.modules[name]
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # cache (it also ensures `==` works on loaded items)
    spec.loader.exec_module(module)
    return module


def _find_module(module_name, package_dir, root_dir):
    """Given a module (that could normally be imported by ``module_name``
    after the build is complete), find the path to the parent directory where
    it is contained and the canonical name that could be used to import it
    considering the ``package_dir`` in the build configuration and ``root_dir``
    """
    parent_path = root_dir
    module_parts = module_name.split('.')
    if package_dir:
        if module_parts[0] in package_dir:
            # A custom path was specified for the module we want to import
            custom_path = package_dir[module_parts[0]]
            parts = custom_path.rsplit('/', 1)
            if len(parts) > 1:
                parent_path = os.path.join(root_dir, parts[0])
                parent_module = parts[1]
            else:
                parent_module = custom_path
            module_name = ".".join([parent_module, *module_parts[1:]])
        elif '' in package_dir:
            # A custom parent directory was specified for all root modules
            parent_path = os.path.join(root_dir, package_dir[''])

    path_start = os.path.join(parent_path, *module_name.split("."))
    candidates = chain(
        (f"{path_start}.py", os.path.join(path_start, "__init__.py")),
        iglob(f"{path_start}.*")
    )
    module_path = next((x for x in candidates if os.path.isfile(x)), None)
    return parent_path, module_path, module_name


def resolve_class(qualified_class_name, package_dir=None, root_dir=None):
    """Given a qualified class name, return the associated class object"""
    root_dir = root_dir or os.getcwd()
    idx = qualified_class_name.rfind('.')
    class_name = qualified_class_name[idx + 1 :]
    pkg_name = qualified_class_name[:idx]

    parent_path, path, module_name = _find_module(pkg_name, package_dir, root_dir)
    module = _load_spec(_find_spec(module_name, path, parent_path), module_name)
    return getattr(module, class_name)


def cmdclass(values, package_dir=None, root_dir=None):
    """Given a dictionary mapping command names to strings for qualified class
    names, apply :func:`resolve_class` to the dict values.
    """
    return {k: resolve_class(v, package_dir, root_dir) for k, v in values.items()}


def find_packages(*, namespaces=False, root_dir=None, **kwargs):
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

    root_dir = root_dir or "."
    where = kwargs.pop('where', ['.'])
    if isinstance(where, str):
        where = [where]
    target = [_nest_path(root_dir, path) for path in where]
    return list(chain_iter(PackageFinder.find(x, **kwargs) for x in target))


def _nest_path(parent, path):
    path = parent if path == "." else os.path.join(parent, path)
    return os.path.normpath(path)


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


def canonic_package_data(package_data):
    if "*" in package_data:
        package_data[""] = package_data.pop("*")
    return package_data


def canonic_data_files(data_files, root_dir=None):
    """For compatibility with ``setup.py``, ``data_files`` should be a list
    of pairs instead of a dict.

    This function also expands glob patterns.
    """
    if isinstance(data_files, list):
        return data_files

    return [
        (dest, glob_relative(patterns, root_dir))
        for dest, patterns in data_files.items()
    ]


def entry_points(text, text_source="entry-points"):
    """Given the contents of entry-points file,
    process it into a 2-level dictionary (``dict[str, dict[str, str]]``).
    The first level keys are entry-point groups, the second level keys are
    entry-point names, and the second level values are references to objects
    (that correspond to the entry-point value).
    """
    parser = ConfigParser(default_section=None, delimiters=("=",))
    parser.optionxform = str  # case sensitive
    parser.read_string(text, text_source)
    groups = {k: dict(v.items()) for k, v in parser.items()}
    groups.pop(parser.default_section, None)
    return groups
