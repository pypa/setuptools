"""
Create a dist_info directory
As defined in the wheel specification
"""

import os
import shutil
from distutils import log
from distutils.core import Command
from distutils import dir_util  # prefer dir_util for log/cache consistency
from pathlib import Path

from .. import _normalization
from ..warnings import SetuptoolsDeprecationWarning


_IGNORE = {
    "PKG-INFO",
    "requires.txt",
    "SOURCES.txt",
    "not-zip-safe",
    "dependency_links.txt",
}
# Files to be ignored when copying the egg-info into dist-info


class dist_info(Command):
    """
    This command is private and reserved for internal use of setuptools,
    users should rely on ``setuptools.build_meta`` APIs.
    """

    description = "DO NOT CALL DIRECTLY, INTERNAL ONLY: create .dist-info directory"

    user_options = [
        (
            'egg-base=',
            'e',
            "directory containing .egg-info directories"
            " (default: top of the source tree)"
            " DEPRECATED: use --output-dir.",
        ),
        (
            'output-dir=',
            'o',
            "directory inside of which the .dist-info will be"
            "created (default: top of the source tree)",
        ),
        ('tag-date', 'd', "Add date stamp (e.g. 20050528) to version number"),
        ('tag-build=', 'b', "Specify explicit tag to add to version number"),
        ('no-date', 'D', "Don't include date stamp [default]"),
        ('keep-egg-info', None, "*TRANSITIONAL* will be removed in the future"),
        ('use-cached', None, "*TRANSITIONAL* will be removed in the future"),
    ]

    boolean_options = ['tag-date', 'keep-egg-info', 'use-cached']
    negative_opt = {'no-date': 'tag-date'}

    def initialize_options(self):
        self.egg_base = None
        self.output_dir = None
        self.name = None
        self.dist_info_dir = None
        self.tag_date = None
        self.tag_build = None
        self.keep_egg_info = False
        self.use_cached = False

    def finalize_options(self):
        if self.egg_base:
            msg = "--egg-base is deprecated for dist_info command. Use --output-dir."
            SetuptoolsDeprecationWarning.emit(msg, due_date=(2023, 9, 26))
            # This command is internal to setuptools, therefore it should be safe
            # to remove the deprecated support soon.
            self.output_dir = self.egg_base or self.output_dir

        dist = self.distribution
        project_dir = dist.src_root or os.curdir
        self.output_dir = Path(self.output_dir or project_dir)

        egg_info = self.reinitialize_command("egg_info", reinit_subcommands=True)
        egg_info.egg_base = str(self.output_dir)
        self._sync_tag_details(egg_info)
        egg_info.finalize_options()
        self.egg_info = egg_info

        name = _normalization.safer_name(dist.get_name())
        version = _normalization.safer_best_effort_version(dist.get_version())
        self.name = f"{name}-{version}"
        self.dist_info_dir = Path(self.output_dir, f"{self.name}.dist-info")

    def _sync_tag_details(self, egg_info):
        if self.tag_date:
            egg_info.tag_date = self.tag_date
        else:
            self.tag_date = egg_info.tag_date

        if self.tag_build:
            egg_info.tag_build = self.tag_build
        else:
            self.tag_build = egg_info.tag_build

    def run(self):
        if self.use_cached and (self.dist_info_dir / "METADATA").is_file():
            return

        self.mkpath(str(self.output_dir))
        self.egg_info.run()
        egg_info_dir = Path(self.egg_info.egg_info)
        dist_info_dir = self.dist_info_dir

        assert egg_info_dir.is_dir(), ".egg-info dir should have been created"
        log.info(f"creating {str(os.path.abspath(dist_info_dir))!r}")

        # The egg-info dir should now be basically equivalent to the dist-info dir
        # If in the future we don't want to use egg_info, we have to create the files:
        # METADATA, entry-points.txt
        shutil.copytree(egg_info_dir, dist_info_dir, ignore=lambda _, __: _IGNORE)
        metadata_file = dist_info_dir / "METADATA"
        self.copy_file(egg_info_dir / "PKG-INFO", metadata_file)
        if self.distribution.dependency_links:
            self.copy_file(egg_info_dir / "dependency_links.txt", dist_info_dir)

        for dest, orig in self._license_paths():
            dest = dist_info_dir / dest
            self.mkpath(str(dest.parent))
            self.copy_file(orig, dest)

        if not self.keep_egg_info:
            dir_util.remove_tree(egg_info_dir, self.verbose, self.dry_run)

    def _license_paths(self):
        for file in self.distribution.metadata.license_files or ():
            yield os.path.basename(file), file
