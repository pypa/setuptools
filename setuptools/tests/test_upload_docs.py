import os
import zipfile
import contextlib

import pytest
from jaraco import path

from setuptools.command.upload_docs import upload_docs
from setuptools.dist import Distribution

from .textwrap import DALS
from . import contexts


@pytest.fixture
def sample_project(tmpdir_cwd):
    path.build({
        'setup.py': DALS("""
            from setuptools import setup

            setup(name='foo')
            """),
        'build': {
            'index.html': 'Hello world.',
            'empty': {},
        }
    })


@pytest.mark.usefixtures('sample_project')
@pytest.mark.usefixtures('user_override')
class TestUploadDocsTest:
    def test_create_zipfile(self):
        """
        Ensure zipfile creation handles common cases, including a folder
        containing an empty folder.
        """

        dist = Distribution()

        cmd = upload_docs(dist)
        cmd.target_dir = cmd.upload_dir = 'build'
        with contexts.tempdir() as tmp_dir:
            tmp_file = os.path.join(tmp_dir, 'foo.zip')
            zip_file = cmd.create_zipfile(tmp_file)

            assert zipfile.is_zipfile(tmp_file)

            with contextlib.closing(zipfile.ZipFile(tmp_file)) as zip_file:
                assert zip_file.namelist() == ['index.html']

    def test_build_multipart(self):
        data = dict(
            a="foo",
            b="bar",
            file=('file.txt', b'content'),
        )
        body, content_type = upload_docs._build_multipart(data)
        assert 'form-data' in content_type
        assert "b'" not in content_type
        assert 'b"' not in content_type
        assert isinstance(body, bytes)
        assert b'foo' in body
        assert b'content' in body
