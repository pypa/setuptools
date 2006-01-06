from setuptools import setup, Extension, Library

setup(
    name="shlib_test",
    ext_modules = [
        Library("hellolib", ["hellolib.c"]),
        Extension("hello", ["hello.pyx"], libraries=["hellolib"])
    ],
    test_suite="test_hello.HelloWorldTest",
)
