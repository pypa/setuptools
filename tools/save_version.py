__requires__ = ['setuptools_scm>=8']

from pathlib import Path
from setuptools_scm import get_version


def save_version():
    version = f"v{get_version()}"  # add v -> compatible with jaraco.develop.towncrier
    Path(".latest").write_text(version, encoding="utf-8")
    return version


__name__ == '__main__' and print(save_version())
