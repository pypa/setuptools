import mock
from distutils import log

import pytest

from setuptools.command.register import register
from setuptools.dist import Distribution


class TestRegisterTest:
    def test_warns_deprecation(self):
        dist = Distribution()

        cmd = register(dist)
        cmd.run_command = mock.Mock()
        cmd.send_metadata = mock.Mock()
        cmd.announce = mock.Mock()

        cmd.run()

        cmd.announce.assert_called_with(
            "WARNING: Registering is deprecated, use twine to upload instead "
            "(https://pypi.org/p/twine/)",
            log.WARN
        )

    def test_warns_deprecation_when_raising(self):
        dist = Distribution()

        cmd = register(dist)
        cmd.run_command = mock.Mock()
        cmd.send_metadata = mock.Mock()
        cmd.send_metadata.side_effect = Exception
        cmd.announce = mock.Mock()

        with pytest.raises(Exception):
            cmd.run()

        cmd.announce.assert_called_with(
            "WARNING: Registering is deprecated, use twine to upload instead "
            "(https://pypi.org/p/twine/)",
            log.WARN
        )
