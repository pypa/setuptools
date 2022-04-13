"""
Create a wheel that, when installed, will make the source package 'editable'
(add it to the interpreter's path, including metadata) per PEP 660. Replaces
'setup.py develop'. Based on the setuptools develop command.
"""

# TODO doesn't behave when called outside the hook

import base64
import os
import time
from pathlib import Path

from distutils.core import Command
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pkg_resources
from setuptools import __version__

SOURCE_EPOCH_ZIP = 499162860

WHEEL_FILE = f"""\
Wheel-Version: 1.0
Generator: setuptools ({__version__})
Root-Is-Purelib: false
Tag: py3-none-any
Tag: ed-none-any
"""


class editable_wheel(Command):
    """Build 'editable' wheel for development"""

    description = "create a PEP 660 'editable' wheel"

    user_options = [
        ("dist-dir=", "d", "directory to put final built distributions in"),
    ]

    boolean_options = []

    def run(self):
        self.build_editable_wheel()

    def initialize_options(self):
        self.dist_dir = None

    def finalize_options(self):
        self.dist_info = self.get_finalized_command("dist_info")
        self.egg_base = self.dist_info.egg_base
        self.dist_info_dir = Path(self.dist_info.dist_info_dir)
        self.target = pkg_resources.normalize_path(self.egg_base)

    def build_editable_wheel(self):
        if getattr(self.distribution, "use_2to3", False):
            raise NotImplementedError("2to3 not supported")

        di = self.get_finalized_command("dist_info")
        di.egg_base = self.dist_dir
        di.finalize_options()
        self.run_command("dist_info")

        # Build extensions in-place
        self.reinitialize_command("build_ext", inplace=1)
        self.run_command("build_ext")

        mtime = time.gmtime(SOURCE_EPOCH_ZIP)[:6]

        dist_dir = Path(self.dist_dir)
        dist_info_dir = self.dist_info_dir
        fullname = self.distribution.metadata.get_fullname()
        # superfluous 'ed' tag is only a hint to the user,
        # and guarantees we can't overwrite the normal wheel
        wheel_name = f"{fullname}-ed.py3-none-any.whl"
        wheel_path = dist_dir / wheel_name

        if wheel_path.exists():
            wheel_path.unlink()

        with ZipFile(wheel_path, "a", compression=ZIP_DEFLATED) as archive:
            # copy .pth file
            pth = ZipInfo(f"{fullname}_ed.pth", mtime)
            archive.writestr(pth, f"{self.target}\n")

            # copy .dist-info directory
            for f in sorted(os.listdir(dist_dir / dist_info_dir)):
                with (dist_dir / dist_info_dir / f).open() as metadata:
                    info = ZipInfo(str(dist_info_dir / f), mtime)
                    archive.writestr(info, metadata.read())

            # Add WHEEL file
            info = ZipInfo(str(dist_info_dir / "WHEEL"), mtime)
            archive.writestr(info, WHEEL_FILE)

            add_manifest(archive, dist_info_dir)


def urlsafe_b64encode(data):
    """urlsafe_b64encode without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b"=")


# standalone wheel helpers based on enscons
def add_manifest(archive, dist_info_dir):
    """
    Add the wheel manifest.
    """
    import hashlib
    import zipfile

    lines = []
    for f in archive.namelist():
        data = archive.read(f)
        size = len(data)
        digest = hashlib.sha256(data).digest()
        digest = "sha256=" + (urlsafe_b64encode(digest).decode("ascii"))
        lines.append("%s,%s,%s" % (f.replace(",", ",,"), digest, size))

    record_path = dist_info_dir / "RECORD"
    lines.append(str(record_path) + ",,")
    RECORD = "\n".join(lines)
    archive.writestr(
        zipfile.ZipInfo(str(record_path), time.gmtime(SOURCE_EPOCH_ZIP)[:6]), RECORD
    )
    archive.close()
