from __future__ import annotations

import os

from .._path import StrPath
from ..dist import Distribution

import distutils.command.install_lib as orig


class install_lib(orig.install_lib):
    """Don't add compiled flags to filenames of non-Python files"""

    distribution: Distribution  # override distutils.dist.Distribution with setuptools.dist.Distribution

    def run(self) -> None:
        self.build()
        outfiles = self.install()
        if outfiles is not None:
            # always compile, in case we have any extension stubs to deal with
            self.byte_compile(outfiles)

    def get_exclusions(self):
        return set()

    def copy_tree(
        self,
        infile: StrPath,
        outfile: str,
        # override: Using actual booleans
        preserve_mode: bool = True,  # type: ignore[override]
        preserve_times: bool = True,  # type: ignore[override]
        preserve_symlinks: bool = False,  # type: ignore[override]
        level: object = 1,
    ) -> list[str]:
        assert preserve_mode
        assert preserve_times
        assert not preserve_symlinks
        exclude = self.get_exclusions()

        if not exclude:
            return orig.install_lib.copy_tree(self, infile, outfile)

        # Exclude namespace package __init__.py* files from the output

        from setuptools.archive_util import unpack_directory

        from distutils import log

        outfiles: list[str] = []

        def pf(src: str, dst: str):
            if dst in exclude:
                log.warn("Skipping installation of %s (namespace package)", dst)
                return False

            log.info("copying %s -> %s", src, os.path.dirname(dst))
            outfiles.append(dst)
            return dst

        unpack_directory(infile, outfile, pf)
        return outfiles

    def get_outputs(self):
        outputs = orig.install_lib.get_outputs(self)
        exclude = self.get_exclusions()
        if exclude:
            return [f for f in outputs if f not in exclude]
        return outputs
