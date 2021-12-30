from __future__ import annotations

import os
import sys
import sysconfig

from wheel.bdist_wheel import get_platform
from wheel.macosx_libfile import extract_macosx_min_system_version


def test_read_from_dylib():
    dirname = os.path.dirname(__file__)
    dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
    versions = [
        ("test_lib_10_6_fat.dylib", "10.6.0"),
        ("test_lib_10_10_fat.dylib", "10.10.0"),
        ("test_lib_10_14_fat.dylib", "10.14.0"),
        ("test_lib_10_6.dylib", "10.6.0"),
        ("test_lib_10_10.dylib", "10.10.0"),
        ("test_lib_10_14.dylib", "10.14.0"),
        ("test_lib_10_6_386.dylib", "10.6.0"),
        ("test_lib_10_10_386.dylib", "10.10.0"),
        ("test_lib_10_14_386.dylib", "10.14.0"),
        ("test_lib_multiple_fat.dylib", "10.14.0"),
        ("test_lib_10_10_10.dylib", "10.10.10"),
        ("test_lib_11.dylib", "11.0.0"),
        ("test_lib_10_9_universal2.dylib", "10.9.0"),
    ]
    for file_name, ver in versions:
        extracted = extract_macosx_min_system_version(
            os.path.join(dylib_dir, file_name)
        )
        str_ver = ".".join([str(x) for x in extracted])
        assert str_ver == ver
    assert (
        extract_macosx_min_system_version(os.path.join(dylib_dir, "test_lib.c")) is None
    )
    assert (
        extract_macosx_min_system_version(os.path.join(dylib_dir, "libb.dylib")) is None
    )


def return_factory(return_val):
    def fun(*args, **kwargs):
        return return_val

    return fun


class TestGetPlatformMacosx:
    def test_simple(self, monkeypatch):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-11.0-x86_64")
        )
        assert get_platform(dylib_dir) == "macosx_11_0_x86_64"

    def test_version_bump(self, monkeypatch, capsys):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        assert get_platform(dylib_dir) == "macosx_11_0_x86_64"
        captured = capsys.readouterr()
        assert "[WARNING] This wheel needs a higher macOS version than" in captured.err

    def test_information_about_problematic_files_python_version(
        self, monkeypatch, capsys
    ):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [(dylib_dir, [], ["test_lib_10_6.dylib", "test_lib_10_10_fat.dylib"])]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_10_10_x86_64"
        captured = capsys.readouterr()
        assert "[WARNING] This wheel needs a higher macOS version than" in captured.err
        assert (
            "the version your Python interpreter is compiled against." in captured.err
        )
        assert "test_lib_10_10_fat.dylib" in captured.err

    def test_information_about_problematic_files_env_variable(
        self, monkeypatch, capsys
    ):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", "10.8")
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [(dylib_dir, [], ["test_lib_10_6.dylib", "test_lib_10_10_fat.dylib"])]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_10_10_x86_64"
        captured = capsys.readouterr()
        assert "[WARNING] This wheel needs a higher macOS version than" in captured.err
        assert "is set in MACOSX_DEPLOYMENT_TARGET variable." in captured.err
        assert "test_lib_10_10_fat.dylib" in captured.err

    def test_bump_platform_tag_by_env_variable(self, monkeypatch, capsys):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [(dylib_dir, [], ["test_lib_10_6.dylib", "test_lib_10_6_fat.dylib"])]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_10_9_x86_64"
        monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", "10.10")
        assert get_platform(dylib_dir) == "macosx_10_10_x86_64"
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_bugfix_release_platform_tag(self, monkeypatch, capsys):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [
                    (
                        dylib_dir,
                        [],
                        [
                            "test_lib_10_6.dylib",
                            "test_lib_10_6_fat.dylib",
                            "test_lib_10_10_10.dylib",
                        ],
                    )
                ]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_10_10_x86_64"
        captured = capsys.readouterr()
        assert "This wheel needs a higher macOS version than" in captured.err
        monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", "10.9")
        assert get_platform(dylib_dir) == "macosx_10_10_x86_64"
        captured = capsys.readouterr()
        assert "This wheel needs a higher macOS version than" in captured.err

    def test_warning_on_to_low_env_variable(self, monkeypatch, capsys):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", "10.8")
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [(dylib_dir, [], ["test_lib_10_6.dylib", "test_lib_10_6_fat.dylib"])]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_10_9_x86_64"
        captured = capsys.readouterr()
        assert (
            "MACOSX_DEPLOYMENT_TARGET is set to a lower value (10.8) than the"
            in captured.err
        )

    def test_get_platform_bigsur_env(self, monkeypatch):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-10.9-x86_64")
        )
        monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", "11")
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [(dylib_dir, [], ["test_lib_10_6.dylib", "test_lib_10_10_fat.dylib"])]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_11_0_x86_64"

    def test_get_platform_bigsur_platform(self, monkeypatch):
        dirname = os.path.dirname(__file__)
        dylib_dir = os.path.join(dirname, "testdata", "macosx_minimal_system_version")
        monkeypatch.setattr(
            sysconfig, "get_platform", return_factory("macosx-11-x86_64")
        )
        monkeypatch.setattr(
            os,
            "walk",
            return_factory(
                [(dylib_dir, [], ["test_lib_10_6.dylib", "test_lib_10_10_fat.dylib"])]
            ),
        )
        assert get_platform(dylib_dir) == "macosx_11_0_x86_64"


def test_get_platform_linux(monkeypatch):
    monkeypatch.setattr(sysconfig, "get_platform", return_factory("linux-x86_64"))
    monkeypatch.setattr(sys, "maxsize", 2147483647)
    assert get_platform(None) == "linux_i686"
