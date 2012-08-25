import os
import unittest
import pkg_resources
from setuptools.tests.py26compat import skipIf
from unittest import expectedFailure

try:
    import _ast
except ImportError:
    pass

class TestMarkerlib(unittest.TestCase):

    def test_markers(self):
        from _markerlib import interpret, default_environment, compile
        
        os_name = os.name
        
        self.assert_(interpret(""))
        
        self.assert_(interpret("os.name != 'buuuu'"))
        self.assert_(interpret("python_version > '1.0'"))
        self.assert_(interpret("python_version < '5.0'"))
        self.assert_(interpret("python_version <= '5.0'"))
        self.assert_(interpret("python_version >= '1.0'"))
        self.assert_(interpret("'%s' in os.name" % os_name))
        self.assert_(interpret("'buuuu' not in os.name"))
        
        self.assertFalse(interpret("os.name == 'buuuu'"))
        self.assertFalse(interpret("python_version < '1.0'"))
        self.assertFalse(interpret("python_version > '5.0'"))
        self.assertFalse(interpret("python_version >= '5.0'"))
        self.assertFalse(interpret("python_version <= '1.0'"))
        self.assertFalse(interpret("'%s' not in os.name" % os_name))
        self.assertFalse(interpret("'buuuu' in os.name and python_version >= '5.0'"))    
        
        environment = default_environment()
        environment['extra'] = 'test'
        self.assert_(interpret("extra == 'test'", environment))
        self.assertFalse(interpret("extra == 'doc'", environment))
        
        @expectedFailure(NameError)
        def raises_nameError():
            interpret("python.version == '42'")
        
        raises_nameError()
        
        @expectedFailure(SyntaxError)
        def raises_syntaxError():
            interpret("(x for x in (4,))")
            
        raises_syntaxError()
        
        statement = "python_version == '5'"
        self.assertEqual(compile(statement).__doc__, statement)
        
    @skipIf('_ast' not in globals(),
        "ast not available (Python < 2.5?)")
    def test_ast(self):
        try:
            import ast, nose
            raise nose.SkipTest()
        except ImportError:
            pass
        
        # Nonsensical code coverage tests.
        import _markerlib._markers_ast as _markers_ast
        
        class Node(_ast.AST):
            _fields = ('bogus')
        list(_markers_ast.iter_fields(Node()))
        
        class Node2(_ast.AST):
            def __init__(self):
                self._fields = ('bogus',)
                self.bogus = [Node()]
                
        class NoneTransformer(_markers_ast.NodeTransformer):
            def visit_Attribute(self, node):
                return None
            
            def visit_Str(self, node):
                return None
            
            def visit_Node(self, node):
                return []
                
        NoneTransformer().visit(_markers_ast.parse('a.b = "c"'))
        NoneTransformer().visit(Node2())
        
