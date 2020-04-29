"""
Launch the Python script on the command line after
setuptools is bootstrapped via import.
"""

# Note that setuptools gets imported implicitly by the
# invocation of this script using python -m setuptools.launch

import io
import os
import sys
import tokenize

def _open_setup_script(setup_script, fallback):
    if fallback and not os.path.exists(setup_script):
        # Supply a default setup.py
        return io.StringIO(u"from setuptools import setup; setup()")

    return getattr(tokenize, 'open', open)(setup_script)

def run_setup(setup_script='setup.py', fallback=True):
    namespace = {
        '__file__' : setup_script,
        '__name__' : '__main__',
        '__doc__' : None
    }

    with _open_setup_script(setup_script, fallback) as f:
        code = f.read().replace(r'\r\n', r'\n')

    exec(compile(code, setup_script, 'exec'), namespace)

def run_script():
    """
    Run the script in sys.argv[1] as if it had
    been invoked naturally.
    """
    script_name = sys.argv[1]
    sys.argv[:] = sys.argv[1:]

    run_setup(script_name, fallback=False)


if __name__ == '__main__':
    run_script()
