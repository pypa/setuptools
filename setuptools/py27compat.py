"""
Compatibility Support for Python 2.7 and earlier
"""

import platform

import six


def get_all_headers(message, key):
    """
    Given an HTTPMessage, return all headers matching a given key.
    """
    return message.get_all(key)


if six.PY2:
    def get_all_headers(message, key):
        return message.getheaders(key)


linux_py2_ascii = (
    platform.system() == 'Linux' and
    six.PY2
)

rmtree_safe = str if linux_py2_ascii else lambda x: x
"""Workaround for http://bugs.python.org/issue24672"""


def dict_values_strings(dict_):
    """
    Given a dict, make sure the text values are str.
    """
    if six.PY3:
        return dict_

    # When dropping Python 2.6 support, use a dict constructor
    return dict(
        (key, str(value))
        for key, value in dict_.iteritems()
    )
