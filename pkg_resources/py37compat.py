try:
	from functools import cached_property
except ImportError:
	# todo: consider backports.cached-property
	cached_property = property
