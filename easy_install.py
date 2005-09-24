#!python
"""\
This script/module exists for backward compatibility only!  It will go away
entirely in 0.7.  Please start using the 'easy_install' script or .exe instead
of using 'python -m easy_install' or running 'easy_install.py' directly.
"""

if __name__ == '__main__':
    import sys
    print >>sys.stderr, \
        "Please use the 'easy_install' script or executable instead."
    print >>sys.stderr, \
        "(i.e., don't include the '.py' extension and don't use 'python -m')"
    sys.exit(2)

