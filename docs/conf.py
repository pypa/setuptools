import subprocess
import sys
import os


# hack to run the bootstrap script so that jaraco.packaging.sphinx
# can invoke setup.py
'READTHEDOCS' in os.environ and subprocess.check_call(
    [sys.executable, '-m', 'bootstrap'],
    cwd=os.path.join(os.path.dirname(__file__), os.path.pardir),
)

# -- Project information -----------------------------------------------------

github_url = 'https://github.com'
github_sponsors_url = f'{github_url}/sponsors'

# -- General configuration --

extensions = [
    'sphinx.ext.extlinks',  # allows to create custom roles easily
    'jaraco.packaging.sphinx',
    'rst.linker',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The master toctree document.
master_doc = 'index'

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for extlinks extension ---------------------------------------
extlinks = {
    'user': (f'{github_sponsors_url}/%s', '@'),  # noqa: WPS323
}

# -- Options for HTML output --

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'nature'

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ['_theme']

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    'index': [
        'relations.html', 'sourcelink.html', 'indexsidebar.html',
        'searchbox.html']}

# If false, no module index is generated.
html_use_modindex = False

# If false, no index is generated.
html_use_index = False

# -- Options for LaTeX output --

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author,
# documentclass [howto/manual]).
latex_documents = [(
    'index', 'Setuptools.tex', 'Setuptools Documentation',
    'The fellowship of the packaging', 'manual',
)]

link_files = {
    '../CHANGES.rst': dict(
        using=dict(
            BB='https://bitbucket.org',
            GH='https://github.com',
        ),
        replace=[
            dict(
                pattern=r'(Issue )?#(?P<issue>\d+)',
                url='{package_url}/issues/{issue}',
            ),
            dict(
                pattern=r'BB Pull Request ?#(?P<bb_pull_request>\d+)',
                url='{BB}/pypa/setuptools/pull-request/{bb_pull_request}',
            ),
            dict(
                pattern=r'Distribute #(?P<distribute>\d+)',
                url='{BB}/tarek/distribute/issue/{distribute}',
            ),
            dict(
                pattern=r'Buildout #(?P<buildout>\d+)',
                url='{GH}/buildout/buildout/issues/{buildout}',
            ),
            dict(
                pattern=r'Old Setuptools #(?P<old_setuptools>\d+)',
                url='http://bugs.python.org/setuptools/issue{old_setuptools}',
            ),
            dict(
                pattern=r'Jython #(?P<jython>\d+)',
                url='http://bugs.jython.org/issue{jython}',
            ),
            dict(
                pattern=r'(Python #|bpo-)(?P<python>\d+)',
                url='http://bugs.python.org/issue{python}',
            ),
            dict(
                pattern=r'Interop #(?P<interop>\d+)',
                url='{GH}/pypa/interoperability-peps/issues/{interop}',
            ),
            dict(
                pattern=r'Pip #(?P<pip>\d+)',
                url='{GH}/pypa/pip/issues/{pip}',
            ),
            dict(
                pattern=r'Packaging #(?P<packaging>\d+)',
                url='{GH}/pypa/packaging/issues/{packaging}',
            ),
            dict(
                pattern=r'[Pp]ackaging (?P<packaging_ver>\d+(\.\d+)+)',
                url='{GH}/pypa/packaging/blob/{packaging_ver}/CHANGELOG.rst',
            ),
            dict(
                pattern=r'PEP[- ](?P<pep_number>\d+)',
                url='https://www.python.org/dev/peps/pep-{pep_number:0>4}/',
            ),
            dict(
                pattern=r'setuptools_svn #(?P<setuptools_svn>\d+)',
                url='{GH}/jaraco/setuptools_svn/issues/{setuptools_svn}',
            ),
            dict(
                pattern=r'pypa/distutils#(?P<distutils>\d+)',
                url='{GH}/pypa/distutils/issues/{distutils}',
            ),
            dict(
                pattern=r'^(?m)((?P<scm_version>v?\d+(\.\d+){1,2}))\n[-=]+\n',
                with_scm='{text}\n{rev[timestamp]:%d %b %Y}\n',
            ),
        ],
    ),
}


# Be strict about any broken references:
nitpicky = True


# Ref: https://github.com/python-attrs/attrs/pull/571/files\
#      #diff-85987f48f1258d9ee486e3191495582dR82
default_role = 'any'
