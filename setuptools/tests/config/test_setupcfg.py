from textwrap import dedent

from setuptools.config.setupcfg import convert, read_configuration

EXAMPLE = {
    "LICENSE": "----- MIT LICENSE TEXT PLACEHOLDER ----",
    "README.md": "hello world",
    "pyproject.toml": dedent("""\
        [build-system]
        requires = ["setuptools>=42", "wheel"]
        build-backend = "setuptools.build_meta"
    """),
    "setup.cfg": dedent("""\
        [metadata]
        name = example-pkg
        version = 0.0.1
        author = Example Author
        author_email = author@example.com
        description = A small example package
        long_description = file: README.md
        long_description_content_type = text/markdown
        url = https://github.com/pypa/sampleproject
        project_urls =
            Bug Tracker = https://github.com/pypa/sampleproject/issues
        classifiers =
            Programming Language :: Python :: 3
            License :: OSI Approved :: MIT License
            Operating System :: OS Independent

        [options]
        package_dir =
            = src
        packages = find:
        python_requires = >=3.6
        install_requires =
            peppercorn
        entry_points = file: entry_points.ini

        [options.extras_require]
        dev =
            check-manifest
        test =
            coverage

        [options.packages.find]
        where = src
    """),
    "entry_points.ini": dedent("""\
        [my.plugin.group]
        add_one = example_package.example:add_one
    """),
    "src/example_package/__init__.py": "",
    "src/example_package/example.py": "def add_one(number):\n    return number + 1",
    "src/example_package/package_data.csv": "42",
    "src/example_package/nested/__init__.py": "",
}


def create_project(parent_dir, files):
    for file, content in files.items():
        path = parent_dir / file
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(content)


def test_convert(tmp_path):
    create_project(tmp_path, EXAMPLE)
    pyproject = convert(tmp_path / "setup.cfg")
    project = pyproject["project"]
    assert project["name"] == "example-pkg"
    assert project["version"] == "0.0.1"
    assert project["readme"]["file"] == "README.md"
    assert project["readme"]["content-type"] == "text/markdown"
    assert project["urls"]["Homepage"] == "https://github.com/pypa/sampleproject"
    assert set(project["dependencies"]) == {"peppercorn"}
    assert set(project["optional-dependencies"]["dev"]) == {"check-manifest"}
    assert set(project["optional-dependencies"]["test"]) == {"coverage"}
    setuptools = pyproject["tool"]["setuptools"]
    from pprint import pprint
    pprint(setuptools)
    assert set(setuptools["dynamic"]["entry-points"]["file"]) == {"entry_points.ini"}
    assert setuptools["packages"]["find"]["where"] == ["src"]
    assert setuptools["packages"]["find"]["namespaces"] is False


def test_read_configuration(tmp_path):
    create_project(tmp_path, EXAMPLE)
    pyproject = read_configuration(tmp_path / "setup.cfg")
    project = pyproject["project"]
    ep_value = "example_package.example:add_one"
    assert project["entry-points"]["my.plugin.group"]["add_one"] == ep_value
    setuptools = pyproject["tool"]["setuptools"]
    assert set(setuptools["packages"]) == {"example_package", "example_package.nested"}
