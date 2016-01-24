"""
Launch the Python script on the command line after
setuptools is bootstrapped via import.
"""

# Note that setuptools gets imported implicitly by the
# invocation of this script using python -m setuptools.launch

import tokenize
import sys


def load():
	"""
	Load the script in sys.argv[1] and run it as if it had
	been invoked naturally.
	"""
	globals()['__file__'] = sys.argv[1]
	sys.argv[:] = sys.argv[1:]

	open_ = getattr(tokenize, 'open', open)
	script = open_(__file__).read()
	norm_script = script.replace('\\r\\n', '\\n')
	return compile(norm_script, __file__, 'exec')


if __name__ == '__main__':
	exec(load())
