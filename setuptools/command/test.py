from setuptools import Command
from distutils.errors import DistutilsOptionError
import sys

class test(Command):

    """Command to run unit tests after in-place build"""

    description = "run unit tests after in-place build"

    user_options = [
        ('test-module=','m', "Run 'test_suite' in specified module"),
        ('test-suite=','s',
            "Test suite to run (e.g. 'some_module.test_suite')"),
    ]

    test_suite = None
    test_module = None

    def initialize_options(self):
        pass


    def finalize_options(self):

        if self.test_suite is None:
            if self.test_module is None:
                self.test_suite = self.distribution.test_suite
            else:
                self.test_suite = self.test_module+".test_suite"
        elif self.test_module:
            raise DistutilsOptionError(
                "You may specify a module or a suite, but not both"
            )

        self.test_args = [self.test_suite]

        if self.verbose:
            self.test_args.insert(0,'--verbose')


    def run(self):
        # Ensure metadata is up-to-date
        self.run_command('egg_info')

        # Build extensions in-place
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')

        if self.test_suite:
            cmd = ' '.join(self.test_args)
            if self.dry_run:
                self.announce('skipping "unittest %s" (dry run)' % cmd)
            else:
                self.announce('running "unittest %s"' % cmd)
                self.run_tests()

    def run_tests(self):
        import unittest, pkg_resources
        old_path = sys.path[:]
        ei_cmd = self.get_finalized_command("egg_info")
        try:
            # put the egg on sys.path, and require() it
            sys.path.insert(0, ei_cmd.egg_base)
            pkg_resources.require(
                "%s==%s" % (ei_cmd.egg_name, ei_cmd.egg_version)
            )
            unittest.main(None, None, [unittest.__file__]+self.test_args)
        finally:
            sys.path[:] = old_path
            # XXX later this might need to save/restore the WorkingSet











