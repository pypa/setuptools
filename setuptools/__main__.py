"""
Command-line interface for running setup.py or new-fashioned setup.cfg after
setuptools is monkey-patched into distutils.
"""

if __name__ == '__main__':
    import sys
    from setuptools.launch import run_setup
    sys.argv[0] = 'setuptools'
    run_setup()
