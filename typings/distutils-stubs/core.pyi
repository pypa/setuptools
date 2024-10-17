from collections.abc import Mapping
from typing import Final

from _typeshed import Incomplete, StrOrBytesPath

from .cmd import Command as Command
from .dist import Distribution as Distribution
from .extension import Extension as Extension

USAGE: Final[str]

def gen_usage(script_name: StrOrBytesPath) -> str: ...

setup_keywords: tuple[str, ...]
extension_keywords: tuple[str, ...]

def setup(
    *,
    name: str = ...,
    version: str = ...,
    description: str = ...,
    long_description: str = ...,
    author: str = ...,
    author_email: str = ...,
    maintainer: str = ...,
    maintainer_email: str = ...,
    url: str = ...,
    download_url: str = ...,
    packages: list[str] = ...,
    py_modules: list[str] = ...,
    scripts: list[str] = ...,
    ext_modules: list[Extension] = ...,
    classifiers: list[str] = ...,
    distclass: type[Distribution] = ...,
    script_name: str = ...,
    script_args: list[str] = ...,
    options: Mapping[str, Incomplete] = ...,
    license: str = ...,
    keywords: list[str] | str = ...,
    platforms: list[str] | str = ...,
    cmdclass: Mapping[str, type[Command]] = ...,
    data_files: list[tuple[str, list[str]]] = ...,
    package_dir: Mapping[str, str] = ...,
    obsoletes: list[str] = ...,
    provides: list[str] = ...,
    requires: list[str] = ...,
    command_packages: list[str] = ...,
    command_options: Mapping[str, Mapping[str, tuple[Incomplete, Incomplete]]] = ...,
    package_data: Mapping[str, list[str]] = ...,
    include_package_data: bool = ...,
    libraries: list[str] = ...,
    headers: list[str] = ...,
    ext_package: str = ...,
    include_dirs: list[str] = ...,
    password: str = ...,
    fullname: str = ...,
    # Custom Distributions could accept more params
    **attrs: object,
) -> Distribution: ...
def run_setup(
    script_name: str, script_args: list[str] | None = None, stop_after: str = "run"
) -> Distribution: ...
