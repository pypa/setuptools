"""
Create a dist_info directory
As defined in the wheel specification
"""

import os
import re
import warnings
from inspect import cleandoc
from pathlib import Path

from distutils.core import Command
from distutils import log
from setuptools.extern import packaging
from setuptools._deprecation_warning import SetuptoolsDeprecationWarning


class dist_info(Command):

    description = 'create a .dist-info directory'

    user_options = [
        ('egg-base=', 'e', "directory containing .egg-info directories"
                           " (default: top of the source tree)"
                           " DEPRECATED: use --output-dir."),
        ('output-dir=', 'o', "directory inside of which the .dist-info will be"
                             "created (default: top of the source tree)"),
    ]

    def initialize_options(self):
        self.egg_base = None
        self.output_dir = None
        self.name = None
        self.dist_info_dir = None

    def finalize_options(self):
        if self.egg_base:
            msg = "--egg-base is deprecated for dist_info command. Use --output-dir."
            warnings.warn(msg, SetuptoolsDeprecationWarning)
            self.output_dir = self.egg_base or self.output_dir

        dist = self.distribution
        project_dir = dist.src_root or os.curdir
        self.output_dir = Path(self.output_dir or project_dir)

        egg_info = self.reinitialize_command('egg_info')
        egg_info.egg_base = str(self.output_dir)
        egg_info.finalize_options()
        self.egg_info = egg_info

        name = _safe(dist.get_name())
        version = _version(dist.get_version())
        self.name = f"{name}-{version}"
        self.dist_info_dir = os.path.join(self.output_dir, f"{self.name}.dist-info")

    def run(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.egg_info.run()
        egg_info_dir = self.egg_info.egg_info
        log.info("creating '{}'".format(os.path.abspath(self.dist_info_dir)))
        bdist_wheel = self.get_finalized_command('bdist_wheel')
        bdist_wheel.egg2dist(egg_info_dir, self.dist_info_dir)
        assert os.path.exists(egg_info_dir) is False


def _safe(component: str) -> str:
    """Escape a component used to form a wheel name according to PEP 491"""
    return re.sub(r"[^\w\d.]+", "_", component)


def _version(version: str) -> str:
    """Convert an arbitrary string to a version string."""
    v = version.replace(' ', '.')
    try:
        return str(packaging.version.Version(v)).replace("-", "_")
    except packaging.version.InvalidVersion:
        msg = f"""Invalid version: {version!r}.
        !!\n\n
        ###################
        # Invalid version #
        ###################
        {version!r} is not valid according to PEP 440.\n
        Please make sure specify a valid version for your package.
        Also note that future releases of setuptools may halt the build process
        if an invalid version is given.
        \n\n!!
        """
        warnings.warn(cleandoc(msg))
        return _safe(v).strip("_")
