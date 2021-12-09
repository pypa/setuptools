"""Automatically convert ``setup.cfg`` file into a ``pyproject.toml``-equivalent
in memory data structure, and then proceed to load the configuration.
"""
import os
from typing import Union

from setuptools.errors import FileError
from setuptools.extern.ini2toml.base_translator import BaseTranslator
from setuptools.extern.ini2toml.drivers import configparser as configparser_driver
from setuptools.extern.ini2toml.drivers import plain_builtins as plain_builtins_driver
from setuptools.extern.ini2toml.plugins import setuptools_pep621 as setuptools_plugin

from setuptools.config import pyprojecttoml as pyproject_config


_Path = Union[os.PathLike, str, None]


def convert(setupcfg_file: _Path) -> dict:
    """Convert the ``setup.cfg`` file into a data struct similar to
    the one that would be obtained by parsing a ``pyproject.toml``
    """
    with open(setupcfg_file, "r") as f:
        ini_text = f.read()

    translator = BaseTranslator(
        ini_loads_fn=configparser_driver.parse,
        toml_dumps_fn=plain_builtins_driver.convert,
        plugins=[setuptools_plugin.activate],
        ini_parser_opts={},
    )
    return translator.translate(ini_text, profile_name="setup.cfg")


expand_configuration = pyproject_config.expand_configuration


def read_configuration(
    filepath: _Path, expand: bool = True, ignore_option_errors: bool = False
):
    """Read given configuration file and returns options from it as a dict.

    :param str|unicode filepath: Path to configuration file to get options from.

    :param bool expand: Whether to expand directives and other computed values
        (i.e. post-process the given configuration)

    :param bool ignore_option_errors: Whether to silently ignore
        options, values of which could not be resolved (e.g. due to exceptions
        in directives such as file:, attr:, etc.).
        If False exceptions are propagated as expected.

    :rtype: dict
    """
    filepath = os.path.abspath(filepath)

    if not os.path.isfile(filepath):
        raise FileError(f"Configuration file {filepath!r} does not exist.")

    asdict = convert(filepath)

    with pyproject_config._ignore_errors(ignore_option_errors):
        pyproject_config.validate(asdict)

    if expand:
        root_dir = os.path.dirname(filepath)
        return expand_configuration(asdict, root_dir, ignore_option_errors)
