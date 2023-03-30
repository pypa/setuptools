# This test is based on the `test_wheelfile.py` from pypa/wheel,
# which was initially distributed under the MIT License:
# Copyright (c) 2012 Daniel Holth <dholth@fastmail.fm> and contributors
import stat
import sys
import textwrap
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from setuptools._wheelbuilder import WheelBuilder


def test_write_str(tmp_path):
    with WheelBuilder(tmp_path / "test-1.0-py3-none-any.whl") as builder:
        builder.new_file("hello/héllö.py", 'print("Héllö, world!")\n')
        builder.new_file("hello/h,ll,.py", 'print("Héllö, world!")\n')

    with ZipFile(tmp_path / "test-1.0-py3-none-any.whl", "r") as zf:
        infolist = zf.infolist()
        assert len(infolist) == 4  # RECORD + WHEEL
        assert infolist[0].filename == "hello/héllö.py"
        assert infolist[0].file_size == 25
        assert infolist[1].filename == "hello/h,ll,.py"
        assert infolist[1].file_size == 25
        assert infolist[2].filename == "test-1.0.dist-info/WHEEL"
        assert infolist[3].filename == "test-1.0.dist-info/RECORD"

        record = "\n".join(
            line
            for line in str(zf.read("test-1.0.dist-info/RECORD"), "utf-8").splitlines()
            if not line.startswith("test-1.0.dist-info/WHEEL")
            # Avoid changes in setuptools versions messing with the test
        )

        expected = """\
        hello/héllö.py,sha256=bv-QV3RciQC2v3zL8Uvhd_arp40J5A9xmyubN34OVwo,25
        "hello/h,ll,.py",sha256=bv-QV3RciQC2v3zL8Uvhd_arp40J5A9xmyubN34OVwo,25
        test-1.0.dist-info/RECORD,,
        """
        assert record.strip() == textwrap.dedent(expected).strip()


def test_timestamp(tmp_path_factory, tmp_path, monkeypatch):
    build_dir = tmp_path_factory.mktemp("build")
    for filename in ("one", "two", "three"):
        (build_dir / filename).write_text(filename + "\n", encoding="utf-8")

    # The earliest date representable in TarInfos, 1980-01-01
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "315576060")

    wheel_path = tmp_path / "test-1.0-py3-none-any.whl"
    with WheelBuilder(wheel_path) as builder:
        builder.add_tree(build_dir)

    with ZipFile(wheel_path, "r") as zf:
        for info in zf.infolist():
            assert info.date_time[:3] == (1980, 1, 1)
            assert info.compress_type == ZIP_DEFLATED


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows does not support UNIX-like permissions"
)
def test_attributes(tmp_path_factory, tmp_path):
    # With the change from ZipFile.write() to .writestr(), we need to manually
    # set member attributes.
    build_dir = tmp_path_factory.mktemp("build")
    files = (("foo", 0o644), ("bar", 0o755))
    for filename, mode in files:
        path = build_dir / filename
        path.write_text(filename + "\n", encoding="utf-8")
        path.chmod(mode)

    wheel_path = tmp_path / "test-1.0-py3-none-any.whl"
    with WheelBuilder(wheel_path) as builder:
        builder.add_tree(build_dir)

    with ZipFile(wheel_path, "r") as zf:
        for filename, mode in files:
            info = zf.getinfo(filename)
            assert info.external_attr == (mode | stat.S_IFREG) << 16
            assert info.compress_type == ZIP_DEFLATED

        info = zf.getinfo("test-1.0.dist-info/RECORD")
        assert info.external_attr == (0o664 | stat.S_IFREG) << 16
