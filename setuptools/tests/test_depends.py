import sys

from setuptools import get_module_constant


class TestGetModuleConstant:

    def test_basic(self):
        """
        Invoke get_module_constant on a module in
        the test package.
        """
        mod_name = 'setuptools.tests.mod_with_constant'
        val = get_module_constant.get_module_constant(mod_name, 'value')
        assert val == 'three, sir!'
        assert 'setuptools.tests.mod_with_constant' not in sys.modules
