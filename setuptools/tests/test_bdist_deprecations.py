"""develop tests
"""
import mock
import sys

import pytest

from setuptools.dist import Distribution
from setuptools import SetuptoolsDeprecationWarning


@pytest.mark.skipif(sys.platform == 'win32', reason='non-Windows only')
@mock.patch('distutils.command.bdist_rpm.bdist_rpm.run')
def test_bdist_rpm_warning(distutils_cmd_run, tmpdir_cwd):
    dist = Distribution(
        dict(
            script_name='setup.py',
            script_args=['bdist_rpm'],
            name='foo',
            py_modules=['hi'],
        )
    )
    dist.parse_command_line()
    with pytest.warns(SetuptoolsDeprecationWarning):
        dist.run_commands()

    distutils_cmd_run.assert_called_once()
