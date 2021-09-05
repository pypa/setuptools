"""
Ensure Setuptools dependencies are present.
"""
import sys
import pathlib

sys.path.extend(map(str, pathlib.Path(__file__).parent.glob('*.whl')))
