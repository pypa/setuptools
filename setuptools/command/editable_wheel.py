"""
Create a wheel that, when installed, will make the source package 'editable'
(add it to the interpreter's path, including metadata) per PEP 660. Replaces
'setup.py develop'. Based on the setuptools develop command.
"""

import os
import shutil
import sys
from distutils.core import Command
from pathlib import Path
from tempfile import TemporaryDirectory


class editable_wheel(Command):
    """Build 'editable' wheel for development"""

    description = "create a PEP 660 'editable' wheel"

    user_options = [
        ("dist-dir=", "d", "directory to put final built distributions in"),
        ("dist-info-dir=", "I", "path to a pre-build .dist-info directory"),
    ]

    boolean_options = ["strict"]

    def initialize_options(self):
        self.dist_dir = None
        self.dist_info_dir = None
        self.project_dir = None
        self.strict = False

    def finalize_options(self):
        dist = self.distribution
        self.project_dir = dist.src_root or os.curdir
        self.dist_dir = Path(self.dist_dir or os.path.join(self.project_dir, "dist"))
        self.dist_dir.mkdir(exist_ok=True)

    @property
    def target(self):
        package_dir = self.distribution.package_dir or {}
        return package_dir.get("") or self.project_dir

    def run(self):
        self._ensure_dist_info()

        # Add missing dist_info files
        bdist_wheel = self.reinitialize_command("bdist_wheel")
        bdist_wheel.write_wheelfile(self.dist_info_dir)

        # Build extensions in-place
        self.reinitialize_command("build_ext", inplace=1)
        self.run_command("build_ext")

        self._create_wheel_file(bdist_wheel)

    def _ensure_dist_info(self):
        if self.dist_info_dir is None:
            dist_info = self.reinitialize_command("dist_info")
            dist_info.output_dir = self.dist_dir
            dist_info.finalize_options()
            dist_info.run()
            self.dist_info_dir = dist_info.dist_info_dir
        else:
            assert str(self.dist_info_dir).endswith(".dist-info")
            assert Path(self.dist_info_dir, "METADATA").exists()

    def _create_wheel_file(self, bdist_wheel):
        from wheel.wheelfile import WheelFile

        dist_info = self.get_finalized_command("dist_info")
        tag = "-".join(bdist_wheel.get_tag())
        editable_name = dist_info.name
        build_tag = "0.editable"  # According to PEP 427 needs to start with digit
        archive_name = f"{editable_name}-{build_tag}-{tag}.whl"
        wheel_path = Path(self.dist_dir, archive_name)
        if wheel_path.exists():
            wheel_path.unlink()

        # Currently the wheel API receives a directory and dump all its contents
        # inside of a wheel. So let's use a temporary directory.
        with TemporaryDirectory(suffix=archive_name) as tmp:
            tmp_dist_info = Path(tmp, Path(self.dist_info_dir).name)
            shutil.copytree(self.dist_info_dir, tmp_dist_info)
            self._populate_wheel(editable_name, tmp)
            with WheelFile(wheel_path, "w") as wf:
                wf.write_files(tmp)

        return wheel_path


    def _best_strategy(self):
        if self.strict:
            return self._link_tree

        dist = self.distribution
        if set(dist.packages) == {""}:
            # src-layout(ish) package detected. These kind of packages are relatively
            # safe so we can simply add the src directory to the pth file.
            return self._top_level_pth

        if self._can_symlink():
            return self._top_level_symlinks

    # >>> def _targets(self):
    # >>>     build_py.find_modules()
    # >>>     self.dist.packages

    def _populate_wheel(self, dist_id, unpacked_wheel_dir):
        pth = Path(unpacked_wheel_dir, f"_editable.{dist_id}.pth")
        pth.write_text(f"{_normalize_path(self.target)}\n", encoding="utf-8")


def _normalize_path(filename):
    """Normalize a file/dir name for comparison purposes"""
    # See pkg_resources.normalize_path
    file = os.path.abspath(filename) if sys.platform == 'cygwin' else filename
    return os.path.normcase(os.path.realpath(os.path.normpath(file)))
