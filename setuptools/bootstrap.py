"""
When setuptools is installed in a clean environment, it doesn't have its
dependencies, so it can't run to install its dependencies. This module
checks those dependencies and if one or more are missing, it uses vendored
versions.
"""

import os
import sys
import glob

def ensure_deps():
	"""
	Detect if dependencies are installed and if not, use vendored versions.
	"""
	try:
		__import__('six')
	except ImportError:
		use_vendor_deps()

def use_vendor_deps():
	"""
	Use vendored versions
	"""
	here = os.path.dirname(__file__)
	eggs = glob.glob(here + '/_vendor/*.egg')
	sys.path.extend(eggs)
