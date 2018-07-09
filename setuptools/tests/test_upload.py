import mock
from distutils import log

import pytest

from setuptools.command.upload import upload
from setuptools.dist import Distribution


class TestUploadTest:
    def test_warns_deprecation(self):
        dist = Distribution()
        dist.dist_files = [(mock.Mock(), mock.Mock(), mock.Mock())]

        cmd = upload(dist)
        cmd.upload_file = mock.Mock()
        cmd.announce = mock.Mock()

        cmd.run()

        cmd.announce.assert_called_once_with(
            "WARNING: Uploading via this command is deprecated, use twine to "
            "upload instead (https://pypi.org/p/twine/)",
            log.WARN
        )

    def test_warns_deprecation_when_raising(self):
        dist = Distribution()
        dist.dist_files = [(mock.Mock(), mock.Mock(), mock.Mock())]

        cmd = upload(dist)
        cmd.upload_file = mock.Mock()
        cmd.upload_file.side_effect = Exception
        cmd.announce = mock.Mock()

        with pytest.raises(Exception):
            cmd.run()

        cmd.announce.assert_called_once_with(
            "WARNING: Uploading via this command is deprecated, use twine to "
            "upload instead (https://pypi.org/p/twine/)",
            log.WARN
        )
