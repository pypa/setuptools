from setuptools import metadata as meta
from setuptools.config.pyprojecttoml import read_configuration
from setuptools.dist import Distribution

EXAMPLE = """
[project]
name = "myproj"
keywords = ["some", "key", "words"]
dynamic = ["version", "readme", "license"]
requires-python = ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*"
dependencies = [
    'importlib_metadata>=0.12;python_version<"3.8"',
    'importlib_resources>=1.0;python_version<"3.7"',
    'pathlib2>=2.3.3,<3;python_version < "3.4" and sys.platform != "win32"',
]

[project.optional-dependencies]
docs = [
    "sphinx>=3",
    "sphinx-argparse>=0.2.5",
    "sphinx-rtd-theme>=0.4.3",
]
testing = [
    "pytest>=1",
    "coverage>=3,<5",
]

[project.scripts]
exec = "pkg.__main__:exec"

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}
zip-safe = true
platforms = ["any"]

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true

[tool.setuptools.cmdclass]
sdist = "pkg.mod.CustomSdist"

[tool.setuptools.dynamic]
license = "MIT"

[tool.setuptools.dynamic.version]
attr = "pkg.__version__.VERSION"

[tool.setuptools.dynamic.readme]
file = ["README.md"]
content-type = "text/markdown"

[tool.setuptools.package-data]
"*" = ["*.txt"]

[tool.setuptools.data-files]
"data" = ["files/*.txt"]

[tool.distutils.sdist]
formats = "gztar"

[tool.distutils.bdist_wheel]
universal = true
"""


def _project_files(root_dir):
    pyproject = root_dir / "pyproject.toml"

    files = ["src/pkg/__init__.py", "src/other/nested/__init__.py", "files/file.txt"]
    for file in files:
        (root_dir / file).parent.mkdir(exist_ok=True, parents=True)
        (root_dir / file).touch()

    pyproject.write_text(EXAMPLE)
    (root_dir / "LICENSE.txt").write_text("MIT")
    (root_dir / "README.md").write_text("hello world")
    (root_dir / "src/pkg/mod.py").write_text("class CustomSdist: pass")
    (root_dir / "src/pkg/__version__.py").write_text("VERSION = (3, 10)")
    (root_dir / "src/pkg/__main__.py").write_text("def exec(): print('hello')")


EXPECTED_METADATA = {
    "name": "myproj",
    "version": "3.10",
    "keywords": ["some", "key", "words"],
    "license": "MIT",
    "license_file": ["LICENSE.txt"],
    "description": "hello world",
    "description_content_type": "text/markdown",
    "requires_python": ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    "platform": ["any"],
    "provides_extra": ["docs", "testing"],
    "requires_dist": [
        'importlib_metadata>=0.12;python_version<"3.8"',
        'importlib_resources>=1.0;python_version<"3.7"',
        'pathlib2>=2.3.3,<3;python_version < "3.4" and sys.platform != "win32"',
        "sphinx>=3; extra == 'docs'",
        "sphinx-argparse>=0.2.5; extra == 'docs'",
        "sphinx-rtd-theme>=0.4.3; extra == 'docs'",
        "pytest>=1; extra == 'testing'",
        "coverage>=3,<5; extra == 'testing'",
    ],
}


def test_from_pyproject(tmp_path):
    _project_files(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    metadata = meta.from_pyproject(read_configuration(pyproject), root_dir=tmp_path)
    cmp = meta.compare(metadata, EXPECTED_METADATA)
    if cmp is not True:
        print("cmp:", cmp)
        assert metadata == EXPECTED_METADATA  # just so pytest will print the diff


def test_apply(tmp_path):
    _project_files(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    metadata = meta.from_pyproject(read_configuration(pyproject), root_dir=tmp_path)
    dist = Distribution({})
    meta.apply(metadata, dist)
    internal_meta = dist.metadata
    assert internal_meta.name == EXPECTED_METADATA["name"]
    assert internal_meta.license_files == EXPECTED_METADATA["license_file"]
    assert (
        internal_meta.long_description_content_type
        == EXPECTED_METADATA["description_content_type"]
    )

    reconstructed = meta.from_dist(dist)
    cmp = meta.compare(metadata, reconstructed)
    if cmp is not True:
        print("cmp:", cmp)
        assert metadata == reconstructed  # just so pytest will print the diff
