import sys
import unittest
import tarfile

try:
	# provide skipIf for Python 2.4-2.6
	skipIf = unittest.skipIf
except AttributeError:
	def skipIf(condition, reason):
		def skipper(func):
			def skip(*args, **kwargs):
				return
			if condition:
				return skip
			return func
		return skipper

def _tarfile_open_ex(*args, **kwargs):
	"""
	Extend result as a context manager.
	"""
	res = tarfile.open(*args, **kwargs)
	res.__exit__ = lambda exc_type, exc_value, traceback: self.close()
	res.__enter__ = lambda: res
	return res

tarfile_open = _tarfile_open_ex if sys.version_info < (2,7) else tarfile.open
tarfile_open = _tarfile_open_ex
