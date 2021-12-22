"""Load setuptools configuration from ``pyproject.toml`` files"""
import os
import sys
from contextlib import contextmanager
from functools import partial
from typing import Union
import json

from setuptools.errors import OptionError, FileError
from distutils import log

from . import expand as _expand

_Path = Union[str, os.PathLike]


def load_file(filepath: _Path):
    try:
        from setuptools.extern import tomli
    except ImportError:  # Bootstrap problem (?) diagnosed by test_distutils_adoption
        sys_path = sys.path.copy()
        try:
            from setuptools import _vendor
            sys.path.append(_vendor.__path__[0])
            import tomli
        finally:
            sys.path = sys_path

    with open(filepath, "rb") as file:
        return tomli.load(file)


def validate(config: dict, filepath: _Path):
    from setuptools.extern import _validate_pyproject
    from setuptools.extern._validate_pyproject import fastjsonschema_exceptions

    try:
        return _validate_pyproject.validate(config)
    except fastjsonschema_exceptions.JsonSchemaValueException as ex:
        msg = [f"Schema: {ex}"]
        if ex.value:
            msg.append(f"Given value:\n{json.dumps(ex.value, indent=2)}")
        if ex.rule:
            msg.append(f"Offending rule: {json.dumps(ex.rule, indent=2)}")
        if ex.definition:
            msg.append(f"Definition:\n{json.dumps(ex.definition, indent=2)}")

        log.error("\n\n".join(msg) + "\n")
        raise


def read_configuration(filepath, expand=True, ignore_option_errors=False):
    """Read given configuration file and returns options from it as a dict.

    :param str|unicode filepath: Path to configuration file in the ``pyproject.toml``
        format.

    :param bool expand: Whether to expand directives and other computed values
        (i.e. post-process the given configuration)

    :param bool ignore_option_errors: Whether to silently ignore
        options, values of which could not be resolved (e.g. due to exceptions
        in directives such as file:, attr:, etc.).
        If False exceptions are propagated as expected.

    :rtype: dict
    """
    filepath = os.path.abspath(filepath)

    if not os.path.isfile(filepath):
        raise FileError(f"Configuration file {filepath!r} does not exist.")

    asdict = load_file(filepath) or {}
    project_table = asdict.get("project")
    tool_table = asdict.get("tool", {}).get("setuptools")
    if not asdict or not(project_table or tool_table):
        return {}  # User is not using pyproject to configure setuptools

    # There is an overall sense in the community that making include_package_data=True
    # the default would be an improvement.
    # `ini2toml` backfills include_package_data=False when nothing is explicitly given,
    # therefore setting a default here is backwards compatible.
    tool_table.setdefault("include-package-data", True)

    with _ignore_errors(ignore_option_errors):
        validate(asdict, filepath)

    if expand:
        root_dir = os.path.dirname(filepath)
        return expand_configuration(asdict, root_dir, ignore_option_errors)

    return asdict


def expand_configuration(config, root_dir=None, ignore_option_errors=False):
    """Given a configuration with unresolved fields (e.g. dynamic, cmdclass, ...)
    find their final values.

    :param dict config: Dict containing the configuration for the distribution
    :param str root_dir: Top-level directory for the distribution/project
        (the same directory where ``pyproject.toml`` is place)
    :param bool ignore_option_errors: see :func:`read_configuration`

    :rtype: dict
    """
    root_dir = root_dir or os.getcwd()
    project_cfg = config.get("project", {})
    setuptools_cfg = config.get("tool", {}).get("setuptools", {})
    package_dir = setuptools_cfg.get("package-dir")

    _expand_all_dynamic(project_cfg, setuptools_cfg, root_dir, ignore_option_errors)
    _expand_packages(setuptools_cfg, root_dir, ignore_option_errors)
    _canonic_package_data(setuptools_cfg)
    _canonic_package_data(setuptools_cfg, "exclude-package-data")

    process = partial(_process_field, ignore_option_errors=ignore_option_errors)
    cmdclass = partial(_expand.cmdclass, package_dir=package_dir, root_dir=root_dir)
    data_files = partial(_expand.canonic_data_files, root_dir=root_dir)
    process(setuptools_cfg, "data-files", data_files)
    process(setuptools_cfg, "cmdclass", cmdclass)

    return config


def _expand_all_dynamic(project_cfg, setuptools_cfg, root_dir, ignore_option_errors):
    silent = ignore_option_errors
    dynamic_cfg = setuptools_cfg.get("dynamic", {})
    package_dir = setuptools_cfg.get("package-dir", None)
    special = ("license", "readme", "version", "entry-points", "scripts", "gui-scripts")
    # license-files are handled directly in the metadata, so no expansion
    # readme, version and entry-points need special handling
    dynamic = project_cfg.get("dynamic", [])
    regular_dynamic = (x for x in dynamic if x not in special)

    for field in regular_dynamic:
        value = _expand_dynamic(dynamic_cfg, field, package_dir, root_dir, silent)
        project_cfg[field] = value

    if "version" in dynamic and "version" in dynamic_cfg:
        version = _expand_dynamic(dynamic_cfg, "version", package_dir, root_dir, silent)
        project_cfg["version"] = _expand.version(version)

    if "readme" in dynamic:
        project_cfg["readme"] = _expand_readme(dynamic_cfg, root_dir, silent)

    if "entry-points" in dynamic:
        field = "entry-points"
        value = _expand_dynamic(dynamic_cfg, field, package_dir, root_dir, silent)
        project_cfg.update(_expand_entry_points(value, dynamic))


def _expand_dynamic(dynamic_cfg, field, package_dir, root_dir, ignore_option_errors):
    if field in dynamic_cfg:
        directive = dynamic_cfg[field]
        if "file" in directive:
            return _expand.read_files(directive["file"], root_dir)
        if "attr" in directive:
            return _expand.read_attr(directive["attr"], package_dir, root_dir)
    elif not ignore_option_errors:
        msg = f"Impossible to expand dynamic value of {field!r}. "
        msg += f"No configuration found for `tool.setuptools.dynamic.{field}`"
        raise OptionError(msg)
    return None


def _expand_readme(dynamic_cfg, root_dir, ignore_option_errors):
    silent = ignore_option_errors
    return {
        "text": _expand_dynamic(dynamic_cfg, "readme", None, root_dir, silent),
        "content-type": dynamic_cfg["readme"].get("content-type", "text/x-rst")
    }


def _expand_entry_points(text, dynamic):
    groups = _expand.entry_points(text)
    expanded = {"entry-points": groups}
    if "scripts" in dynamic and "console_scripts" in groups:
        expanded["scripts"] = groups.pop("console_scripts")
    if "gui-scripts" in dynamic and "gui_scripts" in groups:
        expanded["gui-scripts"] = groups.pop("gui_scripts")
    return expanded


def _expand_packages(setuptools_cfg, root_dir, ignore_option_errors=False):
    packages = setuptools_cfg.get("packages")
    if packages is None or isinstance(packages, (list, tuple)):
        return

    find = packages.get("find")
    if isinstance(find, dict):
        find["root_dir"] = root_dir
        with _ignore_errors(ignore_option_errors):
            setuptools_cfg["packages"] = _expand.find_packages(**find)


def _process_field(container, field, fn, ignore_option_errors=False):
    if field in container:
        with _ignore_errors(ignore_option_errors):
            container[field] = fn(container[field])


def _canonic_package_data(setuptools_cfg, field="package-data"):
    package_data = setuptools_cfg.get(field, {})
    return _expand.canonic_package_data(package_data)


@contextmanager
def _ignore_errors(ignore_option_errors):
    if not ignore_option_errors:
        yield
        return

    try:
        yield
    except Exception as ex:
        log.debug(f"Ignored error: {ex.__class__.__name__} - {ex}")
