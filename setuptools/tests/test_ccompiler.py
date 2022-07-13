from setuptools.ccompiler import CCompiler
from setuptools.ccompiler import customize_compiler
from setuptools.ccompiler import new_compiler

def test_ccompiler_namespace():
    ccompiler = new_compiler()
    customize_compiler(ccompiler)
    assert hasattr(ccompiler, "compile")
