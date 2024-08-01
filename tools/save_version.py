from pathlib import Path
from setuptools_scm import get_version


def save_version():
    version = get_version()
    Path(".version").write_text(version, encoding="utf-8")
    return version


__name__ == '__main__' and print(save_version())
