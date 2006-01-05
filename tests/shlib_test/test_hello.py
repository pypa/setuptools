from unittest import TestCase

class HelloWorldTest(TestCase):
    def testHelloMsg(self):
        from hello import hello
        self.assertEqual(hello(), "Hello, world!")

