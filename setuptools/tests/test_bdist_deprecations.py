"""develop tests
"""
import mock

import pytest

from setuptools.dist import Distribution
from setuptools import SetuptoolsDeprecationWarning


@mock.patch("distutils.command.bdist_wininst.bdist_wininst")
def test_bdist_wininst_warning(distutils_cmd):
    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['bdist_wininst'],
        name='foo',
        py_modules=['hi'],
    ))
    dist.parse_command_line()
    with pytest.warns(SetuptoolsDeprecationWarning):
        dist.run_commands()

    distutils_cmd.run.assert_called_once()
