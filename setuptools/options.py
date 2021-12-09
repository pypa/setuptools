"""Collection of functions and constants to help dealing with setuptools and
distutils configuration options.
(e.g. obtaining it from ``pyproject.toml``, comparing, applying to a dist
object, etc..).
"""
import os
from itertools import chain
from typing import (TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set, Tuple,
                    Type, Union)

if TYPE_CHECKING:
    from pkg_resources import EntryPoint  # noqa
    from setuptools.dist import Distribution  # noqa

Scalar = Union[int, float, bool, None, str]
_Path = Union[os.PathLike, str, None]

OPTIONS = {
    # "obsoletes", "provides" => covered in metadata
    # "install_requires",  => covered in metadata
    # "setup_requires",  =>  replaced by build.requirements
    # "tests_require",  => deprecated
    # "python_requires", => covered in metadata
    "zip_safe",
    "package_dir",
    "scripts",
    "eager_resources",
    "dependency_links",
    "namespace_packages",
    "py_modules",
    "packages",
    "package_data",
    "include_package_data",
    "exclude_package_data",
    "data_files",
    "entry_points",
    "cmdclass",
    "command_options",
}

TOOL_TABLE_RENAMES = {"script_files": "scripts"}

SCALAR_VALUES = {"zip_safe", "include_package_data"}
DICT_VALUES = {
    "package_dir",
    "package_data",
    "exclude_package_data",
    "entry_points",
    "cmdclass",
    "command_options",
}
LIST_VALUES = OPTIONS - SCALAR_VALUES - DICT_VALUES


def normalise_key(key: str) -> str:
    return key.lower().replace("-", "_")


def from_pyproject(pyproject: dict, root_dir: _Path = None) -> dict:
    """Given a dict representing the contents of a ``pyproject.toml``,
    already validated and with directives and dynamic values expanded,
    return dict with setuptools specific options.

    This function is "forgiving" with its inputs, but strict with its outputs.
    """
    options = {}
    _ = root_dir  # argument exists for symmetry with setuptools.metadata

    valid_options = OPTIONS - {"command_options"}

    tool_table = pyproject.get("tool", {}).get("setuptools", {})
    for key, value in tool_table.items():
        norm_key = normalise_key(key)
        norm_key = TOOL_TABLE_RENAMES.get(norm_key, norm_key)
        if norm_key in valid_options:
            options[norm_key] = value

    _normalise_entry_points(pyproject, options)
    _copy_command_options(pyproject, options)

    return options


def _normalise_entry_points(pyproject: dict, options: dict):
    project = pyproject.get("project", {})

    entry_points = project.get("entry-points", project.get("entry_points", {}))
    renaming = {"scripts": "console_scripts", "gui_scripts": "scripts"}
    for key, value in project.items():
        norm_key = normalise_key(key)
        if norm_key in renaming and value:
            entry_points[renaming[norm_key]] = value

    if entry_points:
        options["entry_points"] = {
            name: [f"{k} = {v}" for k, v in group.items()]
            for name, group in entry_points.items()
        }


def _copy_command_options(pyproject: dict, options: dict):
    from distutils import log

    from pkg_resources import iter_entry_points
    from setuptools.dist import Distribution

    tool_table = pyproject.get("tool", {})
    valid_options = {"global": _normalise_cmd_options(Distribution.global_options)}

    cmdclass = tool_table.get("setuptools", {}).get("cmdclass", {}).items()
    entry_points = (_load_ep(ep) for ep in iter_entry_points('distutils.commands'))
    entry_points = (ep for ep in entry_points if ep)
    for cmd, cmd_class in chain(entry_points, cmdclass):
        opts = valid_options.get(cmd, set())
        opts = opts | _normalise_cmd_options(getattr(cmd_class, "user_options", []))
        valid_options[cmd] = opts

    cmd_opts = {}
    for cmd, config in pyproject.get("tool", {}).get("distutils", {}).items():
        cmd = normalise_key(cmd)
        valid = valid_options.get(cmd, set())
        cmd_opts.setdefault(cmd, {})
        for key, value in config.items():
            key = normalise_key(key)
            cmd_opts[cmd][key] = value
            if key not in valid:
                # To avoid removing options that are specified dynamically we
                # just log a warn...
                log.warn(f"Command option {cmd}.{key} is not defined")

    if cmd_opts:
        options["command_options"] = cmd_opts


def _load_ep(ep: "EntryPoint") -> Optional[Tuple[str, Type]]:
    # Ignore all the errors
    try:
        return (ep.name, ep.load())
    except Exception as ex:
        from distutils import log
        msg = f"{ex.__class__.__name__} while trying to load entry-point {ep.name}"
        log.warn(f"{msg}: {ex}")
        return None


def _normalise_cmd_option_key(name: str) -> str:
    return normalise_key(name).strip("_=")


def _normalise_cmd_options(desc: List[Tuple[str, Optional[str], str]]) -> Set[str]:
    return {_normalise_cmd_option_key(fancy_option[0]) for fancy_option in desc}


def apply(options: dict, dist: "Distribution", source: str = "pyproject.toml"):
    """Apply ``options`` into a ``Distribution`` object
    (configuring the distribution object accordingly).

    ``option`` should be a dict similar to the ones returned by
    :func:`from_pyproject` (already validated and expanded).
    """
    for key, value in options.items():
        setattr(dist, key, value)

    command_options = dist.command_options
    for cmd, opts in options.get("command_options", {}).items():
        dest = command_options.setdefault(cmd, {})
        items = list(dest.items())  # eager, so we can modify dest
        for key, value in items:
            dest.pop(key.replace("_", "-"), None)
            dest[normalise_key(key)] = (source, value)


def compare(options1: dict, options2: dict) -> Union[bool, int]:
    """Compare ``options1`` and ``options2`` and return:
    - ``True`` if ``options1 == ``options2``
    - ``1`` if ``options1`` is a subset of ``options2``
    - ``-1`` if ``options2`` is a subset of ``options1``
    - ``False`` otherwise

    Both ``options1`` and ``options2`` should be dicts similar to the ones
    returned by :func:`from_pyproject`. Extra keys will be ignored.
    """
    valid_keys = OPTIONS
    options1_keys = valid_keys & set(options1)
    options2_keys = valid_keys & set(options2)
    return_value: Union[bool, int] = _compare_sets(options1_keys, options2_keys)
    if return_value is False:
        return False

    for key in (options1_keys & options2_keys):
        value1, value2 = options1[key], options1[key]
        if key == "data_files":
            value1, value2 = _norm_items(value1), _norm_items(value2)
        elif key == "cmdclass":
            value1 = {(k, v.__qualname__) for k, v in value1.items()}
            value2 = {(k, v.__qualname__) for k, v in value2.items()}
        elif key == "command_options":
            value1 = _norm_items(_comparable_cmd_opts(value1).items())
            value2 = _norm_items(_comparable_cmd_opts(value2).items())
            cmp = _compare_sets(value1, value2)
            # Let's be more relaxed with command options, since they can be read
            # from other files in disk
            all_int = isinstance(cmp, int) and isinstance(return_value, int)
            if cmp is False or (cmp != return_value and all_int):
                return False
            return_value = cmp
            continue
        elif key in DICT_VALUES:
            value1, value2 = _norm_items(value1.items()), _norm_items(value2.items())
        elif key in LIST_VALUES:
            value1, value2 = set(value1), set(value2)
        if value1 != value2:
            return False

    return return_value


def _compare_sets(value1: set, value2: set) -> Union[bool, int]:
    """
    ``True`` if ``value1 == ``value2``
    ``1`` if ``value1`` is a subset of ``value2``
    ``-1`` if ``value2`` is a subset of ``value1``
    ``False`` otherwise
    """
    return_value: Union[bool, int] = True
    if value1 ^ value2:
        return False
    if value1 - value2:
        return_value = -1
    elif value2 - value1:
        return_value = 1
    return return_value


def _norm_items(
    items: Iterable[Tuple[str, Union[Scalar, list]]]
) -> Set[Tuple[Scalar, ...]]:
    return {_comparable_items(i) for i in items}


def _comparable_cmd_opts(value: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return {f"{cmd}.{k}": v for cmd, opts in value.items() for k, v in opts.items()}


def _comparable_items(
    items: Tuple[str, Union[Scalar, List[Scalar]]]
) -> Tuple[Scalar, ...]:
    key, values = items
    if isinstance(values, list):
        return (key, *sorted(values))
    return (key, values)


def from_dist(dist: "Distribution") -> dict:
    """Given a distribution object, extract options from it"""
    options = {}
    for key in OPTIONS:
        value = getattr(dist, key, None)
        if value or value is False:
            options[key] = value

    for cmd, opts in dist.command_options.items():
        command_options = options.setdefault("command_options", {})
        for key, (_src, value) in opts.items():
            dest = command_options.setdefault(cmd, {})
            dest[key] = value

    return options
