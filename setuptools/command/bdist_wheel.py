# The original version of this file was adopted from pypa/wheel,
# initially distributed under the MIT License:
# Copyright (c) 2012 Daniel Holth <dholth@fastmail.fm> and contributors
"""
Create a wheel (.whl) distribution.

A wheel is a built archive format.
"""
import logging
import os
import re
import shutil
import stat
import sys
import sysconfig
import warnings
from collections import OrderedDict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED

from distutils import dir_util  # prefer dir_util for log/cache consistency

from .. import Command, _normalization
from .._wheelbuilder import WheelBuilder
from ..extern.packaging import tags
from ._macosx_libfile import calculate_macosx_platform_tag

_logger = logging.getLogger(__name__)
_PYTHON_TAG = f"py{sys.version_info[0]}"
_PY_LIMITED_API_PATTERN = r"cp3\d"


def _get_platform(archive_root):
    """Return our platform name 'win32', 'linux_x86_64'"""
    result = sysconfig.get_platform()
    if result.startswith("macosx") and archive_root is not None:
        result = calculate_macosx_platform_tag(archive_root, result)
    elif result == "linux-x86_64" and sys.maxsize == 2147483647:
        # pip pull request #3497
        result = "linux-i686"

    return result.replace("-", "_")


def _get_flag(var, fallback, expected=True, warn=True):
    """Use a fallback value for determining SOABI flags if the needed config
    var is unset or unavailable."""
    val = sysconfig.get_config_var(var)
    if val is None:
        if warn:
            warnings.warn(
                "Config variable '{}' is unset, Python ABI tag may "
                "be incorrect".format(var),
                RuntimeWarning,
                2,
            )
        return fallback
    return val == expected


def _get_abi_tag():
    """Return the ABI tag based on SOABI (if available) or emulate SOABI (PyPy2)."""
    soabi = sysconfig.get_config_var("SOABI")
    impl = tags.interpreter_name()
    if not soabi and impl in ("cp", "pp") and hasattr(sys, "maxunicode"):
        d = ""
        m = ""
        u = ""
        if _get_flag("Py_DEBUG", hasattr(sys, "gettotalrefcount"), warn=(impl == "cp")):
            d = "d"

        if _get_flag(
            "WITH_PYMALLOC",
            impl == "cp",
            warn=(impl == "cp" and sys.version_info < (3, 8)),
        ) and sys.version_info < (3, 8):
            m = "m"

        abi = f"{impl}{tags.interpreter_version()}{d}{m}{u}"
    elif soabi and impl == "cp":
        abi = "cp" + soabi.split("-")[1]
    elif soabi and impl == "pp":
        # we want something like pypy36-pp73
        abi = "-".join(soabi.split("-")[:2])
        abi = abi.replace(".", "_").replace("-", "_")
    elif soabi:
        abi = soabi.replace(".", "_").replace("-", "_")
    else:
        abi = None

    return abi


class bdist_wheel(Command):
    description = "create a wheel distribution"

    supported_compressions = OrderedDict(
        [("stored", ZIP_STORED), ("deflated", ZIP_DEFLATED)]
    )

    user_options = [
        ("bdist-dir=", "b", "temporary directory for creating the distribution"),
        (
            "plat-name=",
            "p",
            "platform name to embed in generated filenames "
            "(default: %s)" % _get_platform(None),
        ),
        (
            "keep-temp",
            "k",
            "keep the pseudo-installation tree around after "
            + "creating the distribution archive",
        ),
        ("dist-dir=", "d", "directory to put final built distributions in"),
        ("skip-build", None, "skip rebuilding everything (for testing/debugging)"),
        (
            "relative",
            None,
            "build the archive using relative paths " "(default: false)",
        ),
        (
            "owner=",
            "u",
            "Owner name used when creating a tar file" " [default: current user]",
        ),
        (
            "group=",
            "g",
            "Group name used when creating a tar file" " [default: current group]",
        ),
        ("universal", None, "make a universal wheel" " (default: false)"),
        (
            "compression=",
            None,
            "zipfile compression (one of: {})"
            " (default: 'deflated')".format(", ".join(supported_compressions)),
        ),
        (
            "python-tag=",
            None,
            "Python implementation compatibility tag" f" (default: {_PYTHON_TAG!r})",
        ),
        (
            "build-number=",
            None,
            "Build number for this particular version. "
            "As specified in PEP-0427, this must start with a digit. "
            "[default: None]",
        ),
        (
            "py-limited-api=",
            None,
            "Python tag (cp32|cp33|cpNN) for abi3 wheel tag" " (default: false)",
        ),
        ("dist-info-dir=", "I", "*DO NOT USE/PRIVATE* pre-build .dist-info directory"),
    ]

    boolean_options = ["keep-temp", "skip-build", "relative", "universal"]

    def initialize_options(self):
        self._name = None
        self.bdist_dir = None
        self.data_dir = None
        self.plat_name = None
        self.plat_tag = None
        self.format = "zip"
        self.keep_temp = False
        self.dist_dir = None
        self.root_is_pure = None
        self.skip_build = None
        self.relative = False
        self.owner = None
        self.group = None
        self.universal = False
        self.compression = "deflated"
        self.python_tag = _PYTHON_TAG
        self.build_number = None
        self.py_limited_api = False
        self.plat_name_supplied = False
        self.dist_info_dir = None

    def finalize_options(self):
        if self.dist_info_dir is not None:
            self.dist_info_dir = Path(self.dist_info_dir)

        if self.bdist_dir is None:
            bdist_base = self.get_finalized_command("bdist").bdist_base
            self.bdist_dir = os.path.join(bdist_base, "wheel")

        self._wheel_dist_name = self._get_dist_info_name()
        if self.build_number:
            build_tag = _normalization.filename_component(self.build_number)
            self._wheel_dist_name += f"-{build_tag}"

        self.data_dir = self._wheel_dist_name + ".data"
        self.plat_name_supplied = self.plat_name is not None

        try:
            self.compression = self.supported_compressions[self.compression]
        except KeyError:
            raise ValueError(f"Unsupported compression: {self.compression}")

        need_options = ("dist_dir", "plat_name", "skip_build")

        self.set_undefined_options("bdist", *zip(need_options, need_options))

        self.root_is_pure = not (
            self.distribution.has_ext_modules() or self.distribution.has_c_libraries()
        )

        if self.py_limited_api and not re.match(
            _PY_LIMITED_API_PATTERN, self.py_limited_api
        ):
            raise ValueError("py-limited-api must match '%s'" % _PY_LIMITED_API_PATTERN)

        if self.build_number is not None and not self.build_number[:1].isdigit():
            raise ValueError("Build tag (build-number) must start with a digit.")

    def _get_dist_info_name(self):
        if self.dist_info_dir is None:
            dist_info = self.get_finalized_command("dist_info")
            self.dist_info_dir = dist_info.dist_info_dir
            return dist_info.name

        assert str(self.dist_info_dir).endswith(".dist-info")
        assert (self.dist_info_dir / "METADATA").exists()
        return self.dist_info_dir.name[: -len(".dist-info")]

    def _ensure_dist_info(self):
        if not Path(self.dist_info_dir, "METADATA").exists():
            self.run_command("dist_info")

    def get_tag(self):
        # bdist sets self.plat_name if unset, we should only use it for purepy
        # wheels if the user supplied it.

        # cibuildwheel recommends users to override get_tag, so we cannot make it
        # explicitly private, to avoid breaking people's script, see:
        # https://cibuildwheel.readthedocs.io/en/stable/faq/#abi3
        # https://github.com/joerick/python-abi3-package-sample/blob/main/setup.py

        if self.plat_name_supplied:
            plat_name = self.plat_name
        elif self.root_is_pure:
            plat_name = "any"
        else:
            # macosx contains system version in platform name so need special handle
            if self.plat_name and not self.plat_name.startswith("macosx"):
                plat_name = self.plat_name
            else:
                # on macosx always limit the platform name to comply with any
                # c-extension modules in bdist_dir, since the user can specify
                # a higher MACOSX_DEPLOYMENT_TARGET via tools like CMake

                # on other platforms, and on macosx if there are no c-extension
                # modules, use the default platform name.
                plat_name = _get_platform(self.bdist_dir)

            if (
                plat_name in ("linux-x86_64", "linux_x86_64")
                and sys.maxsize == 2147483647
            ):
                plat_name = "linux_i686"

        plat_name = (
            plat_name.lower().replace("-", "_").replace(".", "_").replace(" ", "_")
        )

        if self.root_is_pure:
            if self.universal:
                impl = "py2.py3"
            else:
                impl = self.python_tag
            tag = (impl, "none", plat_name)
        else:
            impl_name = tags.interpreter_name()
            impl_ver = tags.interpreter_version()
            impl = impl_name + impl_ver
            # We don't work on CPython 3.1, 3.0.
            if self.py_limited_api and (impl_name + impl_ver).startswith("cp3"):
                impl = self.py_limited_api
                abi_tag = "abi3"
            else:
                abi_tag = str(_get_abi_tag()).lower()
            tag = (impl, abi_tag, plat_name)
            # issue gh-374: allow overriding plat_name
            supported_tags = [
                (t.interpreter, t.abi, plat_name) for t in tags.sys_tags()
            ]
            assert (
                tag in supported_tags
            ), f"would build wheel with unsupported tag {tag}"
        return tag

    def run(self):
        self.mkpath(self.bdist_dir)
        build_scripts = self.reinitialize_command("build_scripts")
        build_scripts.executable = "python"
        build_scripts.force = True

        build_ext = self.reinitialize_command("build_ext")
        build_ext.inplace = False

        if not self.skip_build:
            self.run_command("build")

        install = self.reinitialize_command("install", reinit_subcommands=True)
        install.root = self.bdist_dir
        install.compile = False
        install.skip_build = self.skip_build
        install.warn_dir = False
        # install.skip_egg_info = True

        # A wheel without setuptools scripts is more cross-platform.
        # Use the (undocumented) `no_ep` option to setuptools'
        # install_scripts command to avoid creating entry point scripts.
        install_scripts = self.reinitialize_command("install_scripts")
        install_scripts.no_ep = True

        # Use a custom scheme for the archive, because we have to decide
        # at installation time which scheme to use.
        for key in ("headers", "scripts", "data", "purelib", "platlib"):
            setattr(install, "install_" + key, os.path.join(self.data_dir, key))

        basedir_observed = ""

        if os.name == "nt":
            # win32 barfs if any of these are ''; could be '.'?
            # (distutils.command.install:change_roots bug)
            basedir_observed = os.path.normpath(os.path.join(self.data_dir, ".."))
            self.install_libbase = self.install_lib = basedir_observed

        setattr(
            install,
            "install_purelib" if self.root_is_pure else "install_platlib",
            basedir_observed,
        )

        _logger.info(f"installing to {self.bdist_dir}")

        self.run_command("install")

        impl_tag, abi_tag, plat_tag = self.get_tag()
        archive_basename = f"{self._wheel_dist_name}-{impl_tag}-{abi_tag}-{plat_tag}"
        if not self.relative:
            archive_root = self.bdist_dir
        else:
            archive_root = os.path.join(
                self.bdist_dir, dir_util.ensure_relative(install.install_base)
            )

        # Make the archive
        if not os.path.exists(self.dist_dir):
            self.mkpath(self.dist_dir)

        wheel_path = os.path.join(self.dist_dir, archive_basename + ".whl")
        with WheelBuilder(wheel_path, compression=self.compression) as builder:
            builder.add_tree(archive_root, exclude=["*.dist-info/*", "*.egg-info/*"])
            self._ensure_dist_info()
            builder.add_tree(self.dist_info_dir, prefix=self.dist_info_dir.name)

        # Add to 'Distribution.dist_files' so that the "upload" command works
        getattr(self.distribution, "dist_files", []).append(
            (
                "bdist_wheel",
                "{}.{}".format(*sys.version_info[:2]),  # like 3.7
                wheel_path,
            )
        )

        if not self.keep_temp:
            # use dir_util to keep its state caching consistent
            dir_util.remove_tree(self.bdist_dir, self.verbose, self.dry_run)
            if os.path.isdir(self.bdist_dir) and not self.dry_run:
                # force removal in the case dir_util cannot handle it
                shutil.rmtree(self.bdist_dir, onerror=_remove_readonly)


def _remove_readonly(func, path, excinfo):
    print(str(excinfo[1]))
    os.chmod(path, stat.S_IWRITE)
    func(path)
