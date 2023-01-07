extensions = [
    'sphinx.ext.autodoc',
    'jaraco.packaging.sphinx',
]

master_doc = "index"
html_theme = "furo"

# Link dates and other references in the changelog
extensions += ['rst.linker']
link_files = {
    '../CHANGES.rst': dict(
        using=dict(
            BB='https://bitbucket.org',
            GH='https://github.com',
        ),
        replace=[
            dict(
                pattern=r'(Issue #|\B#)(?P<issue>\d+)',
                url='{package_url}/issues/{issue}',
            ),
            dict(
                pattern=r'(?m:^((?P<scm_version>v?\d+(\.\d+){1,2}))\n[-=]+\n)',
                with_scm='{text}\n{rev[timestamp]:%d %b %Y}\n',
            ),
            dict(
                pattern=r'PEP[- ](?P<pep_number>\d+)',
                url='https://peps.python.org/pep-{pep_number:0>4}/',
            ),
            dict(
                pattern=r'(?<!\w)PR #(?P<pull>\d+)',
                url='{package_url}/pull/{pull}',
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
                pattern=r'setuptools_svn #(?P<setuptools_svn>\d+)',
                url='{GH}/jaraco/setuptools_svn/issues/{setuptools_svn}',
            ),
            dict(
                pattern=r'pypa/(?P<issue_repo>[\-\.\w]+)#(?P<issue_number>\d+)',
                url='{GH}/pypa/{issue_repo}/issues/{issue_number}',
            ),
            dict(
                pattern=r'pypa/(?P<commit_repo>[\-\.\w]+)@(?P<commit_number>[\da-f]+)',
                url='{GH}/pypa/{commit_repo}/commit/{commit_number}',
            ),
        ],
    ),
}

# Be strict about any broken references
nitpicky = True

# Include Python intersphinx mapping to prevent failures
# jaraco/skeleton#51
extensions += ['sphinx.ext.intersphinx']
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Preserve authored syntax for defaults
autodoc_preserve_defaults = True

intersphinx_mapping.update({
    'pip': ('https://pip.pypa.io/en/latest', None),
    'build': ('https://pypa-build.readthedocs.io/en/latest', None),
    'PyPUG': ('https://packaging.python.org/en/latest/', None),
    'packaging': ('https://packaging.pypa.io/en/latest/', None),
    'twine': ('https://twine.readthedocs.io/en/stable/', None),
    'importlib-resources': (
        'https://importlib-resources.readthedocs.io/en/latest', None
    ),
})

# Support tooltips on references
extensions += ['hoverxref.extension']
hoverxref_auto_ref = True
hoverxref_intersphinx = [
    'python',
    'pip',
    'build',
    'PyPUG',
    'packaging',
    'twine',
    'importlib-resources',
]

# Add support for linking usernames
github_url = 'https://github.com'
github_repo_org = 'pypa'
github_repo_name = 'setuptools'
github_repo_slug = f'{github_repo_org}/{github_repo_name}'
github_repo_url = f'{github_url}/{github_repo_slug}'
github_sponsors_url = f'{github_url}/sponsors'
extlinks = {
    'user': (f'{github_sponsors_url}/%s', '@%s'),  # noqa: WPS323
    'pypi': ('https://pypi.org/project/%s', '%s'),  # noqa: WPS323
    'wiki': ('https://wikipedia.org/wiki/%s', '%s'),  # noqa: WPS323
}
extensions += ['sphinx.ext.extlinks']

# Ref: https://github.com/python-attrs/attrs/pull/571/files\
#      #diff-85987f48f1258d9ee486e3191495582dR82
default_role = 'any'

# HTML theme
html_theme = 'furo'
html_logo = "images/logo.svg"

html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#336790",  # "blue"
        "color-brand-content": "#336790",
    },
    "dark_css_variables": {
        "color-brand-primary": "#E5B62F",  # "yellow"
        "color-brand-content": "#E5B62F",
    },
}

# Redirect old docs so links and references in the ecosystem don't break
extensions += ['sphinx_reredirects']
redirects = {
    "userguide/keywords": "/deprecated/changed_keywords.html",
    "userguide/commands": "/deprecated/commands.html",
}

# Add support for inline tabs
extensions += ['sphinx_inline_tabs']

# Support for distutils

# Ref: https://stackoverflow.com/a/30624034/595220
nitpick_ignore = [
    ('c:func', 'SHGetSpecialFolderPath'),  # ref to MS docs
    ('envvar', 'DISTUTILS_DEBUG'),  # undocumented
    ('envvar', 'HOME'),  # undocumented
    ('envvar', 'PLAT'),  # undocumented
    ('envvar', 'DIST_EXTRA_CONFIG'),  # undocumented
    ('py:attr', 'CCompiler.language_map'),  # undocumented
    ('py:attr', 'CCompiler.language_order'),  # undocumented
    ('py:class', 'distutils.dist.Distribution'),  # undocumented
    ('py:class', 'distutils.extension.Extension'),  # undocumented
    ('py:class', 'BorlandCCompiler'),  # undocumented
    ('py:class', 'CCompiler'),  # undocumented
    ('py:class', 'CygwinCCompiler'),  # undocumented
    ('py:class', 'distutils.dist.DistributionMetadata'),  # undocumented
    ('py:class', 'FileList'),  # undocumented
    ('py:class', 'IShellLink'),  # ref to MS docs
    ('py:class', 'MSVCCompiler'),  # undocumented
    ('py:class', 'OptionDummy'),  # undocumented
    ('py:class', 'UnixCCompiler'),  # undocumented
    ('py:exc', 'CompileError'),  # undocumented
    ('py:exc', 'DistutilsExecError'),  # undocumented
    ('py:exc', 'DistutilsFileError'),  # undocumented
    ('py:exc', 'LibError'),  # undocumented
    ('py:exc', 'LinkError'),  # undocumented
    ('py:exc', 'PreprocessError'),  # undocumented
    ('py:exc', 'setuptools.errors.PlatformError'),  # sphinx cannot find it
    ('py:func', 'distutils.CCompiler.new_compiler'),  # undocumented
    # undocumented:
    ('py:func', 'distutils.dist.DistributionMetadata.read_pkg_file'),
    ('py:func', 'distutils.file_util._copy_file_contents'),  # undocumented
    ('py:func', 'distutils.log.debug'),  # undocumented
    ('py:func', 'distutils.spawn.find_executable'),  # undocumented
    ('py:func', 'distutils.spawn.spawn'),  # undocumented
    # TODO: check https://docutils.rtfd.io in the future
    ('py:mod', 'docutils'),  # there's no Sphinx site documenting this
]

# Allow linking objects on other Sphinx sites seamlessly:
intersphinx_mapping.update(
    python=('https://docs.python.org/3', None),
)

# Add support for the unreleased "next-version" change notes
extensions += ['sphinxcontrib.towncrier']
# Extension needs a path from here to the towncrier config.
towncrier_draft_working_directory = '..'
# Avoid an empty section for unpublished changes.
towncrier_draft_include_empty = False

extensions += ['jaraco.tidelift']

# Add icons (aka "favicons") to documentation
extensions += ['sphinx-favicon']
html_static_path = ['images']  # should contain the folder with icons

# Add support for nice Not Found 404 pages
extensions += ['notfound.extension']

# List of dicts with <link> HTML attributes
# static-file points to files in the html_static_path (href is computed)
favicons = [
    {  # "Catch-all" goes first, otherwise some browsers will overwrite
        "rel": "icon",
        "type": "image/svg+xml",
        "static-file": "logo-symbol-only.svg",
        "sizes": "any"
    },
    {  # Version with thicker strokes for better visibility at smaller sizes
        "rel": "icon",
        "type": "image/svg+xml",
        "static-file": "favicon.svg",
        "sizes": "16x16 24x24 32x32 48x48"
    },
    # rel="apple-touch-icon" does not support SVG yet
]
