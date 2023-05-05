# The original version of this file was adopted from pypa/wheel,
# initially distributed under the MIT License:
# Copyright (c) 2012 Daniel Holth <dholth@fastmail.fm> and contributors
import os.path
import shutil
import stat
import sys
import sysconfig
from inspect import cleandoc
from zipfile import ZipFile

import pytest
from jaraco.path import DirectoryStack
from jaraco.path import build as build_paths

from distutils.core import run_setup
from setuptools.command.bdist_wheel import _get_abi_tag, bdist_wheel
from setuptools.dist import Distribution
from setuptools.extern.packaging import tags
from setuptools.warnings import SetuptoolsDeprecationWarning

DEFAULT_FILES = {
    "dummy_dist-1.0.dist-info/top_level.txt",
    "dummy_dist-1.0.dist-info/METADATA",
    "dummy_dist-1.0.dist-info/WHEEL",
    "dummy_dist-1.0.dist-info/RECORD",
}
DEFAULT_LICENSE_FILES = {
    "LICENSE",
    "LICENSE.txt",
    "LICENCE",
    "LICENCE.txt",
    "COPYING",
    "COPYING.md",
    "NOTICE",
    "NOTICE.rst",
    "AUTHORS",
    "AUTHORS.txt",
}
OTHER_IGNORED_FILES = {
    "LICENSE~",
    "AUTHORS~",
}
SETUPPY_EXAMPLE = """\
from setuptools import setup

setup(
    name='dummy_dist',
    version='1.0',
)
"""


EXAMPLES = {
    "dummy-dist": {
        "setup.py": SETUPPY_EXAMPLE,
        "licenses": {"DUMMYFILE": ""},
        **dict.fromkeys(DEFAULT_LICENSE_FILES | OTHER_IGNORED_FILES, ""),
    },
    "simple-dist": {
        "setup.py": cleandoc(
            """
            from setuptools import setup

            setup(
                name="simple.dist",
                version="0.1",
                description="A testing distribution \N{SNOWMAN}",
                extras_require={"voting": ["beaglevote"]},
            )
            """
        ),
        "simpledist": "",
    },
    "complex-dist": {
        "setup.py": cleandoc(
            """
            from setuptools import setup

            setup(
                name="complex-dist",
                version="0.1",
                description="Another testing distribution \N{SNOWMAN}",
                long_description="Another testing distribution \N{SNOWMAN}",
                author="Illustrious Author",
                author_email="illustrious@example.org",
                url="http://example.org/exemplary",
                packages=["complexdist"],
                setup_requires=["setuptools"],
                install_requires=["quux", "splort"],
                extras_require={"simple": ["simple.dist"]},
                tests_require=["foo", "bar>=10.0.0"],
                entry_points={
                    "console_scripts": [
                        "complex-dist=complexdist:main",
                        "complex-dist2=complexdist:main",
                    ],
                },
            )
            """
        ),
        "complexdist": {"__init__.py": "def main(): return"},
    },
    "headers-dist": {
        "setup.py": cleandoc(
            """
            from setuptools import setup

            setup(
                name="headers.dist",
                version="0.1",
                description="A distribution with headers",
                headers=["header.h"],
            )
            """
        ),
        "setup.cfg": "[bdist_wheel]\nuniversal=1",
        "headersdist.py": "",
        "header.h": "",
    },
    "commasinfilenames-dist": {
        "setup.py": cleandoc(
            """
            from setuptools import setup

            setup(
                name="testrepo",
                version="0.1",
                packages=["mypackage"],
                description="A test package with commas in file names",
                include_package_data=True,
                package_data={"mypackage.data": ["*"]},
            )
            """
        ),
        "mypackage": {
            "__init__.py": "",
            "data": {"__init__.py": "", "1,2,3.txt": ""},
        },
        "testrepo-0.1.0": {
            "mypackage": {"__init__.py": ""},
        },
    },
    "unicode-dist": {
        "setup.py": cleandoc(
            """
            from setuptools import setup

            setup(
                name="unicode.dist",
                version="0.1",
                description="A testing distribution \N{SNOWMAN}",
                packages=["unicodedist"],
            )
            """
        ),
        "unicodedist": {"__init__.py": "", "åäö_日本語.py": ""},
    },
    "utf8-metadata-dist": {
        "setup.cfg": cleandoc(
            """
            [metadata]
            name = utf8-metadata-dist
            version = 42
            author_email = "John X. Ãørçeč" <john@utf8.org>, Γαμα קּ 東 <gama@utf8.org>
            long_description = file: README.rst
            """
        ),
        "README.rst": "UTF-8 描述 説明",
    },
}


if sys.platform != "win32":
    EXAMPLES["abi3extension-dist"] = {
        "setup.py": cleandoc(
            """
            from setuptools import Extension, setup

            setup(
                name="extension.dist",
                version="0.1",
                description="A testing distribution \N{SNOWMAN}",
                ext_modules=[
                    Extension(
                        name="extension", sources=["extension.c"], py_limited_api=True
                    )
                ],
            )
            """
        ),
        "setup.cfg": "[bdist_wheel]\npy_limited_api=cp32",
        "extension.c": "#define Py_LIMITED_API 0x03020000\n#include <Python.h>",
    }


def bdist_wheel_cmd(**kwargs):
    dist_obj = (
        run_setup("setup.py", stop_after="init")
        if os.path.exists("setup.py")
        else Distribution({"script_name": "%%build_meta%%"})
    )
    dist_obj.parse_config_files()
    cmd = bdist_wheel(dist_obj)
    for attr, value in kwargs.items():
        setattr(cmd, attr, value)
    cmd.finalize_options()
    return cmd


def mkexample(tmp_path_factory, name):
    """Make sure entry point scripts are not generated."""
    basedir = tmp_path_factory.mktemp(name)
    build_paths(EXAMPLES[name], prefix=str(basedir))
    return basedir


def mkwheel(build_dir=".build", dist_dir=".dist"):
    bdist_wheel_cmd(bdist_dir=str(build_dir), dist_dir=str(dist_dir)).run()


@pytest.fixture(scope="session")
def wheel_paths(tmp_path_factory):
    build_dir = tmp_path_factory.mktemp("build")
    dist_dir = tmp_path_factory.mktemp("dist")
    for name in EXAMPLES:
        basedir = mkexample(tmp_path_factory, name)
        with DirectoryStack().context(basedir):
            bdist_wheel_cmd(bdist_dir=str(build_dir), dist_dir=str(dist_dir)).run()

    return sorted(str(fname) for fname in dist_dir.glob("*.whl"))


@pytest.fixture
def dummy_dist(tmp_path_factory):
    return mkexample(tmp_path_factory, "dummy-dist")


def test_no_scripts(wheel_paths):
    """Make sure entry point scripts are not generated."""
    path = next(path for path in wheel_paths if "complex_dist" in path)
    for entry in ZipFile(path).infolist():
        assert ".data/scripts/" not in entry.filename


def test_unicode_record(wheel_paths):
    path = next(path for path in wheel_paths if "unicode.dist" in path)
    with ZipFile(path) as zf:
        record = zf.read("unicode.dist-0.1.dist-info/RECORD")

    assert "åäö_日本語.py".encode() in record


def test_unicode_metadata(wheel_paths):
    path = next(path for path in wheel_paths if "utf8_metadata_dist" in path)
    with ZipFile(path) as zf:
        metadata = str(zf.read("utf8_metadata_dist-42.dist-info/METADATA"), "utf-8")
    assert 'Author-email: "John X. Ãørçeč"' in metadata
    assert "Γαμα קּ 東 " in metadata
    assert "UTF-8 描述 説明" in metadata


def test_licenses_default(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(dummy_dist)

    bdist_wheel_cmd(bdist_dir=str(tmp_path), universal=True).run()
    with ZipFile("dist/dummy_dist-1.0-py2.py3-none-any.whl") as wf:
        license_files = {
            "dummy_dist-1.0.dist-info/" + fname for fname in DEFAULT_LICENSE_FILES
        }
        assert set(wf.namelist()) == DEFAULT_FILES | license_files


@pytest.mark.filterwarnings("ignore:.*license_file parameter is deprecated")
def test_licenses_deprecated(dummy_dist, monkeypatch, tmp_path):
    dummy_dist.joinpath("setup.cfg").write_text(
        "[metadata]\nlicense_file=licenses/DUMMYFILE", encoding="utf-8"
    )
    monkeypatch.chdir(dummy_dist)

    with pytest.warns(SetuptoolsDeprecationWarning, match="use license_files"):
        bdist_wheel_cmd(bdist_dir=str(tmp_path), universal=True).run()

    with ZipFile("dist/dummy_dist-1.0-py2.py3-none-any.whl") as wf:
        license_files = {"dummy_dist-1.0.dist-info/DUMMYFILE"}
        assert set(wf.namelist()) == DEFAULT_FILES | license_files


@pytest.mark.parametrize(
    "config_file, config",
    [
        ("setup.cfg", "[metadata]\nlicense_files=licenses/*\n  LICENSE"),
        ("setup.cfg", "[metadata]\nlicense_files=licenses/*, LICENSE"),
        (
            "setup.py",
            SETUPPY_EXAMPLE.replace(
                ")", "  license_files=['licenses/DUMMYFILE', 'LICENSE'])"
            ),
        ),
    ],
)
def test_licenses_override(dummy_dist, monkeypatch, tmp_path, config_file, config):
    dummy_dist.joinpath(config_file).write_text(config, encoding="utf-8")
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), universal=True).run()
    with ZipFile("dist/dummy_dist-1.0-py2.py3-none-any.whl") as wf:
        license_files = {
            "dummy_dist-1.0.dist-info/" + fname for fname in {"DUMMYFILE", "LICENSE"}
        }
        assert set(wf.namelist()) == DEFAULT_FILES | license_files


def test_licenses_disabled(dummy_dist, monkeypatch, tmp_path):
    dummy_dist.joinpath("setup.cfg").write_text(
        "[metadata]\nlicense_files=\n", encoding="utf-8"
    )
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), universal=True).run()
    with ZipFile("dist/dummy_dist-1.0-py2.py3-none-any.whl") as wf:
        assert set(wf.namelist()) == DEFAULT_FILES


def test_build_number(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), build_number="2", universal=True).run()
    with ZipFile("dist/dummy_dist-1.0-2-py2.py3-none-any.whl") as wf:
        filenames = set(wf.namelist())
        assert "dummy_dist-1.0.dist-info/RECORD" in filenames
        assert "dummy_dist-1.0.dist-info/METADATA" in filenames


EXTENSION_EXAMPLE = """\
#include <Python.h>

static PyMethodDef methods[] = {
  { NULL, NULL, 0, NULL }
};

static struct PyModuleDef module_def = {
  PyModuleDef_HEAD_INIT,
  "extension",
  "Dummy extension module",
  -1,
  methods
};

PyMODINIT_FUNC PyInit_extension(void) {
  return PyModule_Create(&module_def);
}
"""
EXTENSION_SETUPPY = """\
from __future__ import annotations

from setuptools import Extension, setup

setup(
    name="extension.dist",
    version="0.1",
    description="A testing distribution \N{SNOWMAN}",
    ext_modules=[Extension(name="extension", sources=["extension.c"])],
)
"""


@pytest.mark.filterwarnings("ignore:Config variable 'Py_DEBUG' is unset.*")
# ^-- Warning may happen in Windows (inherited from original pypa/wheel implementation)
def test_limited_abi(monkeypatch, tmp_path, tmp_path_factory):
    """Test that building a binary wheel with the limited ABI works."""
    proj_dir = tmp_path_factory.mktemp("dummy_dist")
    (proj_dir / "setup.py").write_text(EXTENSION_SETUPPY, encoding="utf-8")
    (proj_dir / "extension.c").write_text(EXTENSION_EXAMPLE, encoding="utf-8")
    build_dir = tmp_path.joinpath("build")
    dist_dir = tmp_path.joinpath("dist")
    monkeypatch.chdir(proj_dir)
    bdist_wheel_cmd(bdist_dir=str(build_dir), dist_dir=str(dist_dir)).run()


def test_build_from_readonly_tree(dummy_dist, monkeypatch, tmp_path):
    basedir = str(tmp_path.joinpath("dummy"))
    shutil.copytree(str(dummy_dist), basedir)
    monkeypatch.chdir(basedir)

    # Make the tree read-only
    for root, _dirs, files in os.walk(basedir):
        for fname in files:
            os.chmod(os.path.join(root, fname), stat.S_IREAD)

    bdist_wheel_cmd().run()


@pytest.mark.parametrize(
    "option, compress_type",
    list(bdist_wheel.supported_compressions.items()),
    ids=list(bdist_wheel.supported_compressions),
)
def test_compression(dummy_dist, monkeypatch, tmp_path, option, compress_type):
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), universal=True, compression=option).run()
    with ZipFile("dist/dummy_dist-1.0-py2.py3-none-any.whl") as wf:
        filenames = set(wf.namelist())
        assert "dummy_dist-1.0.dist-info/RECORD" in filenames
        assert "dummy_dist-1.0.dist-info/METADATA" in filenames
        for zinfo in wf.filelist:
            assert zinfo.compress_type == compress_type


def test_wheelfile_line_endings(wheel_paths):
    for path in wheel_paths:
        with ZipFile(path) as wf:
            wheelfile = next(fn for fn in wf.filelist if fn.filename.endswith("WHEEL"))
            wheelfile_contents = wf.read(wheelfile)
            assert b"\r" not in wheelfile_contents


def test_unix_epoch_timestamps(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), build_number="2a", universal=True).run()
    with ZipFile("dist/dummy_dist-1.0-2a-py2.py3-none-any.whl") as wf:
        for zinfo in wf.filelist:
            assert zinfo.date_time >= (1980, 1, 1, 0, 0, 0)  # min epoch is used


def test_get_abi_tag_old(monkeypatch):
    monkeypatch.setattr(tags, "interpreter_name", lambda: "pp")
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: "pypy36-pp73")
    assert _get_abi_tag() == "pypy36_pp73"


def test_get_abi_tag_new(monkeypatch):
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: "pypy37-pp73-darwin")
    monkeypatch.setattr(tags, "interpreter_name", lambda: "pp")
    assert _get_abi_tag() == "pypy37_pp73"


def test_platform_with_space(dummy_dist, monkeypatch):
    """Ensure building on platforms with a space in the name succeed."""
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(plat_name="isilon onefs").run()
