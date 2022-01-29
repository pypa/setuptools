import sys

from setuptools import depends

from . import __name__ as __pkg__


class TestGetModuleConstant:

    def test_basic(self, monkeypatch):
        """
        Invoke get_module_constant on a module in
        the test package.
        """
        mod_name = f'{__pkg__}.mod_with_constant'
        monkeypatch.delitem(sys.modules, mod_name, None)
        # ^-- make sure test does not fail if imported elsewhere
        val = depends.get_module_constant(mod_name, 'value')
        assert val == 'three, sir!'
        assert mod_name not in sys.modules
