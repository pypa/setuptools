from setuptools import setup, Extension, SharedLibrary

setup(
    name="shlib_test",
    ext_modules = [
        SharedLibrary("hellolib", ["hellolib.c"]),
        Extension("hello", ["hello.pyx"], libraries=["hellolib"])
    ],
    test_suite="test_hello.HelloWorldTest",
)
