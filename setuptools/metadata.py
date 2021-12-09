"""Collection of functions and constants to help dealing with `core metadata`_
(e.g. obtaining it from ``pyproject.toml``, comparing, applying to a dist
object, etc..).

.. _core metadata: https://packaging.python.org/en/latest/specifications/core-metadata
"""
import os
from email.headerregistry import Address
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Set, Union

from setuptools.extern.packaging import version
from setuptools.extern.packaging.requirements import Requirement

if TYPE_CHECKING:
    from setuptools.dist import Distribution  # noqa

_Path = Union[os.PathLike, str, None]
_DictOrStr = Union[dict, str]
_CorrespFn = Callable[[Any, dict, _Path], None]
_Correspondence = Union[str, _CorrespFn]


CORE_METADATA = (
    "Metadata-Version",
    "Name",
    "Version",
    "Dynamic",
    "Platform",
    "Supported-Platform",
    "Summary",
    "Description",
    "Description-Content-Type",
    "Keywords",
    "Home-page",
    "Download-URL",
    "Author",
    "Author-email",
    "Maintainer",
    "Maintainer-email",
    "License",
    "License-File",  # Not standard yet
    "Classifier",
    "Requires-Dist",
    "Requires-Python",
    "Requires-External",
    "Project-URL",
    "Provides-Extra",
    "Provides-Dist",
    "Obsoletes-Dist",
)

MULTIPLE_USE = (
    "Dynamic",
    "Platform",
    "Supported-Platform",
    "License-File",  # Not standard yet
    "Classifier",
    "Requires-Dist",
    "Requires-External",
    "Project-URL",
    "Provides-Extra",
    "Provides-Dist",
    "Obsoletes-Dist",
)

UPDATES = {
    "requires": "requires_dist",  # PEP 314 => PEP 345
    "provides": "provides_dist",  # PEP 314 => PEP 345
    "obsoletes": "obsoletes_dist",  # PEP 314 => PEP 345
}
"""Fields whose names where updated but whose syntax remained basically the same
(can be safely upgraded).
This mapping uses the JSON key normalisation from :pep:`566#json-compatible-metadata`
"""

LIST_VALUES = {*MULTIPLE_USE, "Keywords"}
DEFAULT_LICENSE_FILES = ('LICEN[CS]E*', 'COPYING*', 'NOTICE*', 'AUTHORS*')
# defaults from the `wheel` package


def json_compatible_key(key: str) -> str:
    """As defined in :pep:`566#json-compatible-metadata`"""
    return key.lower().replace("-", "_")


RFC822_KEYS = {json_compatible_key(k): k for k in CORE_METADATA}
"""Mapping between JSON compatible keys (:pep:`566#json-compatible-metadata`)
and email-header style (:rfc:`822`) core metadata keys.
"""


def normalise_key(key: str) -> str:
    key = json_compatible_key(key)
    if key[-1] == "s" and key[:-1] in RFC822_KEYS:
        # Sometimes some keys come in the plural (e.g. "classifiers", "license_files")
        return key[:-1]
    return key


def _summary(val: str, dest: dict, _root_dir: _Path):
    from setuptools.dist import single_line
    dest.update(summary=single_line(val))


def _description(val: _DictOrStr, dest: dict, root_dir: _Path):
    if isinstance(val, str):
        text = val
        ctype = "text/x-rst"
    else:
        from setuptools.config import expand

        text = expand.read_files(val["file"]) if "file" in val else val["text"]
        ctype = val["content-type"]

    dest.update(description=text, description_content_type=ctype)


def _license(val: dict, dest: dict, root_dir: _Path):
    if "file" in val:
        dest.update(license_file=val["file"])
    else:
        dest.update(license=val["text"])


def _people(val: List[dict], dest: dict, _root_dir: _Path, kind: str):
    field = []
    email_field = []
    for person in val:
        if "name" not in person:
            email_field.append(person["email"])
        elif "email" not in person:
            field.append(person["name"])
        else:
            addr = Address(display_name=person["name"], addr_spec=person["email"])
            email_field.append(str(addr))

    if field:
        dest.update(kind=field)
    if email_field:
        dest.update({f"{kind}_email": email_field})


def _urls(val: dict, dest: dict, _root_dir: _Path):
    special = ("download_url", "home_page")
    mapping = {x.replace("_", ""): x for x in special}
    for key, url in val.items():
        norm_key = json_compatible_key(key).replace("_", "")
        if norm_key in mapping:
            dest[mapping[norm_key]] = url
    dest["project_url"] = [", ".join(i) for i in val.items()]


def _dependencies(val: list, dest: dict, _root_dir: _Path):
    requires_dist = dest.setdefault("requires_dist", [])
    requires_dist.extend(val)


def _add_extra(dep: str, extra_name: str) -> str:
    cond_expr = f"extra == '{extra_name}'"
    joiner = " and " if ";" in dep else "; "
    return joiner.join((dep, cond_expr))


def _optional_dependencies(val: dict, dest: dict, root_dir: _Path):
    extra = set(dest.get("provides_extra", []))
    for key, deps in val.items():
        extra.add(key)
        cond_deps = [_add_extra(x, key) for x in deps]
        _dependencies(cond_deps, dest, root_dir)
    dest["provides_extra"] = list(extra)


PYPROJECT_CORRESPONDENCE: Dict[str, _CorrespFn] = {
    "description": _summary,
    "readme": _description,
    "license": _license,
    "authors": partial(_people, kind="author"),
    "maintainers": partial(_people, kind="maintainer"),
    "urls": _urls,
    "dependencies": _dependencies,
    "optional_dependencies": _optional_dependencies
}

TOOL_SPECIFIC = ("provides", "obsoletes", "platforms")


def from_pyproject(pyproject: dict, root_dir: _Path = None) -> dict:
    """Given a dict representing the contents of a ``pyproject.toml``,
    already validated and with directives and dynamic values expanded,
    return a JSON-like metadata dict as defined in
    :pep:`566#json-compatible-metadata`

    This function is "forgiving" with its inputs, but strict with its outputs.
    """
    metadata = {}
    project = pyproject.get("project", {}).copy()
    dynamic = {normalise_key(k) for k in project.pop("dynamic", [])}
    _from_project_table(metadata, project, dynamic, root_dir)

    tool_table = pyproject.get("tool", {}).get("setuptools", {})
    _from_tool_table(metadata, tool_table)

    dynamic_cfg = tool_table.get("dynamic", {})
    _finalize_dynamic(metadata, dynamic, dynamic_cfg, root_dir)

    return metadata


def _finalize_dynamic(metadata: dict, dynamic: set, dynamic_cfg: dict, root_dir: _Path):
    from setuptools.config import expand

    # Dynamic license needs special handling (cannot be expanded in terms of PEP 621)
    # due to the mutually exclusive `text` and `file`
    dynamic_license = {"license", "license_files"}
    dynamic_cfg.setdefault("license_files", DEFAULT_LICENSE_FILES)
    keys = set(dynamic_cfg) & dynamic_license if "license" in dynamic else set()

    for key in keys:
        json_key = json_compatible_key(key)
        val = dynamic_cfg[key]
        if json_key == "license_files":
            files = {v: v for v in expand.glob_relative(val, root_dir)}  # deduplicate
            val = [v for v in files.keys() if not v.endswith("~")]
        metadata[normalise_key(key)] = val
        dynamic.discard("license")

    if dynamic:
        metadata["dynamic"] = sorted(list(dynamic))


def _from_project_table(metadata: dict, project: dict, dynamic: set, root_dir: _Path):
    for key, val in project.items():
        if not val:
            continue
        json_key = json_compatible_key(key)
        norm_key = normalise_key(json_key)
        if norm_key in dynamic:
            dynamic.remove(norm_key)
        if json_key in PYPROJECT_CORRESPONDENCE:
            PYPROJECT_CORRESPONDENCE[json_key](val, metadata, root_dir)
        elif norm_key in RFC822_KEYS:
            metadata[norm_key] = val


def _from_tool_table(metadata: dict, tool_table: dict):
    for key in TOOL_SPECIFIC:
        if key in tool_table:
            norm_key = normalise_key(UPDATES.get(key, key))
            metadata[norm_key] = tool_table[key]


SETUPTOOLS_RENAMES = {"long_description_content_type": "description_content_type"}
OUTDATED_SETTERS = {"requires_dist": "requires"}


def apply(metadata: dict, dist: "Distribution", _source: str = "pyproject.toml"):
    """Apply a JSON-like ``metadata`` dict as defined in
    :pep:`566#json-compatible-metadata` into a ``Distribution`` object
    (configuring the distribution object accordingly)
    """
    metadata_obj = dist.metadata
    norm_attrs = ((normalise_key(x), x) for x in metadata_obj.__dict__)
    norm_attrs = ((UPDATES.get(k, k) , v) for k, v in norm_attrs)
    norm_attrs = ((SETUPTOOLS_RENAMES.get(k, k) , v) for k, v in norm_attrs)
    metadata_attrs = ((k, v) for k, v in norm_attrs if k in RFC822_KEYS)
    metadata_setters = {
        k: getattr(metadata_obj, f"set_{v}", partial(setattr, metadata_obj, v))
        for k, v in metadata_attrs
    }

    for key, value in metadata.items():
        norm_key = normalise_key(key)
        if norm_key in OUTDATED_SETTERS:
            setattr(metadata_obj, OUTDATED_SETTERS[norm_key], value)
        elif norm_key in metadata_setters:
            metadata_setters[norm_key](value)
        else:
            setattr(metadata_obj, norm_key, value)


def compare(metadata1: dict, metadata2: dict) -> Union[bool, int]:
    """Compare ``metadata1`` and ``metadata2`` and return:
    - ``True`` if ``metadata1 == ``metadata2``
    - ``1`` if ``metadata1`` is a subset of ``metadata2``
    - ``-1`` if ``metadata2`` is a subset of ``metadata1``
    - ``False`` otherwise

    Both ``metadata1`` and ``metadata2`` should be dicts containing
    JSON-compatible metadata, as defined in :pep:`566#json-compatible-metadata`.
    Extra keys will be ignored.
    """
    valid_keys = set(RFC822_KEYS)
    return_value: Union[bool, int] = True
    metadata1_keys = valid_keys & set(metadata1)
    metadata2_keys = valid_keys & set(metadata2)
    if metadata1_keys ^ metadata2_keys:
        return False
    if metadata1_keys - metadata2_keys:
        return_value = -1
    elif metadata2_keys - metadata1_keys:
        return_value = 1

    for key in (metadata1_keys & metadata2_keys):
        value1, value2 = metadata1[key], metadata2[key]
        if key == "version":
            value1, value2 = version.parse(value1), version.parse(value2)
        elif key == "requires_dist":
            value1, value2 = _norm_reqs(value1), _norm_reqs(value2)
        if RFC822_KEYS.get(key, key) in LIST_VALUES:
            value1, value2 = set(value1), set(value2)
        if value1 != value2:
            return False

    return return_value


def _norm_reqs(reqs: Iterable[str]) -> Set[str]:
    return set(map(lambda req: str(Requirement(req)), reqs))
