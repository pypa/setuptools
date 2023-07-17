import inspect
import logging
import os

import pytest


setup_py = """\
from setuptools import setup

setup(
    name="test_logging",
    version="0.0"
)
"""


@pytest.mark.parametrize(
    "flag, expected_level", [("--dry-run", "INFO"), ("--verbose", "DEBUG")]
)
def test_verbosity_level(tmp_path, monkeypatch, flag, expected_level):
    """Make sure the correct verbosity level is set (issue #3038)"""
    import setuptools  # noqa: F401  # import setuptools to monkeypatch distutils
    import distutils  # <- load distutils after all the patches take place

    logger = logging.Logger(__name__)
    monkeypatch.setattr(logging, "root", logger)
    unset_log_level = logger.getEffectiveLevel()
    assert logging.getLevelName(unset_log_level) == "NOTSET"

    setup_script = tmp_path / "setup.py"
    setup_script.write_text(setup_py)
    dist = distutils.core.run_setup(setup_script, stop_after="init")
    dist.script_args = [flag, "sdist"]
    dist.parse_command_line()  # <- where the log level is set
    log_level = logger.getEffectiveLevel()
    log_level_name = logging.getLevelName(log_level)
    assert log_level_name == expected_level


def test_patching_does_not_cause_problems():
    # Ensure `dist.log` is only patched if necessary

    import setuptools.logging
    from distutils import dist

    setuptools.logging.configure()

    if os.getenv("SETUPTOOLS_USE_DISTUTILS", "local").lower() == "local":
        # Modern logging infra, no problematic patching.
        assert isinstance(dist.log, logging.Logger)
    else:
        assert inspect.ismodule(dist.log)
