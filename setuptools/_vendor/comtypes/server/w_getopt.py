class GetoptError(Exception):
    pass

def w_getopt(args, options):
    """A getopt for Windows.

    Options may start with either '-' or '/', the option names may
    have more than one letter (/tlb or -RegServer), and option names
    are case insensitive.

    Returns two elements, just as getopt.getopt.  The first is a list
    of (option, value) pairs in the same way getopt.getopt does, but
    there is no '-' or '/' prefix to the option name, and the option
    name is always lower case.  The second is the list of arguments
    which do not belong to an option.

    Different from getopt.getopt, a single argument not belonging to an option
    does not terminate parsing.
    """
    opts = []
    arguments = []
    while args:
        if args[0][:1] in "/-":
            arg = args[0][1:] # strip the '-' or '/'
            arg = arg.lower()

            if arg + ':' in options:
                try:
                    opts.append((arg, args[1]))
                except IndexError:
                    raise GetoptError("option '%s' requires an argument" % args[0])
                args = args[1:]
            elif arg in options:
                opts.append((arg, ''))
            else:
                raise GetoptError("invalid option '%s'" % args[0])
            args = args[1:]
        else:
            arguments.append(args[0])
            args = args[1:]

    return opts, arguments

if __debug__:
    if __name__ == "__main__":
        import unittest

        class TestCase(unittest.TestCase):
            def test_1(self):
                args = "-embedding spam /RegServer foo /UnregSERVER blabla".split()
                opts, args = w_getopt(args,
                                      "regserver unregserver embedding".split())
                self.assertEqual(opts,
                                 [('embedding', ''),
                                  ('regserver', ''),
                                  ('unregserver', '')])
                self.assertEqual(args, ["spam", "foo", "blabla"])

            def test_2(self):
                args = "/TLB Hello.Tlb HELLO.idl".split()
                opts, args = w_getopt(args, ["tlb:"])
                self.assertEqual(opts, [('tlb', 'Hello.Tlb')])
                self.assertEqual(args, ['HELLO.idl'])

            def test_3(self):
                # Invalid option
                self.assertRaises(GetoptError, w_getopt,
                                  "/TLIB hello.tlb hello.idl".split(), ["tlb:"])

            def test_4(self):
                # Missing argument
                self.assertRaises(GetoptError, w_getopt,
                                  "/TLB".split(), ["tlb:"])

        unittest.main()
