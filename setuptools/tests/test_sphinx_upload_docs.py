import pytest
import os

from setuptools.command.upload_docs import upload_docs
from setuptools.dist import Distribution


@pytest.fixture
def sphinx_doc_sample_project(tmpdir_cwd):
    # setup.py
    with open('setup.py', 'wt') as f:
        f.write('from setuptools import setup; setup()\n')

    os.makedirs('build/docs')

    # A test conf.py for Sphinx
    with open('build/docs/conf.py', 'w') as f:
        f.write("project = 'test'")

    # A test index.rst for Sphinx
    with open('build/docs/index.rst', 'w') as f:
        f.write(".. toctree::\
                    :maxdepth: 2\
                    :caption: Contents:")


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
