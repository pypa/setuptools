try:
	import unittest.mock as mock
except ImportError:
	import mock

from pkg_resources import evaluate_marker


@mock.patch.dict('pkg_resources.MarkerEvaluation.values',
	python_full_version=mock.Mock(return_value='2.7.10'))
def test_ordering():
	assert evaluate_marker("python_full_version > '2.7.3'") is True
