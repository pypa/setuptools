import mock
import os
import re

from distutils import log
from distutils.version import StrictVersion

import pytest
import six

from setuptools.command.upload import upload
from setuptools.dist import Distribution


def _parse_upload_body(body):
    boundary = '\r\n----------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
    entries = []
    name_re = re.compile('^Content-Disposition: form-data; name="([^\"]+)"')

    for entry in body.split(boundary):
        pair = entry.split('\r\n\r\n')
        if not len(pair) == 2:
            continue

        key, value = map(str.strip, pair)
        m = name_re.match(key)
        if m is not None:
            key = m.group(1)

        entries.append((key, value))

    return entries


class TestUploadTest:
    @pytest.mark.xfail(reason='Issue #1381')
    @mock.patch('setuptools.command.upload.urlopen')
    def test_upload_metadata(self, patch, tmpdir):
        dist = Distribution()
        dist.metadata.metadata_version = StrictVersion('2.1')

        content = os.path.join(str(tmpdir), "test_upload_metadata_content")

        with open(content, 'w') as f:
            f.write("Some content")

        dist.dist_files = [('xxx', '3.7', content)]

        patch.return_value = mock.Mock()
        patch.return_value.getcode.return_value = 200

        cmd = upload(dist)
        cmd.announce = mock.Mock()
        cmd.password = 'hunter2'
        cmd.ensure_finalized()
        cmd.run()

        # Make sure we did the upload
        patch.assert_called_once()

        # Make sure the metadata version is correct in the headers
        request = patch.call_args_list[0][0][0]
        body = request.data.decode('utf-8')

        entries = dict(_parse_upload_body(body))
        assert entries['metadata_version'] == '2.1'


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
