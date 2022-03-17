"""Load setuptools configuration from ``pyproject.toml`` files"""
import logging
import os
import warnings
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, Callable, Optional, Tuple, Union

from setuptools.errors import FileError, OptionError

from . import expand as _expand
from ._apply_pyprojecttoml import apply

if TYPE_CHECKING:
    from setuptools.dist import Distribution  # noqa

_Path = Union[str, os.PathLike]
_logger = logging.getLogger(__name__)


def load_file(filepath: _Path) -> dict:
    from setuptools.extern import tomli  # type: ignore

    with open(filepath, "rb") as file:
        return tomli.load(file)


def validate(config: dict, filepath: _Path):
    from setuptools.extern._validate_pyproject import validate as _validate

    try:
        return _validate(config)
    except Exception as ex:
        if ex.__class__.__name__ != "ValidationError":
            # Workaround for the fact that `extern` can duplicate imports
            ex_cls = ex.__class__.__name__
            error = ValueError(f"invalid pyproject.toml config: {ex_cls} - {ex}")
            raise error from None

        _logger.error(f"configuration error: {ex.summary}")  # type: ignore
        _logger.debug(ex.details)  # type: ignore
        error = ValueError(f"invalid pyproject.toml config: {ex.name}")  # type: ignore
        raise error from None


def apply_configuration(dist: "Distribution", filepath: _Path) -> "Distribution":
    """Apply the configuration from a ``pyproject.toml`` file into an existing
    distribution object.
    """
    config = read_configuration(filepath, dist=dist)
    return apply(dist, config, filepath)


def read_configuration(
    filepath: _Path,
    expand=True,
    ignore_option_errors=False,
    dist: Optional["Distribution"] = None,
):
    """Read given configuration file and returns options from it as a dict.

    :param str|unicode filepath: Path to configuration file in the ``pyproject.toml``
        format.

    :param bool expand: Whether to expand directives and other computed values
        (i.e. post-process the given configuration)

    :param bool ignore_option_errors: Whether to silently ignore
        options, values of which could not be resolved (e.g. due to exceptions
        in directives such as file:, attr:, etc.).
        If False exceptions are propagated as expected.

    :param Distribution|None: Distribution object to which the configuration refers.
        If not given a dummy object will be created and discarded after the
        configuration is read. This is used for auto-discovery of packages in the case
        a dynamic configuration (e.g. ``attr`` or ``cmdclass``) is expanded.
        When ``expand=False`` this object is simply ignored.

    :rtype: dict
    """
    filepath = os.path.abspath(filepath)

    if not os.path.isfile(filepath):
        raise FileError(f"Configuration file {filepath!r} does not exist.")

    asdict = load_file(filepath) or {}
    project_table = asdict.get("project", {})
    tool_table = asdict.get("tool", {}).get("setuptools", {})
    if not asdict or not (project_table or tool_table):
        return {}  # User is not using pyproject to configure setuptools

    # TODO: Remove once the future stabilizes
    msg = (
        "Support for project metadata in `pyproject.toml` is still experimental "
        "and may be removed (or change) in future releases."
    )
    warnings.warn(msg, _ExperimentalProjectMetadata)

    # There is an overall sense in the community that making include_package_data=True
    # the default would be an improvement.
    # `ini2toml` backfills include_package_data=False when nothing is explicitly given,
    # therefore setting a default here is backwards compatible.
    tool_table.setdefault("include-package-data", True)

    with _ignore_errors(ignore_option_errors):
        # Don't complain about unrelated errors (e.g. tools not using the "tool" table)
        subset = {"project": project_table, "tool": {"setuptools": tool_table}}
        validate(subset, filepath)

    if expand:
        root_dir = os.path.dirname(filepath)
        return expand_configuration(asdict, root_dir, ignore_option_errors, dist)

    return asdict


def expand_configuration(
    config: dict,
    root_dir: Optional[_Path] = None,
    ignore_option_errors=False,
    dist: Optional["Distribution"] = None,
) -> dict:
    """Given a configuration with unresolved fields (e.g. dynamic, cmdclass, ...)
    find their final values.

    :param dict config: Dict containing the configuration for the distribution
    :param str root_dir: Top-level directory for the distribution/project
        (the same directory where ``pyproject.toml`` is place)
    :param bool ignore_option_errors: see :func:`read_configuration`
    :param Distribution|None: Distribution object to which the configuration refers.
        If not given a dummy object will be created and discarded after the
        configuration is read. Used in the case a dynamic configuration
        (e.g. ``attr`` or ``cmdclass``).

    :rtype: dict
    """
    root_dir = root_dir or os.getcwd()
    project_cfg = config.get("project", {})
    setuptools_cfg = config.get("tool", {}).get("setuptools", {})

    # A distribution object is required for discovering the correct package_dir
    dist, setuptools_cfg = _ensure_dist_and_package_dir(
        dist, project_cfg, setuptools_cfg, root_dir
    )

    _expand_packages(setuptools_cfg, root_dir, ignore_option_errors)
    _canonic_package_data(setuptools_cfg)
    _canonic_package_data(setuptools_cfg, "exclude-package-data")

    with _expand.EnsurePackagesDiscovered(dist) as ensure_discovered:
        _fill_discovered_attrs(dist, setuptools_cfg, ensure_discovered)
        package_dir = setuptools_cfg["package-dir"]

        process = partial(_process_field, ignore_option_errors=ignore_option_errors)
        cmdclass = partial(_expand.cmdclass, package_dir=package_dir, root_dir=root_dir)
        data_files = partial(_expand.canonic_data_files, root_dir=root_dir)

        process(setuptools_cfg, "data-files", data_files)
        process(setuptools_cfg, "cmdclass", cmdclass)
        _expand_all_dynamic(project_cfg, setuptools_cfg, root_dir, ignore_option_errors)

    return config


def _ensure_dist_and_package_dir(
    dist: Optional["Distribution"],
    project_cfg: dict,
    setuptools_cfg: dict,
    root_dir: _Path,
) -> Tuple["Distribution", dict]:
    from setuptools.dist import Distribution

    attrs = {"src_root": root_dir, "name": project_cfg.get("name", None)}
    dist = dist or Distribution(attrs)

    # dist and setuptools_cfg should use the same package_dir
    if dist.package_dir is None:
        dist.package_dir = setuptools_cfg.get("package-dir", {})
    if setuptools_cfg.get("package-dir") is None:
        setuptools_cfg["package-dir"] = dist.package_dir

    return dist, setuptools_cfg


def _fill_discovered_attrs(
    dist: "Distribution",
    setuptools_cfg: dict,
    ensure_discovered: _expand.EnsurePackagesDiscovered,
):
    """When entering the context, the values of ``packages``, ``py_modules`` and
    ``package_dir`` that are missing in ``dist`` are copied from ``setuptools_cfg``.
    When existing the context, if these values are missing in ``setuptools_cfg``, they
    will be copied from ``dist``.
    """
    package_dir = setuptools_cfg["package-dir"]
    dist.package_dir = package_dir  # need to be the same object

    # Set `py_modules` and `packages` in dist to short-circuit auto-discovery,
    # but avoid overwriting empty lists purposefully set by users.
    if isinstance(setuptools_cfg.get("py_modules"), list) and dist.py_modules is None:
        dist.py_modules = setuptools_cfg["py-modules"]
    if isinstance(setuptools_cfg.get("packages"), list) and dist.packages is None:
        dist.packages = setuptools_cfg["packages"]

    package_dir.update(ensure_discovered())

    # If anything was discovered set them back, so they count in the final config.
    setuptools_cfg.setdefault("packages", dist.packages)
    setuptools_cfg.setdefault("py-modules", dist.py_modules)


def _expand_all_dynamic(
    project_cfg: dict, setuptools_cfg: dict, root_dir: _Path, ignore_option_errors: bool
):
    silent = ignore_option_errors
    dynamic_cfg = setuptools_cfg.get("dynamic", {})
    pkg_dir = setuptools_cfg["package-dir"]
    special = (
        "readme",
        "version",
        "entry-points",
        "scripts",
        "gui-scripts",
        "classifiers",
    )
    # readme, version and entry-points need special handling
    dynamic = project_cfg.get("dynamic", [])
    regular_dynamic = (x for x in dynamic if x not in special)

    for field in regular_dynamic:
        value = _expand_dynamic(dynamic_cfg, field, pkg_dir, root_dir, silent)
        project_cfg[field] = value

    if "version" in dynamic and "version" in dynamic_cfg:
        version = _expand_dynamic(dynamic_cfg, "version", pkg_dir, root_dir, silent)
        project_cfg["version"] = _expand.version(version)

    if "readme" in dynamic:
        project_cfg["readme"] = _expand_readme(dynamic_cfg, root_dir, silent)

    if "entry-points" in dynamic:
        field = "entry-points"
        value = _expand_dynamic(dynamic_cfg, field, pkg_dir, root_dir, silent)
        project_cfg.update(_expand_entry_points(value, dynamic))

    if "classifiers" in dynamic:
        value = _expand_dynamic(dynamic_cfg, "classifiers", pkg_dir, root_dir, silent)
        project_cfg["classifiers"] = value.splitlines()


def _expand_dynamic(
    dynamic_cfg: dict,
    field: str,
    package_dir: dict,
    root_dir: _Path,
    ignore_option_errors: bool,
):
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


def _expand_readme(dynamic_cfg: dict, root_dir: _Path, ignore_option_errors: bool):
    silent = ignore_option_errors
    return {
        "text": _expand_dynamic(dynamic_cfg, "readme", None, root_dir, silent),
        "content-type": dynamic_cfg["readme"].get("content-type", "text/x-rst"),
    }


def _expand_entry_points(text: str, dynamic: set):
    groups = _expand.entry_points(text)
    expanded = {"entry-points": groups}
    if "scripts" in dynamic and "console_scripts" in groups:
        expanded["scripts"] = groups.pop("console_scripts")
    if "gui-scripts" in dynamic and "gui_scripts" in groups:
        expanded["gui-scripts"] = groups.pop("gui_scripts")
    return expanded


def _expand_packages(setuptools_cfg: dict, root_dir: _Path, ignore_option_errors=False):
    packages = setuptools_cfg.get("packages")
    if packages is None or isinstance(packages, (list, tuple)):
        return

    find = packages.get("find")
    if isinstance(find, dict):
        find["root_dir"] = root_dir
        find["fill_package_dir"] = setuptools_cfg["package-dir"]
        with _ignore_errors(ignore_option_errors):
            setuptools_cfg["packages"] = _expand.find_packages(**find)


def _process_field(
    container: dict, field: str, fn: Callable, ignore_option_errors=False
):
    if field in container:
        with _ignore_errors(ignore_option_errors):
            container[field] = fn(container[field])


def _canonic_package_data(setuptools_cfg, field="package-data"):
    package_data = setuptools_cfg.get(field, {})
    return _expand.canonic_package_data(package_data)


@contextmanager
def _ignore_errors(ignore_option_errors: bool):
    if not ignore_option_errors:
        yield
        return

    try:
        yield
    except Exception as ex:
        _logger.debug(f"ignored error: {ex.__class__.__name__} - {ex}")


class _ExperimentalProjectMetadata(UserWarning):
    """Explicitly inform users that `pyproject.toml` configuration is experimental"""
