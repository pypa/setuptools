import sys

from setuptools import depends


class TestGetModuleConstant:

	def test_basic(self):
		"""
		Invoke get_module_constant on a module in
		the test package.
		"""
		mod_name = 'setuptools.tests.mod_with_constant'
		val = depends.get_module_constant(mod_name, 'value')
		assert val == 'three, sir!'
		assert 'setuptools.tests.mod_with_constant' not in sys.modules


class TestIterCode:
	def test_empty(self):
		code = compile('', '<string>', mode='exec')
		expected = (100, 0), (83, None)
		assert tuple(depends._iter_code(code)) == expected

	def test_constant(self):
		code = compile('value = "three, sir!"', '<string>', mode='exec')
		expected = (100, 0), (90, 0), (100, 1), (83, None)
		assert tuple(depends._iter_code(code)) == expected
