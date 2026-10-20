from __future__ import annotations

import builtins
import importlib
import os.path
import platform
import shutil
import stat
import struct
import subprocess
import sys
import sysconfig
from contextlib import nullcontext, suppress
from inspect import cleandoc
from zipfile import ZipFile

import jaraco.path
import pytest
from packaging import tags

import setuptools
from setuptools.archive_util import unpack_zipfile
from setuptools.command.bdist_wheel import (
    _interpreter_name,
    _is_32bit_interpreter,
    _is_debug,
    _python_version,
    bdist_wheel,
    get_abi_tag,
    get_platform,
    stable_abi_tag,
)
from setuptools.command.build_ext import get_abi3_suffix
from setuptools.dist import Distribution
from setuptools.warnings import SetuptoolsDeprecationWarning

from distutils.core import run_setup
from distutils.sysconfig import get_config_vars as get_distutils_config_vars

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
        "licenses_dir": {"DUMMYFILE": ""},
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
                zip_safe=True,
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
    "licenses-dist": {
        "setup.cfg": cleandoc(
            """
            [metadata]
            name = licenses-dist
            version = 1.0
            license_files = **/LICENSE
            """
        ),
        "LICENSE": "",
        "src": {
            "vendor": {"LICENSE": ""},
        },
    },
}


IS_FREE_THREADED = bool(sysconfig.get_config_var('Py_GIL_DISABLED'))

# ABI3 extensions don't really work on Windows, and free-threaded builds only
# support the limited API on 3.15 and newer, where they target the abi3t
# stable ABI (PEP 803). See https://github.com/python/cpython/issues/146636.
if sys.platform != 'win32' and (not IS_FREE_THREADED or sys.version_info >= (3, 15)):
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
        "extension.c": "#define Py_LIMITED_API "
        + ("0x030F0000" if IS_FREE_THREADED else "0x03020000")
        + "\n#include <Python.h>",
    }


def bdist_wheel_cmd(**kwargs):
    """Run command in the same process so that it is easier to collect coverage"""
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
    basedir = tmp_path_factory.mktemp(name)
    jaraco.path.build(EXAMPLES[name], prefix=str(basedir))
    return basedir


@pytest.fixture(scope="session")
def wheel_paths(tmp_path_factory):
    build_base = tmp_path_factory.mktemp("build")
    dist_dir = tmp_path_factory.mktemp("dist")
    for name in EXAMPLES:
        example_dir = mkexample(tmp_path_factory, name)
        build_dir = build_base / name
        with jaraco.path.DirectoryStack().context(example_dir):
            bdist_wheel_cmd(bdist_dir=str(build_dir), dist_dir=str(dist_dir)).run()

    return sorted(str(fname) for fname in dist_dir.glob("*.whl"))


@pytest.fixture
def dummy_dist(tmp_path_factory):
    return mkexample(tmp_path_factory, "dummy-dist")


@pytest.fixture
def licenses_dist(tmp_path_factory):
    return mkexample(tmp_path_factory, "licenses-dist")


@pytest.mark.parametrize('version', ['3.14', '3.15'])
def test_dist_files_target_version(dummy_dist, monkeypatch, version):
    monkeypatch.chdir(dummy_dist)
    monkeypatch.setitem(sysconfig.get_config_vars(), 'VERSION', version)
    cmd = bdist_wheel_cmd()
    cmd.run()
    assert cmd.distribution.dist_files[0][1] == version


def test_no_scripts(wheel_paths):
    """Make sure entry point scripts are not generated."""
    path = next(path for path in wheel_paths if "complex_dist" in path)
    for entry in ZipFile(path).infolist():
        assert ".data/scripts/" not in entry.filename


def test_unicode_record(wheel_paths):
    path = next(path for path in wheel_paths if "unicode_dist" in path)
    with ZipFile(path) as zf:
        record = zf.read("unicode_dist-0.1.dist-info/RECORD")

    assert "åäö_日本語.py".encode() in record


UTF8_PKG_INFO = """\
Metadata-Version: 2.1
Name: helloworld
Version: 42
Author-email: "John X. Ãørçeč" <john@utf8.org>, Γαμα קּ 東 <gama@utf8.org>


UTF-8 描述 説明
"""


def test_preserve_unicode_metadata(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    egginfo = tmp_path / "dummy_dist.egg-info"
    distinfo = tmp_path / "dummy_dist.dist-info"

    egginfo.mkdir()
    (egginfo / "PKG-INFO").write_text(UTF8_PKG_INFO, encoding="utf-8")
    (egginfo / "dependency_links.txt").touch()

    class simpler_bdist_wheel(bdist_wheel):
        """Avoid messing with setuptools/distutils internals"""

        def __init__(self) -> None:
            pass

        @property
        def license_paths(self):
            return []

    cmd_obj = simpler_bdist_wheel()
    cmd_obj.egg2dist(egginfo, distinfo)

    metadata = (distinfo / "METADATA").read_text(encoding="utf-8")
    assert 'Author-email: "John X. Ãørçeč"' in metadata
    assert "Γαμα קּ 東 " in metadata
    assert "UTF-8 描述 説明" in metadata


def test_licenses_default(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path)).run()
    with ZipFile("dist/dummy_dist-1.0-py3-none-any.whl") as wf:
        license_files = {
            "dummy_dist-1.0.dist-info/licenses/" + fname
            for fname in DEFAULT_LICENSE_FILES
        }
        assert set(wf.namelist()) == DEFAULT_FILES | license_files


def test_licenses_deprecated(dummy_dist, monkeypatch, tmp_path):
    dummy_dist.joinpath("setup.cfg").write_text(
        "[metadata]\nlicense_file=licenses_dir/DUMMYFILE", encoding="utf-8"
    )
    monkeypatch.chdir(dummy_dist)

    bdist_wheel_cmd(bdist_dir=str(tmp_path)).run()

    with ZipFile("dist/dummy_dist-1.0-py3-none-any.whl") as wf:
        license_files = {"dummy_dist-1.0.dist-info/licenses/licenses_dir/DUMMYFILE"}
        assert set(wf.namelist()) == DEFAULT_FILES | license_files


@pytest.mark.parametrize(
    ("config_file", "config"),
    [
        ("setup.cfg", "[metadata]\nlicense_files=licenses_dir/*\n  LICENSE"),
        ("setup.cfg", "[metadata]\nlicense_files=licenses_dir/*, LICENSE"),
        (
            "setup.py",
            SETUPPY_EXAMPLE.replace(
                ")", "  license_files=['licenses_dir/DUMMYFILE', 'LICENSE'])"
            ),
        ),
    ],
)
def test_licenses_override(dummy_dist, monkeypatch, tmp_path, config_file, config):
    dummy_dist.joinpath(config_file).write_text(config, encoding="utf-8")
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path)).run()
    with ZipFile("dist/dummy_dist-1.0-py3-none-any.whl") as wf:
        license_files = {
            "dummy_dist-1.0.dist-info/licenses/" + fname
            for fname in ("licenses_dir/DUMMYFILE", "LICENSE")
        }
        assert set(wf.namelist()) == DEFAULT_FILES | license_files
        metadata = wf.read("dummy_dist-1.0.dist-info/METADATA").decode("utf8")
        assert "License-File: licenses_dir/DUMMYFILE" in metadata
        assert "License-File: LICENSE" in metadata


def test_licenses_preserve_folder_structure(licenses_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(licenses_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path)).run()
    print(os.listdir("dist"))
    with ZipFile("dist/licenses_dist-1.0-py3-none-any.whl") as wf:
        default_files = {name.replace("dummy_", "licenses_") for name in DEFAULT_FILES}
        license_files = {
            "licenses_dist-1.0.dist-info/licenses/LICENSE",
            "licenses_dist-1.0.dist-info/licenses/src/vendor/LICENSE",
        }
        assert set(wf.namelist()) == default_files | license_files
        metadata = wf.read("licenses_dist-1.0.dist-info/METADATA").decode("utf8")
        assert "License-File: src/vendor/LICENSE" in metadata
        assert "License-File: LICENSE" in metadata


def test_licenses_disabled(dummy_dist, monkeypatch, tmp_path):
    dummy_dist.joinpath("setup.cfg").write_text(
        "[metadata]\nlicense_files=\n", encoding="utf-8"
    )
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path)).run()
    with ZipFile("dist/dummy_dist-1.0-py3-none-any.whl") as wf:
        assert set(wf.namelist()) == DEFAULT_FILES


def test_build_number(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), build_number="2").run()
    with ZipFile("dist/dummy_dist-1.0-2-py3-none-any.whl") as wf:
        filenames = set(wf.namelist())
        assert "dummy_dist-1.0.dist-info/RECORD" in filenames
        assert "dummy_dist-1.0.dist-info/METADATA" in filenames


def test_universal_deprecated(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(dummy_dist)
    with pytest.warns(SetuptoolsDeprecationWarning, match=".*universal is deprecated"):
        bdist_wheel_cmd(bdist_dir=str(tmp_path), universal=True).run()

    # For now we still respect the option
    assert os.path.exists("dist/dummy_dist-1.0-py2.py3-none-any.whl")


LIMITED_API_PREAMBLE = """\
/* Include pyconfig.h first so Py_GIL_DISABLED is known before choosing a
   stable ABI to target. On free-threaded Windows, Py_GIL_DISABLED is not in
   pyconfig.h but is passed on the command line by setuptools. */
#include <pyconfig.h>

#ifdef Py_GIL_DISABLED
/* Free-threaded builds only support the limited API for 3.15 or newer,
   targeting the abi3t stable ABI (PEP 803). */
#define Py_LIMITED_API 0x030F0000
#else
#define Py_LIMITED_API 0x03020000
#endif

"""

EXTENSION_BODY = """\
#include <Python.h>

static PyMethodDef methods[] = {
  { NULL, NULL, 0, NULL }
};

#ifdef Py_TARGET_ABI3T
/* abi3t makes PyObject opaque, so a static PyModuleDef and PyInit_* cannot
   be used; export the module with slots instead (PEP 793). */
PyABIInfo_VAR(abi_info);

static PySlot slots[] = {
  PySlot_STATIC_DATA(Py_mod_abi, &abi_info),
  PySlot_STATIC_DATA(Py_mod_name, "extension"),
  PySlot_STATIC_DATA(Py_mod_doc, "Dummy extension module"),
  PySlot_STATIC_DATA(Py_mod_methods, methods),
  PySlot_DATA(Py_mod_gil, Py_MOD_GIL_NOT_USED),
  PySlot_END,
};

PyMODEXPORT_FUNC PyModExport_extension(void);

PyMODEXPORT_FUNC PyModExport_extension(void) {
  return slots;
}
#else
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
#endif
"""

EXTENSION_EXAMPLE = LIMITED_API_PREAMBLE + EXTENSION_BODY
EXTENSION_SETUPPY = """\
from __future__ import annotations

from setuptools import Extension, setup

setup(
    name="extension.dist",
    version="0.1",
    description="A testing distribution \N{SNOWMAN}",
    ext_modules=[
        Extension(
            name="extension",
            sources=["extension.c"],
            py_limited_api=True
        )
    ],
)
"""


VERSION_SPECIFIC_SETUPPY = """\
from __future__ import annotations

from setuptools import Extension, setup

setup(
    name="extension.dist",
    version="0.1",
    description="A testing distribution \N{SNOWMAN}",
    ext_modules=[Extension(name="extension", sources=["extension.c"])],
)
"""


@pytest.mark.filterwarnings(
    "once:Config variable '.*' is unset.*, Python ABI tag may be incorrect"
)
@pytest.mark.parametrize('skip_build', [False, True])
def test_limited_api(monkeypatch, tmp_path, tmp_path_factory, skip_build):
    """Test that building a binary wheel with the limited ABI works."""
    source_dir = tmp_path_factory.mktemp("extension_dist")
    (source_dir / "setup.py").write_text(EXTENSION_SETUPPY, encoding="utf-8")
    (source_dir / "extension.c").write_text(EXTENSION_EXAMPLE, encoding="utf-8")
    build_dir = tmp_path.joinpath("build")
    dist_dir = tmp_path.joinpath("dist")
    monkeypatch.chdir(source_dir)
    # The free-threaded build doesn't support the limited API until 3.15.
    ft_unsupported = IS_FREE_THREADED and sys.version_info < (3, 15)
    expectation = pytest.raises(ValueError) if ft_unsupported else nullcontext()
    with expectation:
        cmd = bdist_wheel_cmd(
            bdist_dir=str(build_dir),
            dist_dir=str(dist_dir),
            py_limited_api="cp32",
            skip_build=skip_build,
        )
        if skip_build:
            cmd.run_command('build_ext')
        cmd.run()

    if ft_unsupported:  # pragma: no cover
        return

    abi = get_abi_tag()
    if tags.interpreter_name() == 'cp':
        abi = 'abi3.abi3t' if IS_FREE_THREADED else 'abi3'
    wheel = next(dist_dir.glob('*.whl'))
    assert f'-{abi}-' in wheel.name
    installed = tmp_path / 'installed'
    with ZipFile(wheel) as archive:
        suffix = get_abi3_suffix() or sysconfig.get_config_var('EXT_SUFFIX')
        assert 'extension' + suffix in archive.namelist()
        metadata = archive.read('extension_dist-0.1.dist-info/WHEEL').decode()
        for tag in tags.parse_tag('-'.join(wheel.stem.split('-')[-3:])):
            assert f'Tag: {tag}\n' in metadata
    # Cygwin requires executable permissions when loading DLLs.
    unpack_zipfile(wheel, installed)
    subprocess.run(
        [
            sys.executable,
            '-c',
            'import extension; assert extension.__doc__ == "Dummy extension module"',
        ],
        cwd=installed,
        check=True,
    )


@pytest.mark.filterwarnings(
    "once:Config variable '.*' is unset.*, Python ABI tag may be incorrect"
)
@pytest.mark.parametrize('limited_api', [False, True])
def test_version_specific_abi(monkeypatch, tmp_path, tmp_path_factory, limited_api):
    """Version-specific wheels must import with or without py_limited_api."""
    source_dir = tmp_path_factory.mktemp("extension_dist")
    setup_py = EXTENSION_SETUPPY if limited_api else VERSION_SPECIFIC_SETUPPY
    (source_dir / "setup.py").write_text(setup_py, encoding="utf-8")
    (source_dir / "extension.c").write_text(EXTENSION_BODY, encoding="utf-8")
    build_dir = tmp_path.joinpath("build")
    dist_dir = tmp_path.joinpath("dist")
    monkeypatch.chdir(source_dir)
    bdist_wheel_cmd(bdist_dir=str(build_dir), dist_dir=str(dist_dir)).run()
    wheel_path = next(dist_dir.glob("*.whl"))
    assert f"-{get_abi_tag()}-" in wheel_path.name
    installed = tmp_path / 'installed'
    unpack_zipfile(wheel_path, installed)
    subprocess.run(
        [sys.executable, '-c', 'import extension'], cwd=installed, check=True
    )


@pytest.mark.skipif(
    'abi3extension-dist' not in EXAMPLES or not get_abi3_suffix(),
    reason='requires stable-ABI suffix support',
)
@pytest.mark.parametrize('skip_build', [False, True])
def test_abi3_filename_consistent(monkeypatch, tmp_path, tmp_path_factory, skip_build):
    """Wheel creation must not change the build command's output filenames."""
    from distutils.sysconfig import get_config_vars

    monkeypatch.chdir(mkexample(tmp_path_factory, 'abi3extension-dist'))
    monkeypatch.setitem(get_config_vars(), 'SOABI_PLATFORM', 'target-platform')
    ext = os.path.splitext(get_config_vars()['EXT_SUFFIX'])[1]
    abi = 'abi3t' if IS_FREE_THREADED else 'abi3'
    cmd = bdist_wheel_cmd(
        py_limited_api='cp32', dist_dir=str(tmp_path), skip_build=skip_build
    )
    build_ext = cmd.get_finalized_command('build_ext')
    outputs = build_ext.get_outputs()
    if skip_build:
        cmd.run_command('build_ext')
    cmd.run()
    assert build_ext.get_outputs() == outputs
    wheel = next(tmp_path.glob('*.whl'))
    with ZipFile(wheel) as archive:
        assert f'extension.{abi}-target-platform{ext}' in archive.namelist()


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
    ("option", "compress_type"),
    list(bdist_wheel.supported_compressions.items()),
    ids=list(bdist_wheel.supported_compressions),
)
def test_compression(dummy_dist, monkeypatch, tmp_path, option, compress_type):
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(bdist_dir=str(tmp_path), compression=option).run()
    with ZipFile("dist/dummy_dist-1.0-py3-none-any.whl") as wf:
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
    bdist_wheel_cmd(bdist_dir=str(tmp_path), build_number="2a").run()
    with ZipFile("dist/dummy_dist-1.0-2a-py3-none-any.whl") as wf:
        for zinfo in wf.filelist:
            assert zinfo.date_time >= (1980, 1, 1, 0, 0, 0)  # min epoch is used


@pytest.mark.parametrize('free_threaded', [False, True])
@pytest.mark.parametrize('debug', [False, True])
@pytest.mark.parametrize('debug_var', [False, True])
def test_get_abi_tag_windows(monkeypatch, free_threaded, debug, debug_var):
    abi = 'cp313t' if free_threaded else 'cp313'
    config = {
        'SOABI': f'{abi}-win_amd64',
        'EXT_SUFFIX': f'{"_d" if debug else ""}.{abi}-win_amd64.pyd',
        'Py_DEBUG': int(debug) if debug_var else None,
    }
    monkeypatch.setattr(sysconfig, 'get_config_var', config.get)
    monkeypatch.setattr(sys, "gettotalrefcount", lambda: 1, False)
    expected = abi + ('d' if debug else '')
    assert get_abi_tag() == expected
    monkeypatch.delattr(sys, "gettotalrefcount")
    assert get_abi_tag() == expected


@pytest.mark.parametrize('debug', [False, True])
def test_get_abi_tag_windows_without_soabi(monkeypatch, debug):
    config = {'VERSION': '312', 'EXT_SUFFIX': '_d.pyd' if debug else '.pyd'}
    monkeypatch.setattr(sysconfig, 'get_config_var', config.get)
    monkeypatch.setattr(tags, 'interpreter_name', lambda: 'cp')
    monkeypatch.setattr(sys, 'gettotalrefcount', lambda: 1, raising=False)
    with pytest.warns(RuntimeWarning, match="Config variable 'Py_DEBUG' is unset"):
        assert get_abi_tag() == ('cp312d' if debug else 'cp312')


@pytest.mark.parametrize('debug', [False, True])
def test_is_debug_from_sysconfig(monkeypatch, debug):
    config = {'Py_DEBUG': int(debug), 'EXT_SUFFIX': '.pyd' if debug else '_d.pyd'}
    monkeypatch.setattr(sysconfig, 'get_config_var', config.get)
    assert _is_debug() is debug


def test_get_abi_tag_pypy_old(monkeypatch):
    monkeypatch.setattr(tags, "interpreter_name", lambda: "pp")
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: "pypy36-pp73")
    assert get_abi_tag() == "pypy36_pp73"


def test_get_abi_tag_pypy_new(monkeypatch):
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: "pypy37-pp73-darwin")
    monkeypatch.setattr(tags, "interpreter_name", lambda: "pp")
    assert get_abi_tag() == "pypy37_pp73"


def test_get_abi_tag_graalpy(monkeypatch):
    monkeypatch.setattr(
        sysconfig, "get_config_var", lambda x: "graalpy231-310-native-x86_64-linux"
    )
    monkeypatch.setattr(tags, "interpreter_name", lambda: "graalpy")
    assert get_abi_tag() == "graalpy231_310_native"


def test_get_abi_tag_fallback(monkeypatch):
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: "unknown-python-310")
    monkeypatch.setattr(tags, "interpreter_name", lambda: "unknown-python")
    assert get_abi_tag() == "unknown_python_310"


def test_stable_abi_tag(monkeypatch):
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: 0)
    assert stable_abi_tag("cp", "315") == "abi3"
    monkeypatch.setattr(sysconfig, "get_config_var", lambda x: '1')
    assert stable_abi_tag("cp", "315") == "abi3.abi3t"


@pytest.mark.parametrize('host_version', [(3, 14), (3, 15)])
@pytest.mark.parametrize('target_version', [(3, 14), (3, 15)])
@pytest.mark.parametrize('version_available', [False, True])
@pytest.mark.parametrize('free_threaded', [False, True])
@pytest.mark.parametrize('limited_api', [False, 'cp32'])
@pytest.mark.parametrize(('arch', 'pointer_size'), [('aarch64', 8), ('i686', 4)])
def test_cross_tags(
    monkeypatch,
    host_version,
    target_version,
    version_available,
    free_threaded,
    limited_api,
    arch,
    pointer_size,
):
    """Wheel tags and extension filenames describe the target, not the host."""
    flags = 't' if free_threaded else ''
    version = ''.join(map(str, target_version))
    soabi = f'cpython-{version}{flags}-{arch}-linux-gnu'
    soabi_platform = f'{arch}-linux-gnu' if target_version >= (3, 15) else None
    config = {
        'VERSION': '.'.join(map(str, target_version)) if version_available else None,
        'SOABI': soabi,
        'SOABI_PLATFORM': soabi_platform,
        'EXT_SUFFIX': f'.{soabi}.so',
        'Py_GIL_DISABLED': int(free_threaded),
        'Py_DEBUG': 0,
        'SIZEOF_VOID_P': pointer_size,
        'HAVE_DYNAMIC_LOADING': 1,
        'DYNLOADFILE': 'dynload_shlib.o',
    }
    for name, value in config.items():
        monkeypatch.setitem(sysconfig.get_config_vars(), name, value)
        monkeypatch.setitem(get_distutils_config_vars(), name, value)
    extension = setuptools.Extension('extension', ['extension.c'], py_limited_api=True)
    cmd = bdist_wheel(Distribution({'ext_modules': [extension]}))
    cmd.root_is_pure = False
    cmd.plat_name = f'linux-{arch}'
    cmd.py_limited_api = limited_api
    build_ext = cmd.get_finalized_command('build_ext')
    monkeypatch.setattr(sys, 'version_info', (*host_version, 0, 'final', 0))
    monkeypatch.setattr(struct, 'calcsize', lambda _: 12 - pointer_size)
    monkeypatch.setattr(tags, 'interpreter_name', lambda: 'pp')
    monkeypatch.setattr(tags, 'interpreter_version', lambda: '999')

    def unexpected_sys_tags():  # pragma: no cover
        pytest.fail('tags.sys_tags() describes the host, not the target')

    monkeypatch.setattr(tags, 'sys_tags', unexpected_sys_tags)
    if limited_api and free_threaded and target_version < (3, 15):
        with pytest.raises(ValueError, match='not supported'):
            cmd._validate_py_limited_api()
        return

    cmd._validate_py_limited_api()
    impl = limited_api or f'cp{version}'
    abi = (
        ('abi3.abi3t' if free_threaded else 'abi3')
        if limited_api
        else f'cp{version}{flags}'
    )
    assert cmd.get_tag() == (impl, abi, f'linux_{arch}')
    qualifier = f'-{soabi_platform}' if soabi_platform else ''
    assert build_ext.get_ext_filename('extension') == (
        f"extension{config['EXT_SUFFIX']}"
        if free_threaded and target_version < (3, 15)
        else f'extension.abi3{flags}{qualifier}.so'
    )


@pytest.mark.parametrize('free_threaded', [False, True])
def test_limited_api_newer_than_target(monkeypatch, free_threaded):
    cmd = bdist_wheel(Distribution())
    cmd.root_is_pure = False
    cmd.plat_name = 'linux_aarch64'
    cmd.py_limited_api = 'cp316'
    config = {
        'VERSION': '3.15',
        'SOABI': f'cpython-315{"t" if free_threaded else ""}-aarch64-linux-gnu',
        'Py_GIL_DISABLED': int(free_threaded),
        'SIZEOF_VOID_P': 8,
    }
    monkeypatch.setattr(sysconfig, 'get_config_var', config.get)
    with pytest.raises(AssertionError, match='unsupported tag'):
        cmd.get_tag()


@pytest.mark.parametrize(
    ('version', 'soabi', 'expected'),
    [
        ('3.14', 'cpython-315-aarch64-linux-gnu', (3, 14)),
        ('3.15', None, (3, 15)),
        ('315', None, (3, 15)),
        (315, None, (3, 15)),
        (None, 'cpython-314-aarch64-linux-gnu', (3, 14)),
        ('invalid', 'cpython-314td-x86_64-linux-gnu', (3, 14)),
        (None, 'cp314-win_amd64', (3, 14)),
        (None, 'cp315t-win_arm64', (3, 15)),
        (None, 'pypy311-pp80', (3, 11)),
        (None, 'graalpy-38-native-x86_64-darwin', (3, 8)),
        (None, 'graalpy231-310-native-x86_64-linux', (3, 10)),
        (None, None, sys.version_info[:2]),
        ('invalid', 'unknown', sys.version_info[:2]),
        (None, 'cpython-3', sys.version_info[:2]),
        (None, 'graalpy231-', sys.version_info[:2]),
    ],
)
def test_target_python_version(monkeypatch, version, soabi, expected):
    config = {'VERSION': version, 'SOABI': soabi}
    monkeypatch.setattr(sysconfig, 'get_config_var', config.get)
    assert _python_version() == expected


@pytest.mark.parametrize(
    ('helper', 'expected'),
    [
        (_python_version, sys.version_info[:2]),
        (_interpreter_name, tags.interpreter_name()),
        (_is_32bit_interpreter, struct.calcsize('P') == 4),
        (_is_debug, hasattr(sys, 'gettotalrefcount')),
    ],
)
@pytest.mark.parametrize(
    'override',
    [
        None,
        '_PYTHON_SYSCONFIGDATA_NAME',
        '_PYTHON_SYSCONFIGDATA_PATH',
        '_PYTHON_HOST_PLATFORM',
    ],
)
def test_config_fallback(monkeypatch, helper, expected, override):
    monkeypatch.setattr(sysconfig, 'get_config_var', lambda _: None)
    if override:
        monkeypatch.setenv(override, 'override')
    assert helper() == expected


@pytest.mark.parametrize(
    ('soabi', 'implementation', 'abi'),
    [
        ('pypy311-pp73-aarch64-linux-gnu', 'pp', 'pypy311_pp73'),
        ('graalpy231-311-native-aarch64-linux', 'graalpy', 'graalpy231_311_native'),
    ],
)
def test_non_cpython_target(monkeypatch, soabi, implementation, abi):
    cmd = bdist_wheel(Distribution())
    cmd.root_is_pure = False
    cmd.plat_name = 'linux_aarch64'
    config = {'VERSION': '3.11', 'SOABI': soabi, 'SIZEOF_VOID_P': 8}
    monkeypatch.setattr(sysconfig, 'get_config_var', config.get)
    monkeypatch.setattr(tags, 'interpreter_name', lambda: 'cp')
    assert cmd.get_tag() == (f'{implementation}311', abi, 'linux_aarch64')


def test_platform_with_space(dummy_dist, monkeypatch):
    """Ensure building on platforms with a space in the name succeed."""
    monkeypatch.chdir(dummy_dist)
    bdist_wheel_cmd(plat_name="isilon onefs").run()


def test_data_dir_with_tag_build(monkeypatch, tmp_path):
    """
    Setuptools allow authors to set PEP 440's local version segments
    using ``egg_info.tag_build``. This should be reflected not only in the
    ``.whl`` file name, but also in the ``.dist-info`` and ``.data`` dirs.
    See pypa/setuptools#3997.
    """
    monkeypatch.chdir(tmp_path)
    files = {
        "setup.py": """
            from setuptools import setup
            setup(headers=["hello.h"])
            """,
        "setup.cfg": """
            [metadata]
            name = test
            version = 1.0

            [options.data_files]
            hello/world = file.txt

            [egg_info]
            tag_build = +what
            tag_date = 0
            """,
        "file.txt": "",
        "hello.h": "",
    }
    for file, content in files.items():
        with open(file, "w", encoding="utf-8") as fh:
            fh.write(cleandoc(content))

    bdist_wheel_cmd().run()

    # Ensure .whl, .dist-info and .data contain the local segment
    wheel_path = "dist/test-1.0+what-py3-none-any.whl"
    assert os.path.exists(wheel_path)
    entries = set(ZipFile(wheel_path).namelist())
    for expected in (
        "test-1.0+what.data/headers/hello.h",
        "test-1.0+what.data/data/hello/world/file.txt",
        "test-1.0+what.dist-info/METADATA",
        "test-1.0+what.dist-info/WHEEL",
    ):
        assert expected in entries

    for not_expected in (
        "test.data/headers/hello.h",
        "test-1.0.data/data/hello/world/file.txt",
        "test.dist-info/METADATA",
        "test-1.0.dist-info/WHEEL",
    ):
        assert not_expected not in entries


@pytest.mark.parametrize(
    ("reported", "expected"),
    [("linux-x86_64", "linux_i686"), ("linux-aarch64", "linux_armv7l")],
)
@pytest.mark.skipif(
    platform.system() != "Linux", reason="Only makes sense to test on Linux"
)
def test_platform_linux32(reported, expected, monkeypatch):
    monkeypatch.setitem(sysconfig.get_config_vars(), 'SIZEOF_VOID_P', 4)
    monkeypatch.setattr(struct, "calcsize", lambda x: 8)
    monkeypatch.setattr(sysconfig, 'get_platform', lambda: reported)
    assert get_platform(None) == expected
    dist = setuptools.Distribution()
    cmd = bdist_wheel(dist)
    cmd.plat_name = reported
    cmd.root_is_pure = False
    _, _, actual = cmd.get_tag()
    assert actual == expected


def test_no_ctypes(monkeypatch) -> None:
    def _fake_import(name: str, *args, **kwargs):
        if name == "ctypes":
            raise ModuleNotFoundError(f"No module named {name}")

        return importlib.__import__(name, *args, **kwargs)

    with suppress(KeyError):
        monkeypatch.delitem(sys.modules, "wheel.macosx_libfile")

    # Install an importer shim that refuses to load ctypes
    monkeypatch.setattr(builtins, "__import__", _fake_import)
    with pytest.raises(ModuleNotFoundError, match="No module named ctypes"):
        import wheel.macosx_libfile  # noqa: F401

    # Unload and reimport the bdist_wheel command module to make sure it won't try to
    # import ctypes
    monkeypatch.delitem(sys.modules, "setuptools.command.bdist_wheel")

    import setuptools.command.bdist_wheel  # noqa: F401


def test_dist_info_provided(dummy_dist, monkeypatch, tmp_path):
    monkeypatch.chdir(dummy_dist)
    distinfo = tmp_path / "dummy_dist.dist-info"

    distinfo.mkdir()
    (distinfo / "METADATA").write_text("name: helloworld", encoding="utf-8")

    # We don't control the metadata. According to PEP-517, "The hook MAY also
    # create other files inside this directory, and a build frontend MUST
    # preserve".
    (distinfo / "FOO").write_text("bar", encoding="utf-8")

    bdist_wheel_cmd(bdist_dir=str(tmp_path), dist_info_dir=str(distinfo)).run()
    expected = {
        "dummy_dist-1.0.dist-info/FOO",
        "dummy_dist-1.0.dist-info/RECORD",
    }
    with ZipFile("dist/dummy_dist-1.0-py3-none-any.whl") as wf:
        files_found = set(wf.namelist())
    # Check that all expected files are there.
    assert expected - files_found == set()
    # Make sure there is no accidental egg-info bleeding into the wheel.
    assert not [path for path in files_found if 'egg-info' in str(path)]


def test_allow_grace_period_parent_directory_license(monkeypatch, tmp_path):
    # Motivation: https://github.com/pypa/setuptools/issues/4892
    # TODO: Remove this test after deprecation period is over
    files = {
        "LICENSE.txt": "parent license",  # <---- the license files are outside
        "NOTICE.txt": "parent notice",
        "python": {
            "pyproject.toml": cleandoc(
                """
                [project]
                name = "test-proj"
                dynamic = ["version"]      # <---- testing dynamic will not break
                [tool.setuptools.dynamic]
                version.file = "VERSION"
                """
            ),
            "setup.cfg": cleandoc(
                """
                [metadata]
                license_files =
                  ../LICENSE.txt
                  ../NOTICE.txt
                """
            ),
            "VERSION": "42",
        },
    }
    jaraco.path.build(files, prefix=str(tmp_path))
    monkeypatch.chdir(tmp_path / "python")
    msg = "Pattern '../.*.txt' cannot contain '..'"
    with pytest.warns(SetuptoolsDeprecationWarning, match=msg):
        bdist_wheel_cmd().run()
    with ZipFile("dist/test_proj-42-py3-none-any.whl") as wf:
        files_found = set(wf.namelist())
        expected_files = {
            "test_proj-42.dist-info/licenses/LICENSE.txt",
            "test_proj-42.dist-info/licenses/NOTICE.txt",
        }
        assert expected_files <= files_found

        metadata = wf.read("test_proj-42.dist-info/METADATA").decode("utf8")
        assert "License-File: LICENSE.txt" in metadata
        assert "License-File: NOTICE.txt" in metadata
