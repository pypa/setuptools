"""Collection of functions and constants to help dealing with setuptools and
distutils configuration options.
(e.g. obtaining it from ``pyproject.toml``, comparing, applying to a dist
object, etc..).
"""
import os
from typing import TYPE_CHECKING, Any, Iterable, List, Set, Tuple, Union

if TYPE_CHECKING:
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
}

TOOL_TABLE_RENAMES = {"script_files": "scripts"}

SCALAR_VALUES = {"zip_safe", "include_package_data"}
DICT_VALUES = {
    "package_dir",
    "package_data",
    "exclude_package_data",
    "entry_points",
    "cmdclass"
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
    tool_table = pyproject.get("tool", {}).get("setuptools", {})
    for key, value in tool_table.items():
        norm_key = normalise_key(key)
        norm_key = TOOL_TABLE_RENAMES.get(norm_key, norm_key)
        if norm_key in OPTIONS:
            options[norm_key] = value

    # entry-points
    project = pyproject.get("project", {})
    entry_points = _normalise_entry_points(project)
    if entry_points:
        options["entry_points"] = entry_points

    return options


def _normalise_entry_points(project: dict):
    entry_points = project.get("entry-points", project.get("entry_points", {}))
    renaming = {"scripts": "console_scripts", "gui_scripts": "scripts"}
    for key, value in project.items():
        norm_key = normalise_key(key)
        if norm_key in renaming and value:
            entry_points[renaming[norm_key]] = value

    return {
        name: [f"{k} = {v}" for k, v in group.items()]
        for name, group in entry_points.items()
    }


def apply(options: dict, dist: "Distribution", _source: str = "pyproject.toml"):
    """Apply ``options`` into a ``Distribution`` object
    (configuring the distribution object accordingly).

    ``option`` should be a dict similar to the ones returned by
    :func:`from_pyproject`.
    """
    for key, value in options.items():
        setattr(dist, key, value)



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
    return_value: Union[bool, int] = True
    options1_keys = valid_keys & set(options1)
    options2_keys = valid_keys & set(options2)
    if options1_keys ^ options2_keys:
        return False
    if options1_keys - options2_keys:
        return_value = -1
    elif options2_keys - options1_keys:
        return_value = 1

    for key in (options1_keys & options2_keys):
        value1, value2 = options1[key], options1[key]
        if key == "data_files":
            value1, value2 = _norm_items(value1), _norm_items(value2)
        elif key == "cmdclass":
            value1 = {(k, v.__qualname__) for k, v in value1.items()}
            value2 = {(k, v.__qualname__) for k, v in value2.items()}
        elif key in DICT_VALUES:
            value1, value2 = _norm_items(value1.items()), _norm_items(value2.items())
        elif key in LIST_VALUES:
            value1, value2 = set(value1), set(value2)
        if value1 != value2:
            return False

    return return_value


def _norm_items(
    items: Iterable[Tuple[str, Union[Scalar, list]]]
) -> Set[Tuple[Scalar, ...]]:
    return {_comparable_items(i) for i in items}


def _comparable_items(
    items: Tuple[str, Union[Scalar, List[Scalar]]]
) -> Tuple[Scalar, ...]:
    key, values = items
    if isinstance(values, list):
        return (key, *sorted(values))
    return (key, values)
