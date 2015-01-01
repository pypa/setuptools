import os
import unittest

import pytest


class TestMarkerlib(unittest.TestCase):

    @pytest.mark.importorskip('ast')
    def test_markers(self):
        from _markerlib import interpret, default_environment, compile

        os_name = os.name

        self.assertTrue(interpret(""))

        self.assertTrue(interpret("os.name != 'buuuu'"))
        self.assertTrue(interpret("os_name != 'buuuu'"))
        self.assertTrue(interpret("python_version > '1.0'"))
        self.assertTrue(interpret("python_version < '5.0'"))
        self.assertTrue(interpret("python_version <= '5.0'"))
        self.assertTrue(interpret("python_version >= '1.0'"))
        self.assertTrue(interpret("'%s' in os.name" % os_name))
        self.assertTrue(interpret("'%s' in os_name" % os_name))
        self.assertTrue(interpret("'buuuu' not in os.name"))

        self.assertFalse(interpret("os.name == 'buuuu'"))
        self.assertFalse(interpret("os_name == 'buuuu'"))
        self.assertFalse(interpret("python_version < '1.0'"))
        self.assertFalse(interpret("python_version > '5.0'"))
        self.assertFalse(interpret("python_version >= '5.0'"))
        self.assertFalse(interpret("python_version <= '1.0'"))
        self.assertFalse(interpret("'%s' not in os.name" % os_name))
        self.assertFalse(interpret("'buuuu' in os.name and python_version >= '5.0'"))
        self.assertFalse(interpret("'buuuu' in os_name and python_version >= '5.0'"))

        environment = default_environment()
        environment['extra'] = 'test'
        self.assertTrue(interpret("extra == 'test'", environment))
        self.assertFalse(interpret("extra == 'doc'", environment))

        def raises_nameError():
            try:
                interpret("python.version == '42'")
            except NameError:
                pass
            else:
                raise Exception("Expected NameError")

        raises_nameError()

        def raises_syntaxError():
            try:
                interpret("(x for x in (4,))")
            except SyntaxError:
                pass
            else:
                raise Exception("Expected SyntaxError")

        raises_syntaxError()

        statement = "python_version == '5'"
        self.assertEqual(compile(statement).__doc__, statement)

