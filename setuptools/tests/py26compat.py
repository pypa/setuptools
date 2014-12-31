import sys
import unittest
import tarfile
import contextlib

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
	return contextlib.closing(tarfile.open(*args, **kwargs))

tarfile_open = _tarfile_open_ex if sys.version_info < (2,7) else tarfile.open
