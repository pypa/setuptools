import pytest

from setuptools.config.pyprojecttoml import apply_configuration
from setuptools.dist import Distribution
from setuptools.tests.textwrap import DALS


def test_dynamic_dependencies(tmp_path):
    (tmp_path / "requirements.txt").write_text("six\n  # comment\n")
    pyproject = (tmp_path / "pyproject.toml")
    pyproject.write_text(DALS("""
    [project]
    name = "myproj"
    version = "1.0"
    dynamic = ["dependencies"]

    [build-system]
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta"

    [tool.setuptools.dynamic.dependencies]
    file = ["requirements.txt"]
    """))
    dist = Distribution()
    dist = apply_configuration(dist, pyproject)
    assert dist.install_requires == ["six"]


def test_dynamic_optional_dependencies(tmp_path):
    (tmp_path / "requirements-docs.txt").write_text("sphinx\n  # comment\n")
    pyproject = (tmp_path / "pyproject.toml")
    pyproject.write_text(DALS("""
    [project]
    name = "myproj"
    version = "1.0"
    dynamic = ["optional-dependencies"]

    [tool.setuptools.dynamic.optional-dependencies.docs]
    file = ["requirements-docs.txt"]

    [build-system]
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta"
    """))
    dist = Distribution()
    dist = apply_configuration(dist, pyproject)
    assert dist.extras_require == {"docs": ["sphinx"]}


def test_mixed_dynamic_optional_dependencies(tmp_path):
    """
    Test that if PEP 621 was loosened to allow mixing of dynamic and static
    configurations in the case of fields containing sub-fields (groups),
    things would work out.
    """
    (tmp_path / "requirements-images.txt").write_text("pillow~=42.0\n  # comment\n")
    pyproject = (tmp_path / "pyproject.toml")
    pyproject.write_text(DALS("""
    [project]
    name = "myproj"
    version = "1.0"
    dynamic = ["optional-dependencies"]

    [project.optional-dependencies]
    docs = ["sphinx"]

    [tool.setuptools.dynamic.optional-dependencies.images]
    file = ["requirements-images.txt"]

    [build-system]
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta"
    """))
    # Test that the mix-and-match doesn't currently validate.
    with pytest.raises(ValueError, match="project.optional-dependencies"):
        apply_configuration(Distribution(), pyproject)

    # Explicitly disable the validation and try again, to see that the mix-and-match
    # result would be correct.
    dist = Distribution()
    dist = apply_configuration(dist, pyproject, ignore_option_errors=True)
    assert dist.extras_require == {"docs": ["sphinx"], "images": ["pillow~=42.0"]}
