from __future__ import annotations

from setuptools import setup

setup(
    name="complex-dist",
    version="0.1",
    description="Another testing distribution \N{SNOWMAN}",
    long_description="Another testing distribution \N{SNOWMAN}",
    author="Illustrious Author",
    author_email="illustrious@example.org",
    url="http://example.org/exemplary",
    packages=["complexdist"],
    setup_requires=["wheel", "setuptools"],
    install_requires=["quux", "splort"],
    extras_require={"simple": ["simple.dist"]},
    tests_require=["foo", "bar>=10.0.0"],
    entry_points={
        "console_scripts": [
            "complex-dist=complexdist:main",
            "complex-dist2=complexdist:main",
        ],
    },
)
