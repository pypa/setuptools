import pytest

from jaraco import path

from setuptools.command.upload_docs import upload_docs
from setuptools.dist import Distribution


@pytest.fixture
def sphinx_doc_sample_project(tmpdir_cwd):
    path.build({
        'setup.py': 'from setuptools import setup; setup()',
        'build': {
            'docs': {
                'conf.py': 'project="test"',
                'index.rst': ".. toctree::\
                    :maxdepth: 2\
                    :caption: Contents:",
            },
        },
    })


@pytest.mark.usefixtures('sphinx_doc_sample_project')
class TestSphinxUploadDocs:
    def test_sphinx_doc(self):
        params = dict(
            name='foo',
            packages=['test'],
        )
        dist = Distribution(params)

        cmd = upload_docs(dist)

        cmd.initialize_options()
        assert cmd.upload_dir is None
        assert cmd.has_sphinx() is True
        cmd.finalize_options()
